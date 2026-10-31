"""Üç üyenin paylaştığı başvuru/kanıt kimliği; imza veya kimlik doğrulama değildir.

İş verileri değişirse özet değişir. Süre ve sıralama skorları iş verisi değildir;
aynı başvurunun yeniden ölçülmesi bir onayı başka bir başvuruya dönüştürmez.
Özet, içeriği anonimleştirme veya kötü niyetli sunucuya karşı koruma sağlamaz.
"""

import hashlib
import hmac
import json
import re

from src.contracts import IncelemePaketi


def evidence_digest(packet: IncelemePaketi) -> str:
    """Başvuru, tarih, sipariş, hesaplar ve kaynakların kararlı SHA-256 özetini üret."""
    data = packet.model_dump(mode="json")
    data["arac_izleri"] = [
        {"arac": row["arac"], "durum": row["durum"]} for row in data["arac_izleri"]
    ]
    for source in data["kaynaklar"]:
        source.pop("skor", None)
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def require_packet_binding(packet: IncelemePaketi, expected: str | None) -> None:
    """Eski/başka başvuruya ait taslak veya onay için kullanıcıya güvenli hata ver."""
    if (
        not isinstance(expected, str)
        or re.fullmatch(r"[a-f0-9]{64}", expected) is None
        or not hmac.compare_digest(evidence_digest(packet), expected)
    ):
        raise ValueError("Taslak bu başvurunun kanıt paketiyle eşleşmiyor.")
