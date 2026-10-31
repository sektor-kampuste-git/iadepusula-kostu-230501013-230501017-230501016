"""Üye 2'nin taslak sınırı: sentetik verilerle ağsız davranış testleri."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from eval.contracts import AgentPrediction
from src.evidence import hazirla_inceleme
from src.rag import MevzuatRetriever
from src.schemas import KararTaslagi, TaslakDogrulamaHatasi, dogrula_karar_taslagi


@pytest.fixture
def evidence():
    rag = MevzuatRetriever()
    packet = hazirla_inceleme(
        "SIP-2026-1001",
        "Gömlekte cayma hakkını kullanmak ve iade etmek istiyorum.",
        date(2026, 10, 31),
        retriever=rag,
    )
    yield rag, packet
    rag.close()


def candidate(rag, packet, **updates):
    """Model çağrısı yapmadan aday veri kur; doğruluğu bilinen kanıtları kullan."""
    raw = {
        "sorgu_ozeti": "Sentetik sipariş için iade başvurusu alındı.",
        "karar_onerisi": "KABUL_ONERILIR",
        "gerekce": "Bu yalnız test taslağıdır; kaynaklar insan uzman tarafından incelenmelidir.",
        "kaynaklar": [rag.citation_for(packet.kaynaklar[0].parca.chunk_id).model_dump()],
        "hesaplanan_iade_tutari_tl": "1200.00",
        "insan_onayi_gerekiyor_mu": True,
    }
    return raw | updates


def test_valid_draft_uses_member_one_packet_and_existing_eval_contract(evidence):
    rag, packet = evidence
    result = dogrula_karar_taslagi(candidate(rag, packet), packet, retriever=rag)
    assert result.hesaplanan_iade_tutari_tl == Decimal("1200.00")
    assert result.insan_onayi_gerekiyor_mu is True
    prediction = AgentPrediction.model_validate(result.eval_ciktisi())
    assert prediction.karar_onerisi == result.karar_onerisi
    assert prediction.kaynaklar == result.kaynaklar


@pytest.mark.parametrize("decision", ["KABUL_ONERILIR", "RED_ONERILIR"])
def test_accept_and_reject_require_sources(evidence, decision):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(
                rag, packet, karar_onerisi=decision, kaynaklar=[], hesaplanan_iade_tutari_tl=None
            ),
            packet,
            retriever=rag,
        )


def test_expert_referral_without_sources_or_amount_is_valid(evidence):
    rag, packet = evidence
    unknown = hazirla_inceleme("SIP-2026-9999", "İade başvurusu yapmak istiyorum", "2026-10-31")
    raw = candidate(
        rag,
        packet,
        karar_onerisi="UZMAN_INCELEMESI_GEREKLI",
        kaynaklar=[],
        hesaplanan_iade_tutari_tl=None,
        eksik_bilgiler=["Sipariş kaydı bulunamadı."],
    )
    assert dogrula_karar_taslagi(raw, unknown, retriever=rag).insan_onayi_gerekiyor_mu is True


@pytest.mark.parametrize("value", [False, 0, 1, "true", None])
def test_model_cannot_disable_or_coerce_human_review(evidence, value):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(rag, packet, insan_onayi_gerekiyor_mu=value), packet, retriever=rag
        )


@pytest.mark.parametrize("value", [1200.0, True, "-1", "1200.001", "NaN", "Infinity"])
def test_money_rejects_float_boolean_precision_and_nonfinite_values(evidence, value):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(rag, packet, hesaplanan_iade_tutari_tl=value), packet, retriever=rag
        )


def test_amount_compares_with_trusted_invoice_not_model_supplied_invoice(evidence):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi, match="fatura sınırı"):
        dogrula_karar_taslagi(
            candidate(rag, packet, hesaplanan_iade_tutari_tl="1200.01"), packet, retriever=rag
        )
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(rag, packet, fatura_tutari_tl="999999.00"), packet, retriever=rag
        )


@pytest.mark.parametrize("decision", ["RED_ONERILIR", "UZMAN_INCELEMESI_GEREKLI"])
def test_nonaccepting_draft_cannot_include_positive_refund(evidence, decision):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(candidate(rag, packet, karar_onerisi=decision), packet, retriever=rag)


@pytest.mark.parametrize("where", ["sorgu_ozeti", "gerekce", "eksik_bilgiler", "kaynaklar"])
@pytest.mark.parametrize("pii", ["12345678901", "demo@example.invalid", "+90 (212) 555 55 55"])
def test_all_output_texts_reject_known_pii_and_public_error_hides_value(evidence, where, pii):
    rag, packet = evidence
    raw = candidate(rag, packet)
    if where == "eksik_bilgiler":
        raw.update(
            karar_onerisi="UZMAN_INCELEMESI_GEREKLI",
            hesaplanan_iade_tutari_tl=None,
            eksik_bilgiler=["Eksik bilgi: " + pii],
        )
    elif where == "kaynaklar":
        raw["kaynaklar"][0]["dogrudan_alinti"] = "Kişisel veri içeren alıntı: " + pii
    else:
        raw[where] = "Kişisel veri içeren çıktı: " + pii
    with pytest.raises(TaslakDogrulamaHatasi) as error:
        dogrula_karar_taslagi(raw, packet, retriever=rag)
    assert pii not in str(error.value)


def test_real_corpus_source_not_retrieved_for_request_is_rejected(evidence):
    rag, packet = evidence
    allowed = {row.parca.chunk_id for row in packet.kaynaklar}
    other_id = next(chunk_id for chunk_id in rag.by_id if chunk_id not in allowed)
    raw = candidate(rag, packet, kaynaklar=[rag.citation_for(other_id).model_dump()])
    with pytest.raises(TaslakDogrulamaHatasi, match="bu istekte"):
        dogrula_karar_taslagi(raw, packet, retriever=rag)


@pytest.mark.parametrize(
    "field,value",
    [
        ("dogrudan_alinti", "Belgede bulunmayan uydurma alıntı metnidir."),
        ("kaynak_url", "https://example.invalid/sahte"),
        ("madde", "Madde 987"),
        ("belge_id", "SAHTE_BELGE"),
        ("baglam", "Model tarafından eklenen farklı koşul."),
        ("kaynak_sayfalari", [999]),
    ],
)
def test_citation_metadata_and_quote_must_match_member_one_verifier(evidence, field, value):
    rag, packet = evidence
    raw = candidate(rag, packet)
    raw["kaynaklar"][0][field] = value
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(raw, packet, retriever=rag)


def test_model_copy_cannot_bypass_boundary_revalidation(evidence):
    rag, packet = evidence
    draft = dogrula_karar_taslagi(candidate(rag, packet), packet, retriever=rag)
    forged = draft.model_copy(update={"insan_onayi_gerekiyor_mu": False})
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(forged, packet, retriever=rag)
    forged_cite = draft.kaynaklar[0].model_copy(update={"dogrudan_alinti": ""})
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(rag, packet, kaynaklar=[forged_cite]), packet, retriever=rag
        )


@pytest.mark.parametrize("missing", [["  "], ["Belge", "Belge"], ["x" * 301]])
def test_missing_information_items_have_meaningful_limits(evidence, missing):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(
                rag,
                packet,
                karar_onerisi="UZMAN_INCELEMESI_GEREKLI",
                hesaplanan_iade_tutari_tl=None,
                eksik_bilgiler=missing,
            ),
            packet,
            retriever=rag,
        )


def test_incomplete_information_cannot_be_reported_as_acceptance(evidence):
    rag, packet = evidence
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(
            candidate(rag, packet, eksik_bilgiler=["Teslim kanıtı gerekli."]), packet, retriever=rag
        )


def test_unknown_order_cannot_get_acceptance_even_with_forged_packet_sources(evidence):
    rag, packet = evidence
    unknown = packet.model_copy(update={"siparis": None})
    with pytest.raises(TaslakDogrulamaHatasi, match="uzman incelemesi"):
        dogrula_karar_taslagi(
            candidate(rag, packet, hesaplanan_iade_tutari_tl=None), unknown, retriever=rag
        )


def test_repeated_source_ids_and_whitespace_only_rationale_are_rejected(evidence):
    rag, packet = evidence
    raw = candidate(rag, packet)
    raw["kaynaklar"] *= 2
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(raw, packet, retriever=rag)
    with pytest.raises(TaslakDogrulamaHatasi):
        dogrula_karar_taslagi(candidate(rag, packet, gerekce=" " * 30), packet, retriever=rag)


def test_frozen_schema_does_not_allow_assignment(evidence):
    rag, packet = evidence
    draft = KararTaslagi.model_validate(candidate(rag, packet))
    with pytest.raises(ValidationError):
        draft.karar_onerisi = "RED_ONERILIR"
