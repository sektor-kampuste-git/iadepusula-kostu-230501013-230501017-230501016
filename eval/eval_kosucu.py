"""Offline component checks and explicit opt-in agent evaluation.

python -m eval.eval_kosucu --output artifacts/eval.json
python -m eval.eval_kosucu --predictor src.agent:predict_for_eval
The predictor receives label-free PredictorInput and returns AgentPrediction.
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

from eval.contracts import AgentPrediction, EvalCase, PredictorInput
from src.evidence import hazirla_inceleme
from src.paths import ROOT
from src.rag import MevzuatRetriever
from src.tools import SiparisDeposu

DEFAULT_DATASET = Path(__file__).with_name("evaller.json")


def load_cases(path: Path = DEFAULT_DATASET) -> tuple[EvalCase, ...]:
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
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError("Eval seti boş olamaz ve vaka kimlikleri benzersiz olmalıdır")
    depo = SiparisDeposu()
    rows = []
    for case in cases:
        start = perf_counter()
        wanted = case.beklenen
        checks = {}
        found = set()
        component_ok = False
        agent_ok = None
        error = {}
        stage = "bilesen"
        try:
            packet = hazirla_inceleme(
                case.siparis_no, case.basvuru, case.basvuru_tarihi, retriever=retriever, depo=depo
            )
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
            component_ok = all(checks.values())
            if predictor:
                stage = "ajan"
                prediction = AgentPrediction.model_validate(
                    predictor(
                        PredictorInput(
                            id=case.id,
                            siparis_no=case.siparis_no,
                            basvuru=packet.maskelenmis_basvuru,
                            basvuru_tarihi=case.basvuru_tarihi,
                            kanit_paketi=packet,
                        )
                    )
                )
                checks["ajan_sema"] = True
                checks["ajan_atif"] = all(
                    retriever.verify_citation(cite, allowed_ids=found)
                    for cite in prediction.kaynaklar
                )
                if prediction.karar_onerisi != "UZMAN_INCELEMESI_GEREKLI":
                    checks["karar_kaynagi"] = bool(prediction.kaynaklar)
                # AI draft labels are not an independent human-calibrated gold standard.
                label_key = (
                    "ajan_insan_etiket_uyumu"
                    if case.etiket_durumu == "insan_dogruladi"
                    else "ajan_taslak_etiket_uyumu"
                )
                checks[label_key] = prediction.karar_onerisi == case.taslak_karar
                agent_ok = all(
                    value
                    for key, value in checks.items()
                    if key.startswith("ajan_") or key == "karar_kaynagi"
                )
        except Exception as exc:
            # Error class only; provider exceptions can contain sensitive input data.
            error = {"hata_turu": type(exc).__name__, "hata_asamasi": stage}
            checks["ajan_sema" if stage == "ajan" else "bilesen_calisti"] = False
            if stage == "ajan":
                agent_ok = False
            elif wanted.kaynak_any_of:
                checks["kaynak_hit_at_3"] = False
        rows.append(
            {
                "id": case.id,
                "grup": case.grup,
                "gecti": not error and all(checks.values()),
                "bilesen_gecti": component_ok,
                "ajan_gecti": agent_ok,
                "kontroller": checks,
                "kaynak_ids": sorted(found),
                "sure_ms": round((perf_counter() - start) * 1000, 3),
                **error,
            }
        )
    groups = {}
    for group in sorted({case.grup for case in cases}):
        subset = [row for row in rows if row["grup"] == group]
        groups[group] = {"n": len(subset), "gecen": sum(row["gecti"] for row in subset)}
    measured = [
        row["kontroller"].get("kaynak_hit_at_3", False)
        for case, row in zip(cases, rows, strict=True)
        if case.beklenen.kaynak_any_of
    ]
    return {
        "mod": "ajan_entegrasyonu" if predictor else "arac_ve_rag_bilesenleri",
        "rapor_surumu": 2,
        "tarih_utc": datetime.now(UTC).isoformat(),
        "derlem_sha256": retriever.fingerprint,
        "getirme_yapilandirmasi": getattr(retriever, "configuration", {"backend": "unknown"}),
        "n": len(rows),
        "gecen": sum(row["gecti"] for row in rows),
        "gecme_orani": sum(row["gecti"] for row in rows) / len(rows),
        "kaynak_hit_at_3": sum(measured) / len(measured) if measured else None,
        "kaynak_beklenen_vaka_sayisi": len(measured),
        "bilesen_gecen": sum(row["bilesen_gecti"] for row in rows),
        "ajan_gecen": sum(row["ajan_gecti"] is True for row in rows) if predictor else None,
        "hata_sayisi": sum("hata_turu" in row for row in rows),
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
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
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
