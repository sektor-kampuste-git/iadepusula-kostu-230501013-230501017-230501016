"""Üye 1 kanıtı, Üye 2 taslağı ve Üye 3 onayının aynı başvuruya bağlanması."""

from datetime import date

import pytest

from src.agent_review import kaydet_taslak_incelemesi
from src.case_binding import evidence_digest, require_packet_binding
from src.evidence import hazirla_inceleme
from src.ui_service import calistir_inceleme

DAY = date(2026, 10, 31)


@pytest.mark.parametrize("padding", ["  ", "\n"])
def test_prepared_packet_allows_outer_whitespace_without_changing_bound_evidence(padding):
    result = calistir_inceleme(
        "SIP-2026-1002", padding + "Kulaklık bozuk iade istiyorum" + padding, DAY, mod="demo"
    )
    assert result.rapor.reason == "TASLAK_DOGRULANDI"
    assert result.rapor.evidence_sha256 == evidence_digest(result.paket)
    assert result.paket.maskelenmis_basvuru.startswith(padding)


def test_report_cannot_be_approved_for_a_different_complaint_with_same_sources():
    result = calistir_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY, mod="demo")
    other = result.paket.model_copy(
        update={"maskelenmis_basvuru": "Aynı sipariş hakkında farklı bir başvuru metni."}
    )
    with pytest.raises(ValueError, match="başvuru"):
        kaydet_taslak_incelemesi(
            other,
            result.rapor,
            eylem="ONAYLA",
            gerekce="Kaynakları inceledim, uzman incelemesi gerekiyor.",
            kaynaklar_okundu=True,
        )


def test_ui_and_agent_prepare_the_evidence_only_once(monkeypatch):
    seen = []

    def counted(*args, **kwargs):
        seen.append(args)
        return hazirla_inceleme(*args, **kwargs)

    monkeypatch.setattr("src.ui_service.hazirla_inceleme", counted)
    monkeypatch.setattr("src.agent.hazirla_inceleme", counted)
    result = calistir_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY, mod="demo")
    assert result.rapor.reason == "TASLAK_DOGRULANDI"
    assert len(seen) == 1


def test_duration_and_ranking_score_do_not_change_business_identity():
    packet = hazirla_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY)
    changed = packet.model_copy(
        update={
            "arac_izleri": tuple(
                row.model_copy(update={"sure_ms": 999}) for row in packet.arac_izleri
            ),
            "kaynaklar": tuple(
                row.model_copy(update={"skor": row.skor + 10}) for row in packet.kaynaklar
            ),
        }
    )
    assert evidence_digest(packet) == evidence_digest(changed)


@pytest.mark.parametrize(
    "updates",
    [
        {"basvuru_tarihi": date(2026, 11, 1)},
        {"maskelenmis_basvuru": "Farklı başvuru açıklaması."},
        {"uyarilar": ("FARKLI_UYARI",)},
    ],
)
def test_business_changes_invalidate_binding(updates):
    packet = hazirla_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY)
    with pytest.raises(ValueError, match="başvuru"):
        require_packet_binding(packet.model_copy(update=updates), evidence_digest(packet))


@pytest.mark.parametrize("invalid", [None, "", "0" * 64, "ğ" * 64])
def test_missing_or_invalid_binding_fails_closed(invalid):
    packet = hazirla_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY)
    with pytest.raises(ValueError, match="başvuru"):
        require_packet_binding(packet, invalid)


def test_packet_reuse_preserves_caller_retriever_lifetime(monkeypatch):
    from src.agent import ButceliAjan
    from src.rag import MevzuatRetriever

    result = calistir_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY, mod="demo")
    assert result.rapor.evidence_sha256 == evidence_digest(result.paket)
    rag = MevzuatRetriever()
    closed = []
    monkeypatch.setattr(rag, "close", lambda: closed.append(True))

    # Yerel fiyat yoksa da kanıt, yaşam döngüsü ve çağrı öncesi durma kontrolü çalışmalı.
    class Client:
        settings = None

    agent = ButceliAjan(Client(), None)
    report = agent.run_packet(result.paket, retriever=rag, sentetik=True)
    assert report.reason == "TARIFE_YOK" and report.model_calls == 0
    assert closed == []


def test_packet_without_application_date_cannot_enter_model_workflow():
    from src.agent import ButceliAjan

    class Client:
        settings = None

    packet = hazirla_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY)
    report = ButceliAjan(Client(), None).run_packet(
        packet.model_copy(update={"basvuru_tarihi": None}), sentetik=True
    )
    assert report.reason == "GIRDI_HATASI" and report.model_calls == 0


@pytest.mark.parametrize(
    "unsafe", ["Kulaklık bozuk test@example.invalid", "Kulaklık\u200b bozuk iade istiyorum"]
)
def test_packet_whitespace_tolerance_does_not_allow_unprepared_sensitive_or_hidden_text(unsafe):
    from src.agent import ButceliAjan

    class Client:
        settings = None

    packet = hazirla_inceleme("SIP-2026-1002", "Kulaklık bozuk iade istiyorum", DAY)
    changed = packet.model_copy(update={"maskelenmis_basvuru": unsafe})
    report = ButceliAjan(Client(), None).run_packet(changed, sentetik=True)
    assert report.reason == "GIRDI_HATASI" and report.model_calls == 0
