"""Tam Üye 2 iş akışını gerçek sağlayıcıya bağlanmadan göster ve kanıt üret."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
from pydantic import SecretStr

from src.agent import AgentLimits, ButceliAjan
from src.costs import PriceCard
from src.evren import ProviderSettings
from src.llm_client import LLMClient


def main():
    """Yerel araç/RAG gerçek; model HTTP yanıtları kontrollü taklittir."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    settings = ProviderSettings(
        api_key=SecretStr("not-a-real-credential"),
        base_url="https://offline.invalid/v1",
        model="demo-model",
    )
    price = PriceCard(
        base_url=settings.base_url,
        model=settings.model,
        input_usd_per_million="1",
        output_usd_per_million="2",
        checked_on=date(2026, 10, 31),
        source="Ağsız simülasyon tarifesi; gerçek sağlayıcı fiyatı değildir",
        kind="test_fixture",
    )
    scenarios = (
        ("normal", {}, True, "TASLAK_DOGRULANDI"),
        ("butce", {"max_usd": "0"}, True, "BUTCE_SINIRI"),
        ("adim", {"max_steps": 4}, True, "ADIM_SINIRI"),
        ("kullanim_yok", {}, False, "KULLANIM_BILINMIYOR"),
    )
    rows = []
    for name, limits, include_usage, expected in scenarios:

        def handler(request, include_usage=include_usage):
            payload = json.loads(json.loads(request.content)["messages"][1]["content"])
            draft = {
                "sorgu_ozeti": "Sentetik başvuru için ağsız üye 2 gösterimi.",
                "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
                "gerekce": "Bu elle oluşturulmuş model taklididir; uzman incelemesi gereklidir.",
                "kaynaklar": payload["kaynaklar"][:1],
                "hesaplanan_iade_tutari_tl": None,
                "insan_onayi_gerekiyor_mu": True,
            }
            result = {
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(draft)}}]
            }
            if include_usage:
                result["usage"] = {"prompt_tokens": 100, "completion_tokens": 50}
            return httpx.Response(200, json=result)

        with LLMClient(settings, transport=httpx.MockTransport(handler)) as client:
            report = ButceliAjan(client, price, limits=AgentLimits(**limits)).run(
                "SIP-2026-1001",
                "Gömlekte cayma hakkını kullanmak ve iade etmek istiyorum.",
                "2026-10-31",
                sentetik=True,
            )
        if report.reason != expected:
            raise RuntimeError("Demo beklenen durma nedenini üretmedi")
        row = report.model_dump(mode="json", exclude={"draft"})
        rows.append({"senaryo": name, "beklenen": expected, **row})
    result = {
        "tarih_utc": datetime.now(UTC).isoformat(),
        "mod": "AG_SIZ_SAHTE_MODEL_GERCEK_YEREL_BILESENLER",
        "uyari": "Gerçek model doğruluğu, gerçek token tüketimi veya sağlayıcı fiyatı ölçülmedi",
        "n": len(rows),
        "senaryolar": rows,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
