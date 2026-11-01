import copy
import json
import math

import httpx
import pytest
from pydantic import SecretStr

from eval.retrieval import (
    RetrievalCase,
    api_summary,
    benchmark,
    load_retrieval_cases,
    percentile,
    score_ranking,
)
from src.contracts import AramaSonucu
from src.evren import EvrenAdapter, ProviderError, ProviderSettings, RequestObservation
from src.rag import MevzuatRetriever


def case(**changes):
    values = {"id": "RQ01", "category": "ayip", "query": "örnek sorgu", "relevant_ids": ("a", "b")}
    return RetrievalCase.model_validate(values | changes)


def test_ranking_metrics_use_true_ranks_and_fixed_k():
    result = score_ranking(case(), ["x", "b", "a"], 3)
    assert result["hit_at_k"] is True and result["recall_at_k"] == 1
    assert result["precision_at_k"] == pytest.approx(2 / 3)
    assert result["mrr_at_k"] == 0.5
    assert result["ndcg_at_k"] == pytest.approx((1 / math.log2(3) + 0.5) / (1 + 1 / math.log2(3)))
    assert score_ranking(case(), ["a"], 3)["precision_at_k"] == pytest.approx(1 / 3)


def test_duplicate_results_do_not_inflate_relevance():
    result = score_ranking(case(), ["a", "a", "b"], 3)
    assert result["recall_at_k"] == 1 and result["precision_at_k"] == pytest.approx(2 / 3)
    assert result["ndcg_at_k"] < 1


@pytest.mark.parametrize("ranking", [[], ["x"], ["x", "y"]])
def test_misses_are_zero_for_every_positive_metric(ranking):
    assert all(value == 0 for value in score_ranking(case(), ranking, 3).values())


def test_negative_metrics_are_separate_from_retrieval_metrics():
    negative = case(relevant_ids=(), expected_empty=True)
    assert score_ranking(negative, [], 3) == {"empty_correct": True}
    assert score_ranking(negative, ["x"], 3) == {"empty_correct": False}


@pytest.mark.parametrize(
    "invalid",
    [
        {"relevant_ids": ()},
        {"expected_empty": True},
        {"relevant_ids": ("a", "a")},
        {"label_status": "insan_dogruladi"},
    ],
)
def test_inconsistent_query_labels_fail_before_running(invalid):
    with pytest.raises(ValueError):
        case(**invalid)


def test_dataset_is_explicitly_unreviewed_and_covers_positive_and_negative_queries():
    cases = load_retrieval_cases()
    assert len(cases) == 44 and sum(c.expected_empty for c in cases) == 9
    assert all(c.label_status == "ai_taslak" and c.reviewer is None for c in cases)


def test_missing_usage_is_unknown_while_no_requests_is_zero():
    assert api_summary([])["total_tokens"] == 0
    missing = RequestObservation(endpoint="embeddings", status_code=200, elapsed_ms=1)
    known = RequestObservation(
        endpoint="embeddings", status_code=200, elapsed_ms=1, total_tokens=10
    )
    summary = api_summary([missing, known])
    assert summary["total_tokens"] == 10 and summary["total_tokens_reported_requests"] == 1
    assert summary["prompt_tokens"] is None


def test_percentiles_are_interpolated_and_never_invent_empty_timing():
    assert percentile([], 0.95) is None
    assert percentile([7], 0.95) == 7
    assert percentile([10, 0], 0.5) == 5
    assert percentile([10, 0], 0.95) == pytest.approx(9.5)


class FakeRetriever:
    def __init__(self, *, preparation_error=False, errors=0, status_code=None):
        self.base = MevzuatRetriever()
        self.by_id = self.base.by_id
        self.fingerprint = self.base.fingerprint
        self.configuration = {"backend": "test"}
        self.cache_status = "disabled"
        self.preparation_error = preparation_error
        self.errors = errors
        self.status_code = status_code
        self.calls = 0
        self.closed = False
        self.prepared = False

    def prepare(self):
        self.prepared = True
        if self.preparation_error:
            raise RuntimeError("sensitive internal data")

    def search(self, query, *, top_k):
        assert self.prepared
        self.calls += 1
        if self.calls <= self.errors:
            raise ProviderError("sensitive internal data", status_code=self.status_code)
        return (AramaSonucu(parca=self.by_id["MSY-M9-F2"], skor=1, yontem="bm25"),)

    def close(self):
        self.closed = True


def test_backend_never_receives_gold_labels_and_preparation_is_separate():
    retriever = FakeRetriever()
    result = benchmark(load_retrieval_cases()[:2], lambda: retriever, name="test")
    assert result["preparation"]["status"] == "ok"
    assert result["summary"]["completed"] == 2
    assert retriever.closed and retriever.calls == 2


def test_transient_failure_stays_in_all_positive_denominators():
    retriever = FakeRetriever(errors=1)
    result = benchmark(load_retrieval_cases()[:2], lambda: retriever, name="test")
    summary = result["summary"]
    assert summary["positive_n"] == 2 and summary["errors"] == 1 and summary["completed"] == 1
    assert summary["hit_at_k"] == 0.5 and result["rows"][0]["elapsed_ms"] is not None
    assert "sensitive internal data" not in json.dumps(result)


def test_failed_negative_query_never_counts_as_correct_abstention():
    negative = load_retrieval_cases()[34:35]
    result = benchmark(negative, lambda: FakeRetriever(errors=1), name="test")
    assert result["summary"]["empty_accuracy"] == 0


@pytest.mark.parametrize("status", [401, 403, 429])
def test_auth_or_quota_failure_stops_additional_provider_attempts(status):
    retriever = FakeRetriever(errors=5, status_code=status)
    result = benchmark(load_retrieval_cases()[:5], lambda: retriever, name="test")
    assert retriever.calls == 1
    assert result["summary"]["errors"] == 1 and result["summary"]["not_run"] == 4
    assert result["summary"]["hit_at_k"] == 0


def test_three_consecutive_errors_open_the_backend_circuit():
    retriever = FakeRetriever(errors=10)
    result = benchmark(load_retrieval_cases()[:5], lambda: retriever, name="test")
    assert retriever.calls == 3 and result["summary"]["not_run"] == 2


def test_preparation_failure_preserves_all_scheduled_queries_and_closes_resources():
    retriever = FakeRetriever(preparation_error=True)
    result = benchmark(load_retrieval_cases(), lambda: retriever, name="test")
    assert result["summary"]["not_run"] == 44
    assert result["summary"]["hit_at_k"] == 0 and result["summary"]["empty_accuracy"] == 0
    assert result["summary"]["p95_completed_ms"] is None
    assert retriever.closed


def test_provider_observations_whitelist_usage_and_omit_request_data():
    secret = "fake-sensitive-provider-field"
    body = {
        "data": [{"index": 0, "embedding": [1.0]}],
        "usage": {
            "prompt_tokens": 12,
            "total_tokens": 12,
            "completion_tokens": True,
            "account": secret,
            "quota": 9000,
        },
    }
    with EvrenAdapter(
        ProviderSettings(api_key=SecretStr(secret)),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)),
    ) as provider:
        provider.embed(["public source"])
        assert provider.last_usage == {"prompt_tokens": 12, "total_tokens": 12}
        assert provider.observations[0].completion_tokens is None
        serialized = json.dumps([o.model_dump() for o in provider.observations])
        assert (
            secret not in serialized
            and "public source" not in serialized
            and "quota" not in serialized
        )


def test_bad_dataset_invalidates_old_json_and_markdown_reports(tmp_path, monkeypatch):
    from eval.retrieval_benchmark import main

    dataset = tmp_path / "bad.json"
    dataset.write_text("broken")
    output = tmp_path / "result.json"
    output.write_text('{"status":"complete"}')
    output.with_suffix(".md").write_text("Old success")
    monkeypatch.setattr(
        "sys.argv", ["benchmark", "--dataset", str(dataset), "--output", str(output)]
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 1
    assert json.loads(output.read_text())["status"] == "failed"
    assert "Old success" not in output.with_suffix(".md").read_text()


def test_lexical_benchmark_is_network_free_and_separates_reference_guards():
    result = benchmark(load_retrieval_cases(), MevzuatRetriever, name="lexical")
    assert result["api"]["request_count"] == 0
    assert result["summary"]["reference_negative_n"] == 4
    assert result["summary"]["natural_negative_n"] == 5
    assert result["summary"]["completed"] == 44
    assert result["summary"]["hit_at_k"] >= 0.85


@pytest.fixture(scope="module")
def review_report():
    result = benchmark(load_retrieval_cases(), MevzuatRetriever, name="lexical")
    second = copy.deepcopy(result)
    second["name"] = "evren"
    return {"schema_version": 1, "backends": {"lexical": result, "evren": second}}


def export_review(report, path):
    from eval.review_pack import export_pack

    export_pack(report, path)
    return path.with_suffix(".manifest.json")


def fill_reviews(path, *, backend=None, manifest=None):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mappings = json.loads(manifest.read_text())["items"] if manifest else None
    for row in rows:
        if backend is None or mappings[row["id"]]["backend"] == backend:
            row.update(
                human_score=1,
                judge_score=1,
                reviewer="unit-test-reviewer",
                judge_model="unit-test-judge",
            )
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8"
    )
    return rows


def test_review_export_is_label_free_blinded_and_unscored(review_report, tmp_path):
    from eval.review_pack import score_pack

    path = tmp_path / "review.jsonl"
    manifest = export_review(review_report, path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 20
    for row in rows:
        assert row["human_score"] is None and row["judge_score"] is None
        assert not set(row).intersection(
            {"backend", "metrics", "relevant_ids", "expected_empty", "yontem"}
        )
    assert "lexical" not in path.with_suffix(".md").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="10 ayrı"):
        score_pack(path, manifest)


def test_real_review_extraction_requires_ten_distinct_queries(review_report, tmp_path):
    from eval.review_pack import score_pack

    path = tmp_path / "review.jsonl"
    manifest = export_review(review_report, path)
    fill_reviews(path)
    result = score_pack(path, manifest)
    assert result["reviewed_outputs"] == 20 and result["reviewed_queries"] == 10
    assert result["overall"]["agreement"] == 1 and result["overall"]["cohens_kappa"] is None
    assert "unit-test-reviewer" not in json.dumps(result)


def test_unreviewed_outputs_are_pending_not_successful(review_report, tmp_path):
    from eval.review_pack import score_pack

    path = tmp_path / "review.jsonl"
    manifest = export_review(review_report, path)
    fill_reviews(path, backend="lexical", manifest=manifest)
    result = score_pack(path, manifest)
    assert result["reviewed_outputs"] == 10 and result["pending_outputs"] == 10
    assert result["by_backend"]["evren"]["status"] == "yetersiz_ornek"


@pytest.mark.parametrize("tamper", ["query", "duplicate", "model", "reviewer"])
def test_changed_evidence_invalid_grades_or_mixed_judges_are_rejected(
    review_report, tmp_path, tamper
):
    from eval.review_pack import score_pack

    path = tmp_path / "review.jsonl"
    manifest = export_review(review_report, path)
    rows = fill_reviews(path)
    if tamper == "query":
        rows[0]["query"] += " altered"
    elif tamper == "duplicate":
        rows[1]["id"] = rows[0]["id"]
    elif tamper == "model":
        rows[0]["judge_model"] = "another-version"
    else:
        rows[0]["reviewer"] = " "
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    with pytest.raises(ValueError):
        score_pack(path, manifest)


def test_review_export_rejects_a_different_corpus_snapshot(review_report, tmp_path):
    bad = copy.deepcopy(review_report)
    bad["backends"]["evren"]["corpus_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="derlem sürümü"):
        export_review(bad, tmp_path / "review.jsonl")


def test_review_export_rejects_mixed_questions_under_same_id(review_report, tmp_path):
    bad = copy.deepcopy(review_report)
    bad["backends"]["evren"]["rows"][0]["query"] = "Başka bir tüketici sorusu"
    with pytest.raises(ValueError, match="farklı sorular"):
        export_review(bad, tmp_path / "review.jsonl")


def test_duplicate_benchmark_queries_do_not_inflate_sample_size(tmp_path):
    rows = [load_retrieval_cases()[0].model_dump(mode="json")] * 2
    rows[1] = rows[1] | {"id": "RQ99"}
    path = tmp_path / "duplicates.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match="Aynı sorgu"):
        load_retrieval_cases(path)


def test_incomplete_review_cannot_leave_old_calibration_success(
    review_report, tmp_path, monkeypatch
):
    from eval.review_pack import main

    pack = tmp_path / "review.jsonl"
    manifest = export_review(review_report, pack)
    output = tmp_path / "calibration.json"
    output.write_text('{"status":"complete","agreement":1}')
    monkeypatch.setattr(
        "sys.argv",
        [
            "review",
            "score",
            "--pack",
            str(pack),
            "--manifest",
            str(manifest),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 1
    assert json.loads(output.read_text())["status"] == "not_calibrated"


@pytest.mark.parametrize("contents", ["null", "42", "{}", "[]"])
def test_invalid_dataset_shape_leaves_a_failed_report(tmp_path, monkeypatch, contents):
    from eval.retrieval_benchmark import main

    dataset = tmp_path / "bad.json"
    dataset.write_text(contents)
    output = tmp_path / "result.json"
    monkeypatch.setattr(
        "sys.argv", ["benchmark", "--dataset", str(dataset), "--output", str(output)]
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 1
    assert json.loads(output.read_text())["status"] == "failed"


def test_benchmark_companion_cannot_overwrite_input_dataset(tmp_path, monkeypatch):
    from eval.retrieval_benchmark import main

    dataset = tmp_path / "cases.md"
    contents = json.dumps([load_retrieval_cases()[0].model_dump(mode="json")])
    dataset.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["benchmark", "--dataset", str(dataset), "--output", str(dataset.with_suffix(".json"))],
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 2
    assert dataset.read_text(encoding="utf-8") == contents
    assert not dataset.with_suffix(".json").exists()


@pytest.mark.parametrize("suffix", [".manifest.json", ".md"])
def test_review_companions_cannot_overwrite_the_source_report(tmp_path, monkeypatch, suffix):
    from eval.review_pack import main

    pack = tmp_path / "review.jsonl"
    report = pack.with_suffix(suffix)
    report.write_text("original-report")
    monkeypatch.setattr(
        "sys.argv", ["review", "export", "--report", str(report), "--output", str(pack)]
    )
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 2
    assert report.read_text() == "original-report"
    assert not pack.exists()
