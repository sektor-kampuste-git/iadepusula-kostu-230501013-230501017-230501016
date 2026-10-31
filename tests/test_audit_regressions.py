import json
from datetime import date, datetime

import httpx
import pytest
from pydantic import SecretStr

from eval.calibration import calibration
from eval.contracts import Expected
from eval.eval_kosucu import evaluate, load_cases
from src.evidence import hazirla_inceleme
from src.evren import EvrenAdapter, ProviderError, ProviderSettings
from src.privacy import mask_pii, outside_scope
from src.rag import MevzuatRetriever, tokenize
from src.tools import cayma_suresi_hesapla


@pytest.mark.parametrize(
    "text",
    [
        "Aldığım elbise iade etmek istiyorum",
        "Kriptografi kitabının iadesini istiyorum",
        "Ürünü kripto para ile ödedim, bozuk geldi",
    ],
)
def test_valid_consumer_complaint_is_not_blocked_by_word_substrings(text):
    assert not outside_scope(text)
    packet = hazirla_inceleme("SIP-2026-1001", text, "2026-10-31")
    assert packet.siparis is not None and "KAPSAM_DISI" not in packet.uyarilar


@pytest.mark.parametrize(
    "text", ["İşe iade davası", "Ceza davasında ne yapmalıyım?", "Bana kripto al-sat botu yaz"]
)
def test_explicit_unrelated_tasks_remain_out_of_scope(text):
    assert outside_scope(text)


@pytest.mark.parametrize(
    "text",
    [
        "TCKN: 123 456 789 01",
        "TCKN 123.456.789.01",
        "Telefon 0212 555 55 55",
        "Telefon +90 (212) 555 55 55",
        "Telefon 0850 555 55 55",
        "TCKN12345678901",
        "tel02125555555",
    ],
)
def test_common_pii_formats_are_removed_before_evidence(text):
    safe = mask_pii(text)
    assert "MASKELENDI" in safe
    assert len([char for char in safe if char.isdigit()]) == 0


@pytest.mark.parametrize(
    "query, ids",
    [
        ("MSY Madde 9/2", {"MSY-M9-F2"}),
        ("Mesafeli Sözleşmeler Yönetmeliği Madde 15/1-ç", {"MSY-M15-ç"}),
        ("MSY Madde 15/1-c", {"MSY-M15-c"}),
        ("TKHK 9. maddesi", {"6502-M9-F1", "6502-M9-F2"}),
        ("6502 Madde 8/1", {"6502-M8-F1"}),
        (
            "6502 sayılı Kanunun 11 inci maddesi",
            {
                "6502-M11-F1",
                "6502-M11-F2",
                "6502-M11-F3",
                "6502-M11-F4",
                "6502-M11-F5",
                "6502-M11-F6",
            },
        ),
    ],
)
def test_explicit_instrument_paragraph_and_letter_are_respected(query, ids):
    found = MevzuatRetriever().search(query, top_k=10)
    assert found and {row.parca.chunk_id for row in found} == ids


def test_multiple_provisions_are_covered_and_unknown_provision_is_not_dropped():
    rag = MevzuatRetriever()
    found = rag.search("6502 Madde 8 ve Madde 11")
    assert any(row.parca.madde.startswith("Madde 8/") for row in found)
    assert any(row.parca.madde.startswith("Madde 11/") for row in found)
    assert all(row.istek_kirpildi and row.istek_eslesme_sayisi == 9 for row in found)
    assert rag.search("6502 Madde 8 ve Madde 987") == ()
    assert rag.search("Madde 11") == ()
    assert rag.search("Madde 11", belge_ids={"6502"})


def test_inflected_words_and_normalized_stopwords():
    assert tokenize("İÇİN göre mı mü") == []
    found = MevzuatRetriever().search("ürün bozuktu")
    assert found and any(row.parca.belge_id == "6502" for row in found)


def test_context_and_authority_cannot_be_removed_or_forged_in_citation():
    rag = MevzuatRetriever()
    cite = rag.citation_for("MSY-M15-ç")
    assert cite.baglam and rag.verify_citation(cite)
    assert not rag.verify_citation(cite.model_copy(update={"baglam": None}))
    guide = rag.citation_for("REHBER-KARGO")
    assert guide.kaynak_turu == "resmi_rehber"
    assert not rag.verify_citation(guide.model_copy(update={"kaynak_turu": "kanun"}))
    assert rag.by_id["6502-M11-F1"].kaynak_sayfalari == (9,)
    assert rag.by_id["MSY-M15-ç"].kaynak_sayfalari == (150,)
    assert not rag.verify_citation(cite.model_copy(update={"kaynak_sayfalari": (1,)}))


def test_predictor_only_receives_label_free_masked_evidence():
    seen = []

    def predictor(input):
        seen.append(input)
        assert not hasattr(input, "beklenen")
        assert not hasattr(input, "taslak_karar")
        assert "12345678901" not in input.model_dump_json()
        return {
            "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
            "kaynaklar": [],
            "insan_onayi_gerekiyor_mu": True,
        }

    evaluate((load_cases()[28],), predictor=predictor)
    assert len(seen) == 1


def test_predictor_failure_preserves_component_metrics_and_latency():
    result = evaluate(load_cases()[:1], predictor=lambda _: {"invalid": True})
    row = result["vakalar"][0]
    assert result["gecen"] == 0 and result["bilesen_gecen"] == 1
    assert result["kaynak_hit_at_3"] == 1.0 and result["kaynak_beklenen_vaka_sayisi"] == 1
    assert row["hata_asamasi"] == "ajan" and row["sure_ms"] > 0


def test_failed_retrieval_does_not_shrink_metric_denominator():
    class FailedRetriever:
        fingerprint = "test"

        def search(self, *args, **kwargs):
            raise RuntimeError("sensitive provider details")

    result = evaluate(load_cases()[:1], retriever=FailedRetriever())
    assert result["kaynak_hit_at_3"] == 0 and result["kaynak_beklenen_vaka_sayisi"] == 1
    assert result["hata_sayisi"] == 1 and "sensitive provider details" not in json.dumps(result)


@pytest.mark.parametrize(
    "data", [{}, {"kaynak_bos": True, "kaynak_any_of": ["MSY-M9-F1"]}, {"cayma_durumu": "TYPO"}]
)
def test_empty_contradictory_and_misspelled_expectations_are_rejected(data):
    with pytest.raises(ValueError):
        Expected.model_validate(data)


@pytest.mark.parametrize("score", [True, False, 1.0, "1"])
def test_calibration_requires_integer_scores_and_nonempty_reviewer(score):
    with pytest.raises(ValueError):
        calibration(
            [
                {"id": f"V{i}", "reviewer": "reviewer", "human_score": score, "judge_score": 1}
                for i in range(10)
            ]
        )


@pytest.mark.parametrize("payload", [{"data": [None]}, {"data": ["model"]}, {"data": None}, {}])
def test_malformed_model_list_raises_public_provider_error(payload):
    settings = ProviderSettings(api_key=SecretStr("not-real"))
    with EvrenAdapter(
        settings, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    ) as adapter:
        with pytest.raises(ProviderError):
            adapter.models()


@pytest.mark.parametrize("content", [None, [], "null", "[]", "42"])
def test_malformed_completion_content_is_rejected_at_boundary(content):
    payload = {"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
    with EvrenAdapter(
        ProviderSettings(api_key=SecretStr("not-real")),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
    ) as adapter:
        with pytest.raises(ProviderError):
            adapter.synthetic_completion([])


@pytest.mark.parametrize("texts", ["cayma", b"cayma", [None], [""], [123]])
def test_bad_embedding_input_is_rejected_before_network(texts):
    def forbidden(_):
        pytest.fail("Invalid input reached provider")

    with EvrenAdapter(
        ProviderSettings(api_key=SecretStr("not-real")), transport=httpx.MockTransport(forbidden)
    ) as adapter:
        with pytest.raises(ValueError):
            adapter.embed(texts)


def test_invalid_dates_and_unicode_expansion_have_clear_input_errors():
    with pytest.raises(ValueError):
        hazirla_inceleme("SIP-2026-1001", "Ürünü iade istiyorum", datetime(2026, 10, 31))
    with pytest.raises(ValueError):
        hazirla_inceleme("SIP-2026-1001", "㍿" * 1500, date(2026, 10, 31))
    with pytest.raises(ValueError):
        cayma_suresi_hesapla("9999-12-20", "9999-12-31")
    with pytest.raises(ValueError):
        cayma_suresi_hesapla("2026-10-01", "2026-10-10", bilgilendirme_tarihi="")


@pytest.mark.parametrize("embedding", [[0, 0], [True, 1], ["1", "2"], [10**400, 1]])
def test_provider_vector_contract_rejects_zero_boolean_and_string_values(embedding):
    payload = {"data": [{"index": 0, "embedding": embedding}]}
    with EvrenAdapter(
        ProviderSettings(api_key=SecretStr("not-real")),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
    ) as adapter:
        with pytest.raises(ProviderError):
            adapter.embed(["cayma"])
