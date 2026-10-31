"""Üye 2 yapılandırması: ortam değişkenleri, sınırlar ve açık tarife kaydı."""

import os
from collections.abc import Mapping

from dotenv import dotenv_values
from pydantic import SecretStr, ValidationError

from src.agent import AgentLimits
from src.costs import PriceCard
from src.evren import ProviderSettings
from src.paths import ROOT


class ConfigurationError(ValueError):
    """Yapılandırma değerlerini ve anahtarı göstermeyen hata."""


def load_configuration(
    values: Mapping[str, str] | None = None,
) -> tuple[ProviderSettings, AgentLimits, PriceCard | None]:
    """Açık değerleri veya .env + işletim ortamını oku; API isteği yapma.

    Ortam değişkenleri .env'i ezer. Fiyat alanları boşsa None dönülür ve ajan
    model çağrısından önce TARIFE_YOK ile durur. Test tarifesi burada kabul edilmez.
    """
    env = dict(values) if values is not None else {**dotenv_values(ROOT / ".env"), **os.environ}
    try:
        key = env.get("LLM_API_KEY")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Anahtar eksik")
        defaults = ProviderSettings.model_fields
        settings = ProviderSettings(
            api_key=SecretStr(key),
            base_url=env.get("LLM_BASE_URL") or defaults["base_url"].default,
            model=env.get("LLM_MODEL") or defaults["model"].default,
            embedding_model=env.get("EMBEDDING_MODEL") or defaults["embedding_model"].default,
            timeout_seconds=env.get("LLM_TIMEOUT_SECONDS") or 60,
            max_tokens=env.get("LLM_MAX_TOKENS") or 1200,
        )
        limits = AgentLimits(
            max_steps=int(env.get("AGENT_MAX_STEPS") or 6),
            max_model_calls=int(env.get("AGENT_MAX_MODEL_CALLS") or 2),
            max_tool_calls=int(env.get("AGENT_MAX_TOOL_CALLS") or 4),
            max_usd=env.get("AGENT_MAX_USD") or "0.015",
            max_seconds=env.get("AGENT_MAX_SECONDS") or 90,
        )
        price_keys = (
            "PRICE_INPUT_USD_PER_MILLION",
            "PRICE_OUTPUT_USD_PER_MILLION",
            "PRICE_CHECKED_ON",
            "PRICE_SOURCE",
            "PRICE_KIND",
        )
        if not any(env.get(key) for key in price_keys):
            return settings, limits, None
        if not all(env.get(key) for key in price_keys) or env["PRICE_KIND"] == "test_fixture":
            raise ValueError("Tarife alanları eksik veya test tarifesi")
        price = PriceCard(
            base_url=settings.base_url,
            model=settings.model,
            input_usd_per_million=env["PRICE_INPUT_USD_PER_MILLION"],
            output_usd_per_million=env["PRICE_OUTPUT_USD_PER_MILLION"],
            checked_on=env["PRICE_CHECKED_ON"],
            source=env["PRICE_SOURCE"],
            kind=env["PRICE_KIND"],
        )
        return settings, limits, price
    except (ValueError, TypeError, ValidationError):
        raise ConfigurationError("Model, bütçe veya tarife yapılandırması geçersiz/eksik") from None
