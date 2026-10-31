"""Üye 3: tek kanıt paketine bağlı, kimlik doğrulamasız demo inceleme kaydı."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.contracts import IncelemePaketi
from src.privacy import mask_pii, obvious_injection


class InsanIncelemesi(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    paket_ozeti: str
    sonuc: Literal["EK_BILGI_ISTENDI", "UZMANA_YONLENDIRILDI", "ON_INCELEME_TAMAMLANDI"]
    gerekce: str = Field(min_length=10, max_length=1500)
    kaynak_kimlikleri: tuple[str, ...]
    zaman_utc: str
    kimlik_dogrulandi: Literal[False] = False
    ortam: Literal["sentetik_demo"] = "sentetik_demo"


def paket_ozeti(paket: IncelemePaketi) -> str:
    """Gerekçe ve onayın farklı başvurulara taşınmasını önler."""
    return hashlib.sha256(paket.model_dump_json().encode()).hexdigest()


def kaydet_inceleme(paket, sonuc, gerekce, kaynaklar_okundu):
    if not paket.siparis or not paket.kaynaklar:
        raise ValueError("Sipariş ve kaynak olmadan inceleme tamamlanamaz.")
    if not kaynaklar_okundu:
        raise ValueError("Önce kaynakları ve uyarıları inceleyip kutuyu işaretleyin.")
    if not isinstance(gerekce, str) or not 10 <= len(gerekce.strip()) <= 1500:
        raise ValueError("Gerekçe 10–1500 karakter olmalıdır.")
    if obvious_injection(gerekce):
        raise ValueError("Gerekçeyi yalnız inceleme açıklaması olarak yazın.")
    return InsanIncelemesi(
        paket_ozeti=paket_ozeti(paket),
        sonuc=sonuc,
        gerekce=mask_pii(gerekce.strip()),
        kaynak_kimlikleri=tuple(s.parca.chunk_id for s in paket.kaynaklar),
        zaman_utc=datetime.now(UTC).isoformat(),
    )


def rapor_json(paket: IncelemePaketi, inceleme: InsanIncelemesi) -> str:
    if inceleme.paket_ozeti != paket_ozeti(paket):
        raise ValueError("İnceleme kaydı bu başvuruya ait değil.")
    # Ham şikâyet, serbest metin gerekçe, kişi adı ve hesap bilgisi dışa aktarılmaz.
    # Maskeleme tüm kişisel veri türlerini kapsamadığından bunlar rapora eklenmez.
    return json.dumps(
        {
            "surum": "uye3-demo-1",
            "uyari": "Kimliği doğrulanmamış sentetik demo; hukuki karar ve ödeme talimatı değildir.",
            "siparis_no": paket.siparis.siparis_no,
            "inceleme": inceleme.model_dump(exclude={"gerekce"}),
            "kaynaklar": [s.parca.chunk_id for s in paket.kaynaklar],
            "uyarilar": list(paket.uyarilar),
        },
        ensure_ascii=False,
        indent=2,
    )
