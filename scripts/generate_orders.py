"""Seeded Faker tr_TR fixture generation. Never generates identity/contact data."""

import json
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

ROOT = Path(__file__).resolve().parents[1]


def generate():
    fake = Faker("tr_TR")
    fake.seed_instance(20261031)
    products = [
        ("Gömlek", "giyim"),
        ("Kulak üstü kulaklık", "elektronik"),
        ("Cep telefonu", "elektronik"),
        ("Kişiye özel isim baskılı kupa", "kisisel"),
        ("Koruyucu ambalajlı iç çamaşırı", "hijyen"),
        ("Yaş pasta", "gida"),
        ("Bilgisayar", "elektronik"),
        ("Kablosuz fare", "elektronik"),
        ("Kitap", "kitap"),
        ("Dijital yazılım lisansı", "dijital"),
    ]
    rows = []
    for i in range(100):
        product, category = products[i % len(products)]
        delivery = date(2026, 10, 20) - timedelta(days=i % 40)
        rows.append(
            {
                "siparis_no": f"SIP-2026-{1001 + i}",
                "urun_adi": product,
                "kategori": category,
                "siparis_tarihi": (delivery - timedelta(days=3)).isoformat(),
                "teslim_tarihi": delivery.isoformat(),
                "fatura_tutari_tl": f"{fake.random_int(100, 99000)}.{fake.random_int(0, 99):02d}",
                "satis_kanali": "mesafeli",
                "cayma_bilgilendirildi": True,
                "bilgilendirme_tarihi": None,
                "koruyucu_muhur_acildi": False if category == "hijyen" else None,
                "hijyen_niteligi": True if category == "hijyen" else None,
                "kisisellestirilmis": category == "kisisel",
                "cabuk_bozulabilir": category == "gida",
                "dijital_ifa_onayi": True if category == "dijital" else None,
                "kargo_hasar_tutanagi": False,
                "sentetik": True,
            }
        )
    # Stable scenarios for evaluation and demonstrations.
    overrides = {
        0: {"fatura_tutari_tl": "1200.00", "teslim_tarihi": "2026-10-20"},
        1: {
            "fatura_tutari_tl": "2499.90",
            "teslim_tarihi": "2026-10-01",
            "koruyucu_muhur_acildi": True,
        },
        2: {"fatura_tutari_tl": "25000.00", "teslim_tarihi": "2026-10-17"},
        3: {"fatura_tutari_tl": "350.00", "teslim_tarihi": "2026-10-20"},
        4: {
            "fatura_tutari_tl": "500.00",
            "teslim_tarihi": "2026-10-20",
            "koruyucu_muhur_acildi": True,
        },
        10: {"teslim_tarihi": None},
        11: {"cayma_bilgilendirildi": False},
        12: {"satis_kanali": "magaza"},
        13: {"fatura_tutari_tl": "186000.00"},
        14: {"kargo_hasar_tutanagi": True},
        15: {"cayma_bilgilendirildi": None},
    }
    for i, values in overrides.items():
        rows[i].update(values)
        if rows[i]["teslim_tarihi"]:
            rows[i]["siparis_tarihi"] = (
                date.fromisoformat(rows[i]["teslim_tarihi"]) - timedelta(days=3)
            ).isoformat()
    target = ROOT / "data" / "siparisler_sentetik.json"
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(rows)} synthetic orders; no names, IDs, IBANs, phones or emails.")


if __name__ == "__main__":
    generate()
