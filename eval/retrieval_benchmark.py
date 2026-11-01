"""Compare retrieval backends; network calls require --backend evren or compare."""

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from eval.retrieval import (
    DEFAULT_RETRIEVAL_DATASET,
    benchmark,
    dataset_fingerprint,
    load_retrieval_cases,
    render_markdown,
)
from src.evren import EvrenAdapter, ProviderSettings
from src.paths import ROOT
from src.rag import MevzuatRetriever


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_RETRIEVAL_DATASET)
    parser.add_argument("--backend", choices=["lexical", "evren", "compare"], default="lexical")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--limit", type=int, help="Açık alt küme sınırı; tam veri seti sonucu sayılmaz"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts" / "retrieval_benchmark.json"
    )
    args = parser.parse_args()
    if not 1 <= args.top_k <= 10 or args.limit is not None and args.limit < 1:
        parser.error("top-k 1–10, limit pozitif olmalıdır")
    if args.output.suffix.lower() != ".json":
        parser.error("Karşılaştırma çıktısı .json uzantılı olmalıdır")
    if args.dataset.resolve() in {
        args.output.resolve(),
        args.output.with_suffix(".md").resolve(),
    }:
        parser.error("Çıktı veri setinin üzerine yazılamaz")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        '{"schema_version":1,"status":"running","backends":{}}\n', encoding="utf-8"
    )
    args.output.with_suffix(".md").write_text(
        "# RAG ölçümü\n\nKoşum henüz tamamlanmadı.\n", encoding="utf-8"
    )
    try:
        cases = load_retrieval_cases(args.dataset)
    except (ValueError, OSError) as exc:
        args.output.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "backends": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        args.output.with_suffix(".md").write_text(
            "# RAG ölçümü\n\nVeri seti yüklenemedi; bu koşum başarısız.\n", encoding="utf-8"
        )
        parser.exit(
            1,
            "RAG veri seti yüklenemedi; biçimi, kaynak kimliklerini ve dosya yolunu kontrol edin.\n",
        )
    selected = cases[: args.limit] if args.limit else cases
    report = {
        "schema_version": 1,
        "status": "running",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": dataset_fingerprint(cases),
        "selected_sha256": dataset_fingerprint(selected),
        "dataset_n": len(cases),
        "selected_n": len(selected),
        "selected_ids": [case.id for case in selected],
        "labels": dict(Counter(case.label_status for case in selected)),
        "scope": "RAG geliştirme ve karşılaştırma seti; nihai karar doğruluğu veya bağımsız insan testi değildir.",
        "backends": {},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    try:
        for name in ["lexical", "evren"] if args.backend == "compare" else [args.backend]:
            provider = None
            try:
                if name == "evren":
                    provider = EvrenAdapter(ProviderSettings.from_env())
                report["backends"][name] = benchmark(
                    selected,
                    lambda p=provider: MevzuatRetriever(
                        embedder=p, cache_dir=ROOT / ".cache" / "embeddings" if p else None
                    ),
                    name=name,
                    top_k=args.top_k,
                    provider=provider,
                )
                if provider:
                    report["backends"][name]["embedding_model"] = provider.settings.embedding_model
            finally:
                if provider:
                    provider.close()
        report["status"] = (
            "complete"
            if all(
                item["summary"]["completed"] == len(selected)
                for item in report["backends"].values()
            )
            else "incomplete"
        )
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.output.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "selected_n": len(selected),
                "backends": {
                    name: {"summary": item["summary"], "api": item["api"]}
                    for name, item in report["backends"].items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    raise SystemExit(0 if report["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
