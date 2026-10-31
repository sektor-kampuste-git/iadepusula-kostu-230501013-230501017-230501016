from collections import Counter

import pytest

from eval.calibration import calibration
from eval.contracts import AgentPrediction
from eval.eval_kosucu import evaluate, load_cases


def test_dataset_has_30_cases_and_honest_unreviewed_labels():
    cases = load_cases()
    assert len(cases) == 30
    assert Counter(case.grup for case in cases) == {"standart": 18, "sinir": 6, "adversarial": 6}
    assert all(
        case.etiket_durumu == "ai_taslak" and case.insan_etiketleyen is None for case in cases
    )


def test_development_benchmark_meets_document_target_without_claiming_decision_accuracy():
    result = evaluate(load_cases())
    assert result["n"] == 30
    assert result["gecme_orani"] >= 0.85
    assert result["mod"] == "arac_ve_rag_bilesenleri"
    assert result["insan_hakem_kalibrasyonu"] == "yapilmadi"
    assert result["ajan_karar_dogrulugu"] == "insan_etiketleri_olmadan_olculmedi"


def test_runner_reports_failed_expectations_instead_of_hiding_them():
    case = load_cases()[0]
    wrong = case.model_copy(
        update={"beklenen": case.beklenen.model_copy(update={"cayma_durumu": "IMPOSSIBLE"})}
    )
    result = evaluate((wrong,))
    assert result["gecen"] == 0
    assert result["vakalar"][0]["kontroller"]["cayma"] is False


def test_predictor_schema_failure_counts_as_failure_and_does_not_leak_exception():
    result = evaluate(load_cases()[:1], predictor=lambda _: {"unstructured": "unsafe"})
    assert result["gecen"] == 0
    assert result["vakalar"][0]["hata_turu"] == "ValidationError"
    with pytest.raises(ValueError):
        AgentPrediction(
            karar_onerisi="KABUL_ONERILIR", kaynaklar=[], insan_onayi_gerekiyor_mu=False
        )


def test_calibration_requires_real_reviewers_and_sufficient_samples():
    with pytest.raises(ValueError, match="en az 10"):
        calibration([])
    with pytest.raises(ValueError, match="Gerçek"):
        calibration([{"id": "V01", "human_score": None, "judge_score": 1}])
    rows = [
        {
            "id": f"V{i}",
            "reviewer": "test-reviewer",
            "human_score": i % 2,
            "judge_score": i % 2 if i < 9 else 0,
        }
        for i in range(10)
    ]
    result = calibration(rows)
    assert result["agreement"] == 0.9
    assert result["cohens_kappa"] == pytest.approx(0.8)
