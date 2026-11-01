"""Retrieval-only evaluation. Gold source IDs never go to the search backend."""

import hashlib
import json
import math
import statistics
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import Field, model_validator

from src.contracts import Contract
from src.evren import EvrenAdapter, ProviderError, RequestObservation
from src.privacy import mask_pii
from src.rag import MevzuatRetriever, load_corpus
from src.references import parse_references

DEFAULT_RETRIEVAL_DATASET = Path(__file__).with_name("retrieval_cases.json")


class RetrievalCase(Contract):
    id: str = Field(pattern=r"^RQ\d{2,3}$")
    category: Literal["cayma", "istisna", "rehber", "ayip", "sinir"]
    query: str = Field(min_length=3, max_length=4000)
    relevant_ids: tuple[str, ...] = ()
    expected_empty: bool = False
    label_status: Literal["ai_taslak", "insan_dogruladi"] = "ai_taslak"
    reviewer: str | None = None
    synthetic: Literal[True] = True

    @model_validator(mode="after")
    def consistent_labels(self):
        if self.expected_empty == bool(self.relevant_ids):
            raise ValueError("Kaynak beklentisi veya boş sonuç beklentisi seçilmelidir")
        if len(set(self.relevant_ids)) != len(self.relevant_ids):
            raise ValueError("İlgili kaynak kimlikleri tekrarlanamaz")
        if self.label_status == "insan_dogruladi" and not (self.reviewer and self.reviewer.strip()):
            raise ValueError("İnsan etiketi için etiketleyen gereklidir")
        return self


def load_retrieval_cases(path: Path = DEFAULT_RETRIEVAL_DATASET) -> tuple[RetrievalCase, ...]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("RAG veri seti boş olmayan bir kayıt listesi olmalıdır")
    cases = tuple(RetrievalCase.model_validate(row) for row in rows)
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError("Boş veya tekrar kimlikli RAG veri seti")
    queries = {" ".join(mask_pii(case.query).casefold().split()) for case in cases}
    if len(queries) != len(cases):
        raise ValueError("Aynı sorgu farklı kimliklerle tekrarlanamaz")
    known = {chunk.chunk_id for chunk in load_corpus()}
    if any(set(case.relevant_ids) - known for case in cases):
        raise ValueError("Beklenen kaynak derlemde bulunmuyor")
    return cases


def dataset_fingerprint(cases: Sequence[RetrievalCase]) -> str:
    return hashlib.sha256("\n".join(case.model_dump_json() for case in cases).encode()).hexdigest()


def score_ranking(case: RetrievalCase, ranked_ids: Sequence[str], k: int) -> dict:
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError("k 1–10 arasında olmalıdır")
    if isinstance(ranked_ids, (str, bytes)) or any(
        not isinstance(source_id, str) or not source_id for source_id in ranked_ids
    ):
        raise ValueError("Sıralama kaynak kimliklerinden oluşmalıdır")
    ranking = tuple(ranked_ids[:k])
    if case.expected_empty:
        return {"empty_correct": not ranking}
    relevant = set(case.relevant_ids)
    seen = set()
    gains = []
    for source_id in ranking:
        gains.append(int(source_id in relevant and source_id not in seen))
        seen.add(source_id)
    hits = sum(gains)
    first = next((rank for rank, gain in enumerate(gains, 1) if gain), None)
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return {
        "hit_at_k": hits > 0,
        "recall_at_k": hits / len(relevant),
        "precision_at_k": hits / k,
        "mrr_at_k": 1 / first if first else 0.0,
        "ndcg_at_k": dcg / ideal,
    }


def api_summary(observations: Sequence[RequestObservation]) -> dict:
    """Missing usage stays unknown. Never copy provider account metadata."""
    result = {
        "request_count": len(observations),
        "endpoints": dict(Counter(item.endpoint for item in observations)),
        "http_errors": sum(
            item.status_code is None or item.status_code != 200 for item in observations
        ),
    }
    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
        known = [getattr(item, field) for item in observations if getattr(item, field) is not None]
        result[field] = sum(known) if known else None if observations else 0
        result[field + "_reported_requests"] = len(known)
    return result


def percentile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def benchmark(
    cases: Sequence[RetrievalCase],
    factory: Callable[[], MevzuatRetriever],
    *,
    name: str,
    top_k: int = 3,
    provider: EvrenAdapter | None = None,
) -> dict:
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError("RAG veri seti boş olamaz ve kimlikler benzersiz olmalıdır")
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("top_k 1–10 arasında olmalıdır")
    rows = []
    retriever = None
    start = perf_counter()
    initial_cursor = len(provider.observations) if provider else 0
    preparation = {}
    stopped = None
    consecutive_errors = 0
    try:
        try:
            retriever = factory()
            retriever.prepare()
            preparation["status"] = "ok"
        except Exception as exc:
            preparation.update(status="error", error_type=type(exc).__name__)
            stopped = "preparation_failed"
        preparation["elapsed_ms"] = (perf_counter() - start) * 1000
        cursor = len(provider.observations) if provider else 0
        preparation["api"] = api_summary(
            provider.observations[initial_cursor:cursor] if provider else []
        )
        for case in cases:
            query = mask_pii(case.query)
            row = {
                "id": case.id,
                "category": case.category,
                "query": query,
                "label_status": case.label_status,
                "status": "not_run",
                "ranked_ids": [],
                "elapsed_ms": None,
                "metrics": score_ranking(case, [], top_k),
                "reference_query": bool(parse_references(query)),
                "query_filters": {"belge_ids": None, "tarih": None},
            }
            if case.expected_empty:
                row["metrics"]["empty_correct"] = (
                    False  # An unexecuted query is never correct abstention.
                )
            before = len(provider.observations) if provider else 0
            if stopped:
                row["reason"] = stopped
            else:
                begin = perf_counter()
                try:
                    if len(query) > 4000:
                        raise ValueError("Normalleştirilmiş RAG sorgusu çok uzun")
                    results = retriever.search(query, top_k=top_k)
                    if len(results) > top_k:
                        raise ValueError("RAG sınırı aşıldı")
                    ids = [result.parca.chunk_id for result in results]
                    if any(source_id not in retriever.by_id for source_id in ids):
                        raise ValueError("Bilinmeyen RAG sonucu")
                    row.update(
                        status="ok",
                        ranked_ids=ids,
                        metrics=score_ranking(case, ids, top_k),
                        requested_truncated=any(result.istek_kirpildi for result in results),
                    )
                    consecutive_errors = 0
                except Exception as exc:
                    consecutive_errors += 1
                    row.update(status="error", error_type=type(exc).__name__)
                    code = exc.status_code if isinstance(exc, ProviderError) else None
                    if type(code) is int:
                        row["http_status"] = code
                    if code in (401, 403, 429) or consecutive_errors >= 3:
                        stopped = "provider_or_backend_unavailable"
                row["elapsed_ms"] = (perf_counter() - begin) * 1000
            after = len(provider.observations) if provider else 0
            row["api"] = api_summary(provider.observations[before:after] if provider else [])
            rows.append(row)
        positives = [row for row, case in zip(rows, cases, strict=True) if not case.expected_empty]
        negatives = [row for row, case in zip(rows, cases, strict=True) if case.expected_empty]
        completed_latency = [row["elapsed_ms"] for row in rows if row["status"] == "ok"]
        all_latency = [row["elapsed_ms"] for row in rows if row["elapsed_ms"] is not None]
        reference_negatives = [row for row in negatives if row["reference_query"]]
        natural_negatives = [row for row in negatives if not row["reference_query"]]
        summary = {
            metric: statistics.mean(float(row["metrics"][metric]) for row in positives)
            if positives
            else None
            for metric in ("hit_at_k", "recall_at_k", "precision_at_k", "mrr_at_k", "ndcg_at_k")
        }
        summary.update(
            n=len(cases),
            positive_n=len(positives),
            negative_n=len(negatives),
            completed=sum(row["status"] == "ok" for row in rows),
            errors=sum(row["status"] == "error" for row in rows),
            not_run=sum(row["status"] == "not_run" for row in rows),
            empty_accuracy=statistics.mean(
                float(row["metrics"]["empty_correct"]) for row in negatives
            )
            if negatives
            else None,
            p50_completed_ms=percentile(completed_latency, 0.5),
            p95_completed_ms=percentile(completed_latency, 0.95),
            p50_executed_ms=percentile(all_latency, 0.5),
            p95_executed_ms=percentile(all_latency, 0.95),
            reference_negative_n=len(reference_negatives),
            natural_negative_n=len(natural_negatives),
            empty_accuracy_reference=statistics.mean(
                float(row["metrics"]["empty_correct"]) for row in reference_negatives
            )
            if reference_negatives
            else None,
            empty_accuracy_natural=statistics.mean(
                float(row["metrics"]["empty_correct"]) for row in natural_negatives
            )
            if natural_negatives
            else None,
        )
        return {
            "name": name,
            "top_k": top_k,
            "corpus_sha256": retriever.fingerprint if retriever else None,
            "configuration": retriever.configuration if retriever else None,
            "cache_status": retriever.cache_status if retriever else None,
            "preparation": preparation,
            "summary": summary,
            "api": api_summary(provider.observations[initial_cursor:] if provider else []),
            "usd_cost": None,
            "rows": rows,
        }
    finally:
        if retriever is not None:
            retriever.close()


def render_markdown(report: dict) -> str:
    def number(value, percent=False):
        if value is None:
            return "bilinmiyor"
        return f"{value * 100:.1f}%" if percent else f"{value:.2f}"

    lines = [
        "# RAG karşılaştırma raporu",
        "",
        report["scope"],
        "",
        f"Sorgu sayısı: **{report['selected_n']} / {report['dataset_n']}**. "
        f"Etiket durumu: `{report['labels']}`. Koşum: `{report['status']}`.",
        "",
        "Hazırlık süresi sorgu gecikmesine katılmaz. Tokenlar sağlayıcının bildirdiği değerlerdir; "
        "eksik kullanım bilgisi sıfır maliyet sayılmaz. USD maliyeti hesaplanmadı.",
        "",
        "| Yöntem | Hit@k | Recall@k | Precision@k | MRR@k | nDCG@k | Tamamlanan | Sorgu p95 (ms) | API çağrısı | Bildirilen toplam token |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, result in report["backends"].items():
        summary = result["summary"]
        api = result["api"]
        lines.append(
            f"| {name} (k={result['top_k']}) | {number(summary['hit_at_k'], True)} | "
            f"{number(summary['recall_at_k'], True)} | {number(summary['precision_at_k'], True)} | "
            f"{number(summary['mrr_at_k'])} | {number(summary['ndcg_at_k'])} | "
            f"{summary['completed']}/{summary['n']} | {number(summary['p95_completed_ms'])} | "
            f"{api['request_count']} | {api['total_tokens'] if api['total_tokens'] is not None else 'bilinmiyor'} |"
        )
    lines += [
        "",
        "## Boş sonuç ve hazırlık kontrolleri",
        "",
        "Açık madde koruması ile doğal konu dışı sorular ayrıdır; boş sonuç hukuki hakkın olmadığı anlamına gelmez.",
        "",
        "| Yöntem | Madde koruması n / doğruluk | Doğal konu dışı n / doğruluk | Hazırlık (ms) | Derlem önbelleği |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, result in report["backends"].items():
        summary = result["summary"]
        lines.append(
            f"| {name} | {summary['reference_negative_n']} / {number(summary['empty_accuracy_reference'], True)} | "
            f"{summary['natural_negative_n']} / {number(summary['empty_accuracy_natural'], True)} | "
            f"{number(result['preparation']['elapsed_ms'])} | {result['cache_status']} |"
        )
    lines += ["", "## Gözlenen eksikler", ""]
    for name, result in report["backends"].items():
        failures = []
        for row in result["rows"]:
            metrics = row["metrics"]
            if (
                row["status"] != "ok"
                or metrics.get("recall_at_k", 1) < 1
                or metrics.get("empty_correct") is False
            ):
                failures.append(
                    f"- {row['id']}: `{row['status']}`; kaynaklar: `{row['ranked_ids']}`; ölçümler: `{metrics}`"
                )
        lines += [
            f"### {name}",
            "",
            *(failures or ["Bu taslak beklentilerde eksik gözlenmedi."]),
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"
