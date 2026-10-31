"""OpenAI uyumlu uç noktalar için Üye 2 JSON istemcisi.

Otomatik ağ çağrısı veya görünmez retry yapmaz. Her complete çağrısı tek HTTP
isteğidir; tekrar/adım/maliyet sınırını src.agent uygular. Sağlayıcı gövdesi ve
anahtarlar hata mesajına veya repr çıktısına konulmaz.
"""

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from src.costs import TokenUsage
from src.evren import ProviderSettings
from src.privacy import mask_pii


class LLMError(RuntimeError):
    """Güvenli hata kodu ve yeniden denenebilirlik; sağlayıcı gövdesi saklanmaz."""

    def __init__(self, code: str, *, retryable: bool = False, usage: TokenUsage | None = None):
        super().__init__(code)
        self.code = code
        self.retryable = retryable
        self.usage = usage


@dataclass(frozen=True)
class Completion:
    """Ham taslak repr'den gizlenir; kayıt katmanına taşınmaz."""

    draft: dict[str, Any] = field(repr=False)
    usage: TokenUsage | None


def _parse_usage(data: dict) -> TokenUsage | None:
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return None
    try:
        parsed = TokenUsage(
            prompt_tokens=usage["prompt_tokens"], completion_tokens=usage["completion_tokens"]
        )
        return parsed if parsed.prompt_tokens + parsed.completion_tokens else None
    except (KeyError, ValidationError):
        return None


class LLMClient:
    """Sağlayıcı ayarlarını mevcut .env sözleşmesinden alan tek istek adaptörü."""

    def __init__(self, settings: ProviderSettings, *, transport: httpx.BaseTransport | None = None):
        url = urlparse(settings.base_url)
        local_http = url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1"}
        if (
            not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or (url.scheme != "https" and not local_http)
        ):
            raise ValueError(
                "API adresi güvenli ve kimlik/sorgu bilgisinden arındırılmış olmalıdır"
            )
        if not settings.api_key.get_secret_value().strip():
            raise ValueError("API anahtarı boş olamaz")
        self.settings = settings
        self.offline_transport = isinstance(transport, httpx.MockTransport)
        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/") + "/",
            headers={"Authorization": "Bearer " + settings.api_key.get_secret_value()},
            timeout=settings.timeout_seconds,
            follow_redirects=False,
            transport=transport,
        )

    def complete(
        self, messages: Sequence[dict[str, str]], *, timeout_seconds: float | None = None
    ) -> Completion:
        """Tek JSON yanıtı üret; eksik kullanım bilinmiyor olarak kalır."""
        if (
            not isinstance(messages, Sequence)
            or isinstance(messages, (str, bytes))
            or not 1 <= len(messages) <= 8
        ):
            raise ValueError("İstek 1–8 mesaj içermelidir")
        safe = []
        for message in messages:
            if (
                not isinstance(message, dict)
                or set(message) != {"role", "content"}
                or message["role"] not in {"system", "user", "assistant"}
                or not isinstance(message["content"], str)
                or not message["content"].strip()
                or len(message["content"]) > 30000
            ):
                raise ValueError("Geçersiz mesaj yapısı")
            safe.append({"role": message["role"], "content": mask_pii(message["content"])})
        timeout = self.settings.timeout_seconds
        if timeout_seconds is not None:
            if (
                type(timeout_seconds) not in (int, float)
                or not math.isfinite(timeout_seconds)
                or timeout_seconds <= 0
            ):
                raise ValueError("Zaman aşımı pozitif olmalıdır")
            timeout = min(timeout, timeout_seconds)
        try:
            response = self._client.post(
                "chat/completions",
                json={
                    "model": self.settings.model,
                    "messages": safe,
                    "temperature": 0,
                    "max_tokens": self.settings.max_tokens,
                    "response_format": {"type": "json_object"},
                },
                timeout=timeout,
            )
        except httpx.HTTPError:
            raise LLMError("PROVIDER_UNAVAILABLE", retryable=True) from None
        if response.status_code != 200:
            raise LLMError(
                "PROVIDER_HTTP_ERROR",
                retryable=response.status_code in {429, 500, 502, 503, 504},
            )
        if len(response.content) > 200000:
            raise LLMError("RESPONSE_TOO_LARGE")
        try:
            data = response.json()
        except ValueError:
            raise LLMError("INVALID_PROVIDER_JSON") from None
        if not isinstance(data, dict):
            raise LLMError("INVALID_PROVIDER_JSON")
        usage = _parse_usage(data)
        try:
            choice = data["choices"][0]
            if choice["finish_reason"] != "stop":
                raise LLMError("INCOMPLETE_COMPLETION", usage=usage)
            content = choice["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Metin gerekli")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("JSON nesnesi gerekli")
        except LLMError:
            raise
        except (KeyError, IndexError, TypeError, ValueError):
            raise LLMError("INVALID_COMPLETION_JSON", retryable=True, usage=usage) from None
        return Completion(draft=parsed, usage=usage)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
