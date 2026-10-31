"""Member 1 development CLI. Prints facts and evidence, never a final legal decision."""

import argparse
import json
import sys
from datetime import date

from src.evidence import hazirla_inceleme
from src.evren import EvrenAdapter, ProviderError, ProviderSettings
from src.paths import ROOT
from src.rag import MevzuatRetriever
from src.tools import cayma_suresi_hesapla, parasal_sinir_kontrol, siparis_detay_getir


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="İadePusula — Üye 1 geliştirme araçları")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search", help="Mevzuatta kaynaklı arama")
    search.add_argument("query")
    search.add_argument("--top-k", type=int, default=3)
    search.add_argument("--backend", choices=["lexical", "evren"], default="lexical")
    inspect = sub.add_parser("inspect", help="İnsan incelemesi için kanıt paketi")
    inspect.add_argument("order")
    inspect.add_argument("text")
    inspect.add_argument("--date", required=True, type=date.fromisoformat)
    inspect.add_argument("--backend", choices=["lexical", "evren"], default="lexical")
    order = sub.add_parser("order", help="Tek bir sentetik sipariş")
    order.add_argument("id")
    withdrawal = sub.add_parser("deadline", help="14 takvim günü hesabı")
    withdrawal.add_argument("delivery", type=date.fromisoformat)
    withdrawal.add_argument("application", type=date.fromisoformat)
    threshold = sub.add_parser("threshold", help="Yıllık parasal sınır")
    threshold.add_argument("amount")
    threshold.add_argument("year", type=int)
    sub.add_parser("models", help="Anahtarı yazdırmadan sağlayıcı modellerini doğrula")
    args = parser.parse_args()
    provider = None
    retriever = None
    try:
        if args.command == "models" or getattr(args, "backend", None) == "evren":
            provider = EvrenAdapter(ProviderSettings.from_env())
        if args.command in {"search", "inspect"}:
            retriever = MevzuatRetriever(
                embedder=provider, cache_dir=ROOT / ".cache" / "embeddings" if provider else None
            )
        if args.command == "search":
            result = [
                row.model_dump(mode="json") for row in retriever.search(args.query, args.top_k)
            ]
        elif args.command == "inspect":
            result = hazirla_inceleme(
                args.order, args.text, args.date, retriever=retriever
            ).model_dump(mode="json")
        elif args.command == "order":
            value = siparis_detay_getir(args.id)
            result = value.model_dump(mode="json") if value else {"durum": "SIPARIS_BULUNAMADI"}
        elif args.command == "deadline":
            result = cayma_suresi_hesapla(args.delivery, args.application).model_dump(mode="json")
        elif args.command == "threshold":
            result = parasal_sinir_kontrol(args.amount, args.year).model_dump(mode="json")
        else:
            result = {"models": provider.models()}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ProviderError, ValueError, OSError) as exc:
        parser.exit(1, f"İşlem tamamlanamadı: {exc}\n")
    finally:
        if retriever:
            retriever.close()
        if provider:
            provider.close()


if __name__ == "__main__":
    main()
