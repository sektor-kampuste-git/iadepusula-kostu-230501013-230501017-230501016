"""Tarihli, sağlayıcı/model bazlı tahmini API maliyeti ve istek bütçesi.

Tarife verisi dışarıdan verilir; bilinmeyen fiyat sıfır maliyet sayılmaz.
Rezervasyon tokenizasyon için ihtiyatlı bir tahmindir; sağlayıcı faturasında
uygulanan katı bir harcama limiti veya gerçek fatura tutarı değildir.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import Field, StrictInt, field_validator, model_validator

from src.contracts import Contract


def money(value: Any) -> Decimal:
    """Sonlu ve negatif olmayan Decimal ayrıştır; float/bool kabul etme."""
    if isinstance(value, (bool, float)) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("Maliyet ondalık metin, Decimal veya tam sayı olmalıdır")
    try:
        result = Decimal(value)
    except Exception:
        raise ValueError("Geçersiz maliyet değeri") from None
    if not result.is_finite() or result < 0:
        raise ValueError("Maliyet sonlu ve negatif olmayan bir sayı olmalıdır")
    return result


class TokenUsage(Contract):
    """Sağlayıcının raporladığı token kullanımı; eksik veriyle üretilmez."""

    prompt_tokens: StrictInt = Field(ge=0)
    completion_tokens: StrictInt = Field(ge=0)


class PriceCard(Contract):
    """Bir modelin belirli sağlayıcıdaki fiyat kaynağı ve tarihi."""

    base_url: str = Field(min_length=8, max_length=300)
    model: str = Field(min_length=1, max_length=150)
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal
    checked_on: date
    source: str = Field(min_length=3, max_length=500)
    kind: Literal["provider_published", "user_assumption", "test_fixture"]

    @field_validator("input_usd_per_million", "output_usd_per_million", mode="before")
    @classmethod
    def valid_money(cls, value):
        return money(value)

    @model_validator(mode="after")
    def published_price_needs_source(self):
        if self.kind == "provider_published" and not self.source.startswith("https://"):
            raise ValueError("Yayımlanmış fiyatın HTTPS kaynak bağlantısı gereklidir")
        return self


def request_cost(usage: TokenUsage, price: PriceCard) -> Decimal:
    """Girdi/çıktı token bedelini USD cinsinden yuvarlamadan hesapla."""
    return (
        usage.prompt_tokens * price.input_usd_per_million
        + usage.completion_tokens * price.output_usd_per_million
    ) / Decimal("1000000")


class BudgetExceeded(ValueError):
    """Yeni isteğin tahmini rezervasyonu bütçeye sığmıyor."""


class RequestBudget:
    """Tek çalıştırmaya ait hesap; hatada rezervasyon ihtiyatla tüketilmiş sayılır."""

    def __init__(self, limit_usd: Decimal):
        self.limit_usd = money(limit_usd)
        self.used_usd = Decimal("0")
        self.known_usage_usd = Decimal("0")
        self.estimated = False
        self._pending: Decimal | None = None

    def reserve(self, amount: Decimal):
        """Çağrıdan önce bütçeyi ayır; aynı anda ikinci rezervasyon yapılamaz."""
        amount = money(amount)
        if self._pending is not None:
            raise RuntimeError("Açık rezervasyon önce kapatılmalıdır")
        if self.used_usd + amount > self.limit_usd:
            raise BudgetExceeded("Tahmini istek maliyeti kalan bütçeyi aşıyor")
        self._pending = amount

    def settle(self, actual: Decimal | None):
        """Kullanım bilinmiyorsa rezervasyonu koru; biliniyorsa gerçek token bedelini yaz."""
        if self._pending is None:
            raise RuntimeError("Kapatılacak rezervasyon yok")
        if actual is None:
            self.used_usd += self._pending
            self.estimated = True
        else:
            actual = money(actual)
            self.used_usd += actual
            self.known_usage_usd += actual
        self._pending = None


def monthly_estimate(
    per_request_usd: Decimal, users: int = 1000, requests_per_user: int = 10
) -> Decimal:
    """Açık kullanıcı/istek varsayımıyla yalnız model API maliyetini tahmin et."""
    if type(users) is not int or type(requests_per_user) is not int:
        raise ValueError("Kullanıcı ve istek sayıları tam sayı olmalıdır")
    if users < 0 or requests_per_user < 0:
        raise ValueError("Kullanıcı ve istek sayıları negatif olamaz")
    return money(per_request_usd) * users * requests_per_user
