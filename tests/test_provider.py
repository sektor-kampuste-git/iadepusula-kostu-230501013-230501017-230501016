import json

import httpx
import pytest
from pydantic import SecretStr

from src.evren import EvrenAdapter, ProviderError, ProviderSettings

FAKE_KEY = "test-credential-never-valid"


def settings(**kwargs):
    return ProviderSettings(api_key=SecretStr(FAKE_KEY), **kwargs)


def test_configurable_url_and_embedding_masking_with_shuffled_indices():
    calls = []

    def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert "12345678901" not in body["input"][0]
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0, 1]},
                    {"index": 0, "embedding": [1, 0]},
                ]
            },
        )

    with EvrenAdapter(
        settings(base_url="https://example.invalid/custom/v1"),
        transport=httpx.MockTransport(handler),
    ) as adapter:
        result = adapter.embed(["TCKN 12345678901 iade", "cayma hakkı"], query=True)
    assert result == [[1.0, 0.0], [0.0, 1.0]]
    assert str(calls[0].url) == "https://example.invalid/custom/v1/embeddings"
    assert FAKE_KEY not in repr(settings())


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500])
def test_http_error_never_exposes_provider_body_or_credentials(status):
    def handler(request):
        return httpx.Response(status, text=f"internal details {FAKE_KEY}")

    with EvrenAdapter(settings(), transport=httpx.MockTransport(handler)) as adapter:
        with pytest.raises(ProviderError) as caught:
            adapter.models()
    assert str(status) in str(caught.value)
    assert FAKE_KEY not in str(caught.value)


@pytest.mark.parametrize(
    "bad",
    [
        {"data": []},
        {"data": [{"index": 0, "embedding": []}]},
        {"data": [{"index": 1, "embedding": [1]}]},
        {"data": [{"index": 0, "embedding": ["NaN"]}]},
    ],
)
def test_malformed_embeddings_fail_closed(bad):
    with EvrenAdapter(
        settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=bad))
    ) as adapter:
        with pytest.raises(ProviderError):
            adapter.embed(["cayma"])


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.invalid/v1",
        "https://name:pass@example.invalid",
        "https://example.invalid/v1?api_key=x",
    ],
)
def test_insecure_or_credential_bearing_urls_rejected(url):
    with pytest.raises(ProviderError):
        EvrenAdapter(settings(base_url=url))


def test_timeout_and_non_json_are_safe_errors():
    def timeout(request):
        raise httpx.ReadTimeout(FAKE_KEY, request=request)

    with EvrenAdapter(settings(), transport=httpx.MockTransport(timeout)) as adapter:
        with pytest.raises(ProviderError) as caught:
            adapter.models()
        assert FAKE_KEY not in str(caught.value)
    with EvrenAdapter(
        settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="<html>oops</html>")),
    ) as adapter:
        with pytest.raises(ProviderError, match="JSON"):
            adapter.models()


def test_incomplete_completion_is_not_counted_as_success():
    data = {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
    with EvrenAdapter(
        settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data))
    ) as adapter:
        with pytest.raises(ProviderError, match="tamamlanmış"):
            adapter.synthetic_completion([])
