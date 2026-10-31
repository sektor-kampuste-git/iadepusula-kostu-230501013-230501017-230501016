"""Üye 1 kanıt paketini kullanan, bütçeli ve sınırlı ön inceleme iş akışı.

Araç sırası deterministiktir; model serbest araç çalıştıramaz. Yerel BM25 yolu
kullanılır, dolayısıyla gizli gömme API çağrıları bütçe dışında kalmaz. USD sınırı
tarife ve ihtiyatlı token rezervasyonuna dayalıdır; sağlayıcı tarafı fatura limiti
değildir. Her çalıştırma kendi sayaçlarını oluşturur.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from time import monotonic
from typing import Literal
from uuid import uuid4

from pydantic import Field, StrictInt, field_validator

from src.contracts import Contract
from src.costs import BudgetExceeded, PriceCard, RequestBudget, TokenUsage, money, request_cost
from src.evidence import hazirla_inceleme
from src.llm_client import LLMClient, LLMError
from src.rag import MevzuatRetriever
from src.schemas import KararTaslagi, TaslakDogrulamaHatasi, dogrula_karar_taslagi
from src.security import ALLOWED_TOOLS, blocked_submission, draft_messages, prepare_submission

StopReason = Literal[
    "TASLAK_DOGRULANDI",
    "GIRDI_HATASI",
    "GIRDI_ENGELLENDI",
    "SIPARIS_BULUNAMADI",
    "KAYNAK_YOK",
    "SENTETIK_ONAY_GEREKLI",
    "ADIM_SINIRI",
    "BUTCE_SINIRI",
    "SURE_SINIRI",
    "TARIFE_YOK",
    "SAGLAYICI_HATASI",
    "KULLANIM_BILINMIYOR",
    "GECERSIZ_TASLAK",
]


class AgentLimits(Contract):
    """Dört yerel bileşen + en fazla iki model denemesi; bütün sayılar sınırlıdır."""

    max_steps: StrictInt = Field(default=6, ge=1, le=12)
    max_model_calls: StrictInt = Field(default=2, ge=1, le=3)
    max_tool_calls: StrictInt = Field(default=4, ge=1, le=4)
    max_usd: Decimal = Decimal("0.015")
    max_seconds: float = Field(default=90, gt=0, le=180)
    max_input_estimate: StrictInt = Field(default=30000, ge=1, le=60000)

    @field_validator("max_usd", mode="before")
    @classmethod
    def valid_money(cls, value):
        return money(value)


class TraceEvent(Contract):
    """İzinli olay alanları; başvuru, model metni, kaynak alıntısı veya anahtar yok."""

    event: Literal[
        "KANIT_HAZIRLANDI", "MODEL_DENEMESI", "MODEL_HATASI", "TASLAK_REDDEDILDI", "BITIS"
    ]
    attempt: int = Field(ge=0)
    tools: int = Field(ge=0, le=4)


class RunReport(Contract):
    """Arayüz/eval için doğrulanmış taslak ve ayrı güvenli çalışma özeti."""

    request_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    reason: StopReason
    draft: KararTaslagi | None
    model_calls: int = Field(ge=0)
    tool_calls: int = Field(ge=0, le=4)
    accounted_usd: Decimal = Field(ge=0)
    known_usage_usd: Decimal = Field(ge=0)
    cost_contains_reservation: bool
    elapsed_ms: float = Field(ge=0)
    events: tuple[TraceEvent, ...]
    insan_onayi_gerekiyor_mu: Literal[True] = True


def prompt_token_estimate(messages: list[dict[str, str]]) -> int:
    """UTF-8 baytları ve şablon payı; tokenizer ölçümü veya kesin üst sınır değildir."""
    return sum(len(row["content"].encode("utf-8")) + 64 for row in messages) + 256


@dataclass
class _RunState:
    """Yalnız bir isteğe ait değişebilir sayaçlar; ajan nesnesinde paylaşılmaz."""

    ledger: RequestBudget
    started: float
    clock: Callable[[], float] = field(repr=False)
    request_id: str = field(default_factory=lambda: uuid4().hex)
    attempts: int = 0
    tools: int = 0
    events: list[TraceEvent] = field(default_factory=list)

    def finish(self, reason: StopReason, draft: KararTaslagi | None = None) -> RunReport:
        return RunReport(
            request_id=self.request_id,
            reason=reason,
            draft=draft,
            model_calls=self.attempts,
            tool_calls=self.tools,
            accounted_usd=self.ledger.used_usd,
            known_usage_usd=self.ledger.known_usage_usd,
            cost_contains_reservation=self.ledger.estimated,
            elapsed_ms=round((self.clock() - self.started) * 1000, 3),
            events=(
                *self.events,
                TraceEvent(event="BITIS", attempt=self.attempts, tools=self.tools),
            ),
        )


class ButceliAjan:
    """İstemci enjekte edilir; içe aktarma/oluşturma anında ağ isteği yoktur."""

    def __init__(
        self,
        client: LLMClient,
        price: PriceCard | None,
        *,
        limits: AgentLimits | None = None,
        clock: Callable[[], float] | None = None,
    ):
        if price is not None and (
            price.base_url.rstrip("/") != client.settings.base_url.rstrip("/")
            or price.model != client.settings.model
        ):
            raise ValueError("Tarife sağlayıcı adresi ve modelle eşleşmelidir")
        if price is not None and price.kind == "test_fixture" and not client.offline_transport:
            raise ValueError("Test tarifesi gerçek ağ istemcisiyle kullanılamaz")
        self.client = client
        self.price = price
        self.limits = limits or AgentLimits()
        self._clock = clock or monotonic

    def run(
        self,
        siparis_no: str,
        basvuru: str,
        basvuru_tarihi: date | str,
        *,
        sentetik: bool = False,
    ) -> RunReport:
        """Sentetik sipariş/başvuruyu işle; her çıkışta bütçe ve durma nedeni dön."""
        state = _RunState(RequestBudget(self.limits.max_usd), self._clock(), self._clock)
        finish = state.finish

        if sentetik is not True:
            return finish("SENTETIK_ONAY_GEREKLI")
        try:
            safe = prepare_submission(basvuru)
        except ValueError:
            return finish("GIRDI_HATASI")
        if blocked_submission(safe):
            return finish("GIRDI_ENGELLENDI")
        # Üye 1 birleştiricisi en fazla dört yerel araç çağırır; önce tüm yuvaları ayır.
        if self.limits.max_tool_calls < 4 or self.limits.max_steps < 4:
            return finish("ADIM_SINIRI")
        with_retriever = MevzuatRetriever()  # Yerel arama; gömme sağlayıcısı yok.
        try:
            try:
                packet = hazirla_inceleme(
                    siparis_no, safe, basvuru_tarihi, retriever=with_retriever
                )
            except ValueError:
                return finish("GIRDI_HATASI")
            state.tools = len(packet.arac_izleri)
            if state.tools > 4 or any(row.arac not in ALLOWED_TOOLS for row in packet.arac_izleri):
                return finish("GIRDI_ENGELLENDI")
            state.events.append(TraceEvent(event="KANIT_HAZIRLANDI", attempt=0, tools=state.tools))
            if packet.siparis is None:
                return finish("SIPARIS_BULUNAMADI")
            if not packet.kaynaklar:
                return finish("KAYNAK_YOK")
            if self.price is None:
                return finish("TARIFE_YOK")
            return self._generate(packet, with_retriever, state)
        finally:
            with_retriever.close()

    def _generate(self, packet, retriever, state: _RunState):
        """Retry dahil her denemeyi adım ve maliyet hesabına kat."""
        messages = draft_messages(packet, retriever)
        ledger = state.ledger
        done = state.finish
        last_reason = "GECERSIZ_TASLAK"
        for _ in range(self.limits.max_model_calls):
            remaining_seconds = self.limits.max_seconds - (self._clock() - state.started)
            if remaining_seconds <= 0:
                return done("SURE_SINIRI")
            if state.tools + state.attempts >= self.limits.max_steps:
                return done("ADIM_SINIRI")
            estimated_tokens = prompt_token_estimate(messages)
            if estimated_tokens > self.limits.max_input_estimate:
                return done("ADIM_SINIRI")
            reserved = request_cost(
                TokenUsage(
                    prompt_tokens=estimated_tokens,
                    completion_tokens=self.client.settings.max_tokens,
                ),
                self.price,
            )
            try:
                ledger.reserve(reserved)
            except BudgetExceeded:
                return done("BUTCE_SINIRI")
            state.attempts += 1
            state.events.append(
                TraceEvent(event="MODEL_DENEMESI", attempt=state.attempts, tools=state.tools)
            )
            try:
                completion = self.client.complete(messages, timeout_seconds=remaining_seconds)
            except LLMError as error:
                ledger.settle(request_cost(error.usage, self.price) if error.usage else None)
                state.events.append(
                    TraceEvent(event="MODEL_HATASI", attempt=state.attempts, tools=state.tools)
                )
                if ledger.used_usd > ledger.limit_usd:
                    return done("BUTCE_SINIRI")
                if error.usage is None:
                    return done("SAGLAYICI_HATASI")
                if not error.retryable:
                    return done("SAGLAYICI_HATASI")
                last_reason = "SAGLAYICI_HATASI"
                continue
            ledger.settle(request_cost(completion.usage, self.price) if completion.usage else None)
            if completion.usage is None:
                return done("KULLANIM_BILINMIYOR")
            if ledger.used_usd > ledger.limit_usd:
                return done("BUTCE_SINIRI")
            if self._clock() - state.started >= self.limits.max_seconds:
                return done("SURE_SINIRI")
            try:
                draft = dogrula_karar_taslagi(completion.draft, packet, retriever=retriever)
            except TaslakDogrulamaHatasi:
                state.events.append(
                    TraceEvent(event="TASLAK_REDDEDILDI", attempt=state.attempts, tools=state.tools)
                )
                last_reason = "GECERSIZ_TASLAK"
                # Ham hata/önceki yanıt modele veya izlere geri gönderilmez.
                continue
            return done("TASLAK_DOGRULANDI", draft)
        return done(last_reason)


def make_eval_predictor(agent: ButceliAjan):
    """Mevcut label-free eval girişine açıkça bağla; oluşturmak API çağırmaz.

    Dönen işlev çalıştırılırsa enjekte edilen istemciyi kullanır. Gerçek model
    değerlendirmesi bu yüzden ayrıca ve bilinçli olarak başlatılmalıdır.
    """

    def predictor(value):
        report = agent.run(value.siparis_no, value.basvuru, value.basvuru_tarihi, sentetik=True)
        if report.draft is None:
            # Hata/eksik kanıt hiçbir zaman otomatik ret veya kabul değildir.
            return {
                "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
                "kaynaklar": [],
                "insan_onayi_gerekiyor_mu": True,
            }
        return report.draft.eval_ciktisi()

    return predictor
