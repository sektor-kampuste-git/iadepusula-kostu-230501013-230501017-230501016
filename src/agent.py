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

from pydantic import Field, StrictInt, field_validator, model_validator

from src.case_binding import evidence_digest
from src.contracts import Contract, IncelemePaketi
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
    evidence_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def successful_report_needs_bound_draft(self):
        """Başarılı taslak başvuruya bağlı olmalı; durdurulan rapor taslak taşıyamaz."""
        if self.reason == "TASLAK_DOGRULANDI":
            if self.draft is None or self.evidence_sha256 is None:
                raise ValueError("Doğrulanmış taslak ve başvuru özeti birlikte gereklidir")
        elif self.draft is not None:
            raise ValueError("Tamamlanmamış rapor onaylanabilir taslak taşıyamaz")
        return self


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
    evidence_sha256: str | None = None

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
            evidence_sha256=self.evidence_sha256,
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
            return self._use_packet(packet, with_retriever, state)
        finally:
            with_retriever.close()

    def run_packet(
        self,
        packet: IncelemePaketi,
        *,
        retriever: MevzuatRetriever | None = None,
        sentetik: bool = False,
    ) -> RunReport:
        """UI/eval'in sunucuda hazırladığı paketi yeniden araç çalıştırmadan kullan.

        Bu bir dış API girişi değildir: paket model/kullanıcıdan alınmamalıdır.
        Çağıran retriever verirse onun yaşam döngüsünü kendisi yönetir.
        """
        state = _RunState(RequestBudget(self.limits.max_usd), self._clock(), self._clock)
        if sentetik is not True:
            return state.finish("SENTETIK_ONAY_GEREKLI")
        try:
            packet = IncelemePaketi.model_validate(packet.model_dump(mode="python"))
            if packet.basvuru_tarihi is None:
                raise ValueError("Başvuru tarihi gerekli")
            # Üye 1 dış boşlukları koruyabilir; kanıtı değiştirmeden yalnız bu
            # biçim farkını kabul et. PII/Unicode güvenlik dönüşümleri hâlâ reddedilir.
            if prepare_submission(packet.maskelenmis_basvuru) != packet.maskelenmis_basvuru.strip():
                raise ValueError("Paket güvenli girdi sınırından geçmemiş")
        except (ValueError, TypeError, AttributeError):
            return state.finish("GIRDI_HATASI")
        if blocked_submission(packet.maskelenmis_basvuru):
            return state.finish("GIRDI_ENGELLENDI")
        owned = retriever is None
        rag = retriever if retriever is not None else MevzuatRetriever()
        try:
            return self._use_packet(packet, rag, state)
        finally:
            if owned:
                rag.close()

    def _use_packet(self, packet, retriever, state):
        """Tek kanıt paketini, kaynak bütünlüğünü ve araç sayısını doğrula."""
        finish = state.finish
        if len(packet.arac_izleri) > 4 or any(
            row.arac not in ALLOWED_TOOLS for row in packet.arac_izleri
        ):
            return finish("GIRDI_ENGELLENDI")
        state.tools = len(packet.arac_izleri)
        state.evidence_sha256 = evidence_digest(packet)
        state.events.append(TraceEvent(event="KANIT_HAZIRLANDI", attempt=0, tools=state.tools))
        if state.tools > self.limits.max_tool_calls or state.tools >= self.limits.max_steps:
            return finish("ADIM_SINIRI")
        if packet.siparis is None:
            return finish("SIPARIS_BULUNAMADI")
        if not packet.kaynaklar:
            return finish("KAYNAK_YOK")
        if any(retriever.by_id.get(row.parca.chunk_id) != row.parca for row in packet.kaynaklar):
            return finish("GIRDI_HATASI")
        if self.price is None:
            return finish("TARIFE_YOK")
        return self._generate(packet, retriever, state)

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


class AgentEvaluationError(RuntimeError):
    """Operasyonel durma, başarılı uzman önerisi değildir; yalnız güvenli kod taşır."""


def make_eval_predictor(agent: ButceliAjan):
    """Mevcut label-free eval girişine açıkça bağla; oluşturmak API çağırmaz.

    Dönen işlev çalıştırılırsa enjekte edilen istemciyi kullanır. Gerçek model
    değerlendirmesi bu yüzden ayrıca ve bilinçli olarak başlatılmalıdır.
    """

    def predictor(value):
        report = agent.run_packet(value.kanit_paketi, sentetik=True)
        if report.draft is None:
            # Beklenen yerel güvenlik/eksik kanıt yönlendirmesini operasyonel
            # hatadan ayır. Tarife, bütçe, sağlayıcı, süre vb. başarı sayılamaz.
            if report.reason not in {
                "GIRDI_ENGELLENDI",
                "SIPARIS_BULUNAMADI",
                "KAYNAK_YOK",
            }:
                raise AgentEvaluationError(report.reason)
            return {
                "karar_onerisi": "UZMAN_INCELEMESI_GEREKLI",
                "kaynaklar": [],
                "insan_onayi_gerekiyor_mu": True,
            }
        return report.draft.eval_ciktisi()

    return predictor


def predict_for_eval(value):
    """Belgelenmiş CLI adaptörü; canlı çağrı için ayrı işletim ortamı onayı gerekir.

    İçe aktarma hiçbir istemci/anahtar yüklemez. Her çağrı kendi istemcisini kapatır.
    Ağsız testler enjekte edilmiş make_eval_predictor istemcisini kullanmalıdır.
    """
    import os

    if os.environ.get("IADEPUSULA_ALLOW_LIVE_EVAL") != "1":
        raise AgentEvaluationError("CANLI_EVAL_ONAYI_GEREKLI")
    from src.config import load_configuration

    settings, limits, price = load_configuration()
    with LLMClient(settings) as client:
        return make_eval_predictor(ButceliAjan(client, price, limits=limits))(value)
