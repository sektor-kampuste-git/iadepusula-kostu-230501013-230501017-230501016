"""Offline component checks and explicit opt-in agent evaluation.

python -m eval.eval_kosucu --output artifacts/eval.json
python -m eval.eval_kosucu --predictor src.agent:predict_for_eval
The predictor receives an EvalCase and returns an AgentPrediction-compatible dict.
"""

import argparse
import importlib
import json
import statistics
import sys
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from eval.contracts import AgentPrediction, EvalCase
from src.evidence import hazirla_inceleme
from src.paths import ROOT
from src.rag import MevzuatRetriever
from src.tools import SiparisDeposu


def load_cases(path: Path = ROOT / "eval" / "evaller.json") -> tuple[EvalCase, ...]:
    cases = tuple(
        EvalCase.model_validate(row) for row in json.loads(path.read_text(encoding="utf-8"))
    )
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Eval kimlikleri benzersiz olmalıdır")
    if not cases:
        raise ValueError("Eval seti boş olamaz")
    return cases


def evaluate(
    cases: tuple[EvalCase, ...],
    *,
    predictor: Callable | None = None,
    retriever: MevzuatRetriever | None = None,
) -> dict:
    retriever = retriever or MevzuatRetriever()
    depo = SiparisDeposu()
    rows = []
    for case in cases:
        start = perf_counter()
        try:
            packet = hazirla_inceleme(
                case.siparis_no, case.basvuru, case.basvuru_tarihi, retriever=retriever, depo=depo
            )
            wanted = case.beklenen
            checks = {
                "insan_onayi": packet.insan_onayi_gerekiyor_mu is True,
                "adim_siniri": len(packet.arac_izleri) <= 4,
            }
            if wanted.cayma_durumu:
                checks["cayma"] = (
                    packet.cayma is not None and packet.cayma.durum == wanted.cayma_durumu
                )
            if wanted.parasal_durumu:
                checks["parasal_sinir"] = (
                    packet.parasal_sinir is not None
                    and packet.parasal_sinir.durum == wanted.parasal_durumu
                )
            found = {item.parca.chunk_id for item in packet.kaynaklar}
            if wanted.kaynak_any_of:
                checks["kaynak_hit_at_3"] = bool(found.intersection(wanted.kaynak_any_of))
            if wanted.kaynak_bos:
                checks["kaynak_bos"] = not found
            for warning in wanted.uyarilar:
                checks["uyari_" + warning] = warning in packet.uyarilar
            if predictor:
                prediction = AgentPrediction.model_validate(predictor(case))
                checks["ajan_sema"] = True
                checks["ajan_atif"] = all(
                    retriever.verify_citation(cite, allowed_ids=found)
                    for cite in prediction.kaynaklar
                )
                if prediction.karar_onerisi != "UZMAN_INCELEMESI_GEREKLI":
                    checks["karar_kaynagi"] = bool(prediction.kaynaklar)
                # AI draft labels are not an independent human-calibrated gold standard.
                checks["ajan_taslak_etiket_uyumu"] = prediction.karar_onerisi == case.taslak_karar
            rows.append(
                {
                    "id": case.id,
                    "grup": case.grup,
                    "gecti": all(checks.values()),
                    "kontroller": checks,
                    "kaynak_ids": sorted(found),
                    "sure_ms": round((perf_counter() - start) * 1000, 3),
                }
            )
        except Exception as exc:
            # Error class only; provider exceptions can contain sensitive input data.
            rows.append(
                {
                    "id": case.id,
                    "grup": case.grup,
                    "gecti": False,
                    "hata_turu": type(exc).__name__,
                    "kontroller": {},
                }
            )
    groups = {}
    for group in sorted({case.grup for case in cases}):
        subset = [row for row in rows if row["grup"] == group]
        groups[group] = {"n": len(subset), "gecen": sum(row["gecti"] for row in subset)}
    measured = [
        row["kontroller"]["kaynak_hit_at_3"]
        for row in rows
        if "kaynak_hit_at_3" in row["kontroller"]
    ]
    return {
        "mod": "ajan_entegrasyonu" if predictor else "arac_ve_rag_bilesenleri",
        "tarih_utc": datetime.now(UTC).isoformat(),
        "derlem_sha256": retriever.fingerprint,
        "n": len(rows),
        "gecen": sum(row["gecti"] for row in rows),
        "gecme_orani": sum(row["gecti"] for row in rows) / len(rows),
        "kaynak_hit_at_3": sum(measured) / len(measured) if measured else None,
        "ortalama_sure_ms": statistics.mean(row.get("sure_ms", 0) for row in rows),
        "gruplar": groups,
        "etiket_durumu": dict(Counter(c.etiket_durumu for c in cases)),
        "insan_hakem_kalibrasyonu": "yapilmadi",
        "ajan_karar_dogrulugu": "insan_etiketleri_olmadan_olculmedi",
        "vakalar": rows,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "eval" / "evaller.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "eval.json")
    parser.add_argument("--predictor", help="Açıkça seçilen module:function; ağ çağırabilir")
    parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=1.0,
        help="Çıkış kodu için açık başarı eşiği; varsayılan tüm vakalar",
    )
    args = parser.parse_args()
    if not 0 <= args.min_pass_rate <= 1:
        parser.error("--min-pass-rate 0 ile 1 arasında olmalıdır")
    predictor = None
    if args.predictor:
        module, function = args.predictor.split(":", 1)
        predictor = getattr(importlib.import_module(module), function)
    result = evaluate(load_cases(args.dataset), predictor=predictor)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "vakalar"}, ensure_ascii=False, indent=2
        )
    )
    raise SystemExit(0 if result["gecme_orani"] >= args.min_pass_rate else 1)


if __name__ == "__main__":
    main()
