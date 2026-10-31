"""Doğrulanmış taslak ve başvuruya bağlı gerekçeli demo insan onayı."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.agent import RunReport
from src.case_binding import require_packet_binding
from src.contracts import IncelemePaketi
from src.human_review import paket_ozeti
from src.privacy import mask_pii, obvious_injection
from src.rag import MevzuatRetriever
from src.schemas import KararOnerisi, dogrula_karar_taslagi


class TaslakIncelemesi(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    paket_ozeti: str
    taslak_ozeti: str
    istek_id: str
    eylem: Literal["ONAYLA", "DEGISTIR"]
    ilk_oneri: KararOnerisi
    son_oneri: KararOnerisi
    tutar_tl: Decimal | None
    gerekce: str
    zaman_utc: str
    kimlik_dogrulandi: Literal[False] = False


def _taslak_ozeti(report: RunReport) -> str:
    if report.reason != "TASLAK_DOGRULANDI" or report.draft is None:
        raise ValueError("Doğrulanmış taslak olmadan öneri onaylanamaz.")
    return hashlib.sha256(report.draft.model_dump_json().encode()).hexdigest()


def kaydet_taslak_incelemesi(
    paket: IncelemePaketi,
    rapor: RunReport,
    *,
    eylem: str,
    gerekce: str,
    kaynaklar_okundu: bool,
    yeni_oneri: str | None = None,
    yeni_tutar: str | None = None,
) -> TaslakIncelemesi:
    require_packet_binding(paket, rapor.evidence_sha256)
    digest = _taslak_ozeti(rapor)
    if not paket.siparis or not paket.kaynaklar or kaynaklar_okundu is not True:
        raise ValueError("Önce siparişi, kaynakları ve uyarıları inceleyin.")
    if (
        not isinstance(gerekce, str)
        or not 10 <= len(gerekce.strip()) <= 1500
        or obvious_injection(gerekce)
    ):
        raise ValueError("Kişisel bilgi ve komut içermeyen 10–1500 karakter gerekçe yazın.")
    retriever = MevzuatRetriever()
    try:
        original = dogrula_karar_taslagi(rapor.draft, paket, retriever=retriever)
        raw = original.model_dump(mode="python")
        if eylem == "DEGISTIR":
            if yeni_oneri is None:
                raise ValueError("Yeni öneri seçilmelidir.")
            raw.update(
                karar_onerisi=yeni_oneri,
                hesaplanan_iade_tutari_tl=yeni_tutar,
                gerekce=mask_pii(gerekce.strip()),
            )
            # Eksik bilgi iddiaları değiştirme ile sessizce temizlenmez.
        elif eylem != "ONAYLA":
            raise ValueError("Geçersiz inceleme işlemi")
        final = dogrula_karar_taslagi(raw, paket, retriever=retriever)
    finally:
        retriever.close()
    return TaslakIncelemesi(
        paket_ozeti=paket_ozeti(paket),
        taslak_ozeti=digest,
        istek_id=rapor.request_id,
        eylem=eylem,
        ilk_oneri=original.karar_onerisi,
        son_oneri=final.karar_onerisi,
        tutar_tl=final.hesaplanan_iade_tutari_tl,
        gerekce=mask_pii(gerekce.strip()),
        zaman_utc=datetime.now(UTC).isoformat(),
    )


def taslak_raporu(paket, rapor, kayit: TaslakIncelemesi, *, mod: str) -> str:
    require_packet_binding(paket, rapor.evidence_sha256)
    if (
        kayit.paket_ozeti != paket_ozeti(paket)
        or kayit.taslak_ozeti != _taslak_ozeti(rapor)
        or kayit.istek_id != rapor.request_id
    ):
        raise ValueError("İnceleme bu başvuru ve taslağa ait değil.")
    return json.dumps(
        {
            "surum": "uye3-agent-ui-1",
            "mod": mod,
            "uyari": "Sentetik demo insan değerlendirmesi; hukuki karar veya ödeme değildir.",
            "siparis_no": paket.siparis.siparis_no,
            "inceleme": kayit.model_dump(mode="json", exclude={"gerekce"}),
            "kaynaklar": [c.chunk_id for c in rapor.draft.kaynaklar],
        },
        ensure_ascii=False,
        indent=2,
    )
