"""Create label-free human review files; never invent human or judge scores."""

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StrictInt, model_validator

from eval.calibration import calibration
from src.contracts import Contract, KaynakAtfi
from src.privacy import mask_pii
from src.rag import MevzuatRetriever

Grade = Annotated[StrictInt, Field(ge=0, le=1)]


class ReviewItem(Contract):
    id: str = Field(pattern=r"^REV-\d{3,}$")
    rubric_version: Literal["retrieval-v1"] = "retrieval-v1"
    corpus_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    query: str = Field(min_length=3, max_length=4000)
    retrieval_status: Literal["ok", "error", "not_run"]
    evidence: tuple[KaynakAtfi, ...] = ()
    human_score: Grade | None = None
    judge_score: Grade | None = None
    reviewer: str | None = None
    judge_model: str | None = None
    notes: str = ""

    @model_validator(mode="after")
    def grades_require_evidence(self):
        if self.human_score is not None and not (self.reviewer and self.reviewer.strip()):
            raise ValueError("İnsan puanı için etiketleyen gereklidir")
        if self.judge_score is not None and not (self.judge_model and self.judge_model.strip()):
            raise ValueError("Hakem puanı için kullanılan gerçek model/sürüm gereklidir")
        if self.retrieval_status != "ok" and (
            self.human_score is not None or self.judge_score is not None
        ):
            raise ValueError("Çalışmamış/hatalı arama kaynak doğruluğu olarak puanlanamaz")
        return self


def evidence_fingerprint(item: ReviewItem) -> str:
    immutable = item.model_dump(
        mode="json", exclude={"human_score", "judge_score", "reviewer", "judge_model", "notes"}
    )
    return hashlib.sha256(
        json.dumps(immutable, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


class ManifestEntry(Contract):
    backend: str = Field(min_length=1)
    query_id: str = Field(pattern=r"^RQ\d{2,3}$")
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReviewManifest(Contract):
    schema_version: Literal[1]
    corpus_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_queries: tuple[str, ...] = Field(min_length=1)
    items: dict[str, ManifestEntry] = Field(min_length=1)


def select_rows(rows: list[dict], limit: int) -> list[str]:
    """Round-robin by category, never selected by gold score or observed success."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["category"]].append(row["id"])
    selected = []
    while len(selected) < limit and any(groups.values()):
        for group in groups.values():
            if group and len(selected) < limit:
                selected.append(group.pop(0))
    return selected


def export_pack(report: dict, output: Path, *, limit: int = 10, seed: int = 0) -> dict:
    if type(limit) is not int or limit < 1:
        raise ValueError("İnceleme sorgu sayısı pozitif olmalıdır")
    if output.suffix.lower() != ".jsonl":
        raise ValueError("İnceleme çıktısı .jsonl uzantılı olmalıdır")
    if report.get("schema_version") != 1 or not report.get("backends"):
        raise ValueError("Geçerli RAG karşılaştırma raporu gereklidir")
    rag = MevzuatRetriever()
    backends = report["backends"]
    first = next(iter(backends.values()))
    selected = select_rows(first["rows"], limit)
    first_queries = {row["id"]: mask_pii(row["query"]) for row in first["rows"]}
    if not selected:
        raise ValueError("İncelenecek sorgu bulunamadı")
    pending = []
    for backend, result in backends.items():
        if result["corpus_sha256"] != rag.fingerprint:
            raise ValueError("İnceleme paketi farklı derlem sürümünden üretilemez")
        by_id = {row["id"]: row for row in result["rows"]}
        if len(by_id) != len(result["rows"]) or any(case_id not in by_id for case_id in selected):
            raise ValueError("Yöntemlerin sorgu kimlikleri eşleşmiyor")
        for case_id in selected:
            row = by_id[case_id]
            if mask_pii(row["query"]) != first_queries[case_id]:
                raise ValueError("Yöntemler aynı sorgu kimliği için farklı sorular içeriyor")
            pending.append((backend, case_id, row))
    random.Random(seed).shuffle(pending)
    items = []
    mapping = {}
    for index, (backend, case_id, row) in enumerate(pending, 1):
        if len(row["ranked_ids"]) > 10:
            raise ValueError("İnceleme için en fazla 10 kaynak desteklenir")
        item = ReviewItem(
            id=f"REV-{index:03d}",
            corpus_sha256=rag.fingerprint,
            query=mask_pii(row["query"]),
            retrieval_status=row["status"],
            evidence=tuple(rag.citation_for(source_id) for source_id in row["ranked_ids"]),
        )
        items.append(item)
        mapping[item.id] = {
            "backend": backend,
            "query_id": case_id,
            "evidence_sha256": evidence_fingerprint(item),
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(item.model_dump_json() for item in items) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "corpus_sha256": rag.fingerprint,
        "selected_queries": selected,
        "items": mapping,
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = [
        "# RAG insan inceleme paketi",
        "",
        "Puanlar boş bırakılmıştır. Bu dosya gerçek değerlendirme sonucu değildir.",
        "",
        "Her sorguyu yalnız aşağıdaki kaynaklarla değerlendir. 1: yararlı ve gerekli koşulları koruyan kanıt; "
        "0: ilgisiz, yetersiz veya soruyu karşılamayan kanıt. Boş sonuç ancak derlemde cevap yoksa "
        "veya isteğin açıklığa kavuşturulması gerekiyorsa uygun sayılır. Boş sonuç, hukuki hakkın olmadığı anlamına gelmez.",
        "",
        "Çalışmamış/hatalı aramaları puanlama. `human_score` ve gerçek hakem değerlendirmesi varsa "
        "`judge_score` alanlarını JSONL'de doldur; etiketleyen ve hakem modeli/sürümünü kaydet. "
        "Soru/kaynak/kimlik alanlarını değiştirme. Manifest yöntem eşlemesini içerir; puanlamadan önce açma.",
        "",
    ]
    for item in items:
        markdown += [
            f"## {item.id}",
            "",
            f"> {item.query}",
            "",
            f"Arama durumu: `{item.retrieval_status}`",
            "",
        ]
        if not item.evidence:
            markdown += ["Kaynak dönmedi.", ""]
        for rank, cite in enumerate(item.evidence, 1):
            markdown += [
                f"### Kaynak {rank}: {cite.belge_basligi} — {cite.madde}",
                "",
                f"Tür: `{cite.kaynak_turu}` · [Resmî kaynak]({cite.kaynak_url}) · PDF sayfa: {list(cite.kaynak_sayfalari)}",
                "",
            ]
            if cite.baglam:
                markdown += [f"> Koşul: {cite.baglam}", ""]
            markdown += ["> " + cite.dogrudan_alinti.replace("\n", "\n> "), ""]
        markdown += ["İnsan puanı: ____ · Not: __________________________________", ""]
    output.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return {
        "outputs": len(items),
        "unique_queries": len(selected),
        "human_scores_filled": 0,
        "judge_scores_filled": 0,
        "calibration": "yapilmadi",
    }


def score_pack(path: Path, manifest_path: Path) -> dict:
    items = [
        ReviewItem.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    manifest = ReviewManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    ).model_dump(mode="json")
    mappings = manifest["items"]
    if set(manifest["selected_queries"]) != {mapping["query_id"] for mapping in mappings.values()}:
        raise ValueError("Manifest sorgu listesi eşleşmiyor")
    if len({item.id for item in items}) != len(items) or {item.id for item in items} != set(
        mappings
    ):
        raise ValueError("İnceleme kimlikleri tekrarlanmış, eklenmiş veya eksik")
    for item in items:
        if (
            item.corpus_sha256 != manifest["corpus_sha256"]
            or evidence_fingerprint(item) != mappings[item.id]["evidence_sha256"]
        ):
            raise ValueError("Soru veya kanıt, puanlamaya verilen sürümden farklı")
    complete = [
        item for item in items if item.human_score is not None and item.judge_score is not None
    ]
    unique_queries = {mappings[item.id]["query_id"] for item in complete}
    distinct_texts = {" ".join(item.query.casefold().split()) for item in complete}
    if len(unique_queries) < 10 or len(distinct_texts) < 10:
        raise ValueError(
            "Kalibrasyon için en az 10 ayrı sorguda gerçek insan ve hakem puanı gerekir"
        )
    models = {item.judge_model.strip() for item in complete}
    if len(models) != 1:
        raise ValueError("Farklı hakem model/sürümlerini tek kalibrasyonda birleştirmeyin")

    def record(item):
        return {
            "id": item.id,
            "reviewer": item.reviewer,
            "human_score": item.human_score,
            "judge_score": item.judge_score,
        }

    per_backend = {}
    for backend in sorted({mappings[item.id]["backend"] for item in items}):
        subset = [record(item) for item in complete if mappings[item.id]["backend"] == backend]
        per_backend[backend] = (
            calibration(subset)
            if len(subset) >= 10
            else {"n": len(subset), "status": "yetersiz_ornek"}
        )
    return {
        "scope": "İnsan/hakem RAG kanıt değerlendirmesi; nihai ajan karar doğruluğu değildir.",
        "corpus_sha256": manifest["corpus_sha256"],
        "reviewed_outputs": len(complete),
        "reviewed_queries": len(unique_queries),
        "pending_outputs": len(items) - len(complete),
        "reviewer_count": len({item.reviewer.strip() for item in complete}),
        "judge_model": next(iter(models)),
        "overall": calibration([record(item) for item in complete]),
        "by_backend": per_backend,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--report", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Her yöntem için aynı, kategoriye göre dengeli sorgu sayısı",
    )
    score = commands.add_parser("score")
    score.add_argument("--pack", type=Path, required=True)
    score.add_argument("--manifest", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "export" and args.report.resolve() in {
        args.output.resolve(),
        args.output.with_suffix(".md").resolve(),
        args.output.with_suffix(".manifest.json").resolve(),
    }:
        parser.error("İnceleme paketi raporun üzerine yazılamaz")
    if args.command == "score" and (
        args.output.resolve() in {args.pack.resolve(), args.manifest.resolve()}
        or args.output.suffix.lower() != ".json"
    ):
        parser.error("Kalibrasyon çıktısı ayrı bir .json dosyası olmalıdır")
    if args.command == "score":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            '{"status":"not_calibrated","calibration":"yapilmadi"}\n', encoding="utf-8"
        )
    try:
        if args.command == "export":
            result = export_pack(
                json.loads(args.report.read_text(encoding="utf-8")), args.output, limit=args.limit
            )
        else:
            result = score_pack(args.pack, args.manifest)
            result["status"] = "complete"
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    except (ValueError, KeyError, OSError, TypeError, AttributeError):
        parser.exit(
            1,
            "İnceleme paketi doğrulanamadı; veri sürümünü, kimlikleri ve eksik puanları kontrol edin.\n",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
