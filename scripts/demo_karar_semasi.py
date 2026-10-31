"""Üye 2 şemasını sentetik ve elle oluşturulan taslaklarla göster; API çağrısı yapmaz."""

import json
import sys
from datetime import date

from src.evidence import hazirla_inceleme
from src.rag import MevzuatRetriever
from src.schemas import TaslakDogrulamaHatasi, dogrula_karar_taslagi


def main():
    """Geçerli ön inceleme ile üç bozuk taslağın davranışını göster."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rag = MevzuatRetriever()
    try:
        packet = hazirla_inceleme(
            "SIP-2026-1001",
            "Gömlekte cayma hakkını kullanmak ve iade etmek istiyorum.",
            date(2026, 10, 31),
            retriever=rag,
        )
        raw = {
            "sorgu_ozeti": "Sentetik sipariş için iade başvurusu alındı.",
            "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
            "gerekce": "Bu elle oluşturulmuş bir şema demosudur; uzman kaynakları incelemelidir.",
            "kaynaklar": [rag.citation_for(packet.kaynaklar[0].parca.chunk_id).model_dump()],
            "hesaplanan_iade_tutari_tl": None,
            "insan_onayi_gerekiyor_mu": True,
        }
        draft = dogrula_karar_taslagi(raw, packet, retriever=rag)
        print("ŞEMA DEMOSU: sentetik veri, elle oluşturulmuş taslak, API isteği yok.")
        print(json.dumps(draft.model_dump(mode="json"), ensure_ascii=False, indent=2))
        checks = {
            "İnsan incelemesini kapatma": raw | {"insan_onayi_gerekiyor_mu": False},
            "Kaynaksız kabul önerisi": raw | {"karar_onerisi": "KABUL_ONERILIR", "kaynaklar": []},
            "Fatura üstü tutar": raw
            | {"karar_onerisi": "KABUL_ONERILIR", "hesaplanan_iade_tutari_tl": "50000.00"},
        }
        for name, invalid in checks.items():
            try:
                dogrula_karar_taslagi(invalid, packet, retriever=rag)
            except TaslakDogrulamaHatasi as error:
                print(f"ENGELLENDİ - {name}: {error}")
            else:
                raise RuntimeError(f"Beklenen doğrulama çalışmadı: {name}")
        print("Üç bozuk taslak beklendiği gibi engellendi. Bu bir ajan başarı ölçümü değildir.")
    finally:
        rag.close()


if __name__ == "__main__":
    main()
