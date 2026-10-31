"""Üye 3: ekranı Üye 1 kanıtına ve Üye 2 ajanına bağlayan sınır."""

import json
from dataclasses import dataclass
from datetime import date
from typing import Literal

import httpx
from pydantic import SecretStr

from src.agent import ButceliAjan, RunReport
from src.case_binding import require_packet_binding
from src.config import ConfigurationError, load_configuration
from src.contracts import IncelemePaketi
from src.costs import PriceCard
from src.evidence import hazirla_inceleme
from src.evren import ProviderSettings
from src.llm_client import LLMClient
from src.rag import MevzuatRetriever
from src.schemas import dogrula_karar_taslagi

Mode = Literal["yerel", "demo", "model"]


@dataclass(frozen=True)
class EkranIncelemesi:
    paket: IncelemePaketi
    rapor: RunReport | None
    mod: Mode


def _demo_response(request: httpx.Request) -> httpx.Response:
    """Ağsız sabit uzman yönlendirmesi; hukuki çıkarım veya model başarısı değildir."""
    data = json.loads(json.loads(request.content)["messages"][1]["content"])
    draft = {
        "sorgu_ozeti": "Sentetik başvurunun ağsız arayüz entegrasyon gösterimi.",
        "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
        "gerekce": "Bu sabit demo yanıtıdır; gerçek hukuki değerlendirme için uzman gerekir.",
        "kaynaklar": data["kaynaklar"][:1],
        "hesaplanan_iade_tutari_tl": None,
        "insan_onayi_gerekiyor_mu": True,
    }
    return httpx.Response(
        200,
        json={
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(draft)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        },
    )


def calistir_inceleme(
    siparis_no: str,
    basvuru: str,
    tarih: date,
    *,
    mod: Mode = "yerel",
    sentetik_onay: bool = False,
    api_onay: bool = False,
) -> EkranIncelemesi:
    if mod not in {"yerel", "demo", "model"}:
        raise ValueError("Geçersiz çalışma modu")
    if mod == "model" and (sentetik_onay is not True or api_onay is not True):
        raise ConfigurationError("Sentetik veri ve API kullanımı açıkça onaylanmalıdır.")
    # Üç katman aynı sunucu paketini kullanır; araçlar ikinci kez çalıştırılmaz.
    retriever = MevzuatRetriever()
    try:
        packet = hazirla_inceleme(siparis_no, basvuru, tarih, retriever=retriever)
        if mod == "yerel":
            return EkranIncelemesi(packet, None, mod)
        if mod == "demo":
            settings = ProviderSettings(
                api_key=SecretStr("not-a-real-credential"),
                base_url="https://offline.invalid/v1",
                model="ui-offline-demo",
            )
            price = PriceCard(
                base_url=settings.base_url,
                model=settings.model,
                input_usd_per_million="1",
                output_usd_per_million="2",
                checked_on=date(2026, 10, 31),
                source="Ağsız arayüz test tarifesi, gerçek fiyat değildir",
                kind="test_fixture",
            )
            client = LLMClient(settings, transport=httpx.MockTransport(_demo_response))
            limits = None
        else:
            settings, limits, price = load_configuration()
            if price is None:
                raise ConfigurationError("Model çağrısından önce tarihli tarife tanımlanmalıdır.")
            client = LLMClient(settings)
        with client:
            report = ButceliAjan(client, price, limits=limits).run_packet(
                packet, retriever=retriever, sentetik=True
            )
        if report.draft is not None:
            require_packet_binding(packet, report.evidence_sha256)
            draft = dogrula_karar_taslagi(report.draft, packet, retriever=retriever)
            report = report.model_copy(update={"draft": draft})
        return EkranIncelemesi(packet, report, mod)
    finally:
        retriever.close()
