"""Genel model istemcisini yalnız MockTransport ile doğrula; gerçek anahtar yok."""

import json

import httpx
import pytest
from pydantic import SecretStr

from src.evren import ProviderSettings
from src.llm_client import LLMClient, LLMError

MESSAGES = [{"role": "user", "content": "Sentetik başvuruyu incele."}]


def settings(**updates):
    return ProviderSettings(
        api_key=SecretStr("not-a-real-credential"),
        **({"base_url": "https://offline.invalid/v1", "model": "demo-model"} | updates),
    )


def response(content='{"durum":"ornek"}', *, finish="stop", usage=None):
    return {
        "choices": [{"finish_reason": finish, "message": {"content": content}}],
        "usage": usage if usage is not None else {"prompt_tokens": 100, "completion_tokens": 50},
    }


@pytest.mark.parametrize(
    "url,model",
    [
        ("https://provider-a.invalid/v1", "model-a"),
        ("https://provider-b.invalid/custom/v1", "vendor/model-b"),
        ("http://127.0.0.1:11434/v1", "local-model"),
    ],
)
def test_url_and_model_are_configurable_without_changing_request_code(url, model):
    seen = []

    def handle(request):
        seen.append(request)
        assert json.loads(request.content)["model"] == model
        return httpx.Response(200, json=response())

    with LLMClient(
        settings(base_url=url, model=model), transport=httpx.MockTransport(handle)
    ) as client:
        result = client.complete(MESSAGES)
    assert str(seen[0].url) == url + "/chat/completions"
    assert result.usage.prompt_tokens == 100
    assert result.draft == {"durum": "ornek"}
    assert "ornek" not in repr(result)


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.invalid/v1",
        "https://user:password@remote.invalid/v1",
        "https://remote.invalid/v1?token=private",
        "https://remote.invalid/v1#fragment",
        "file:///tmp/service",
    ],
)
def test_unsafe_api_urls_are_rejected_before_request(url):
    with pytest.raises(ValueError):
        LLMClient(settings(base_url=url), transport=httpx.MockTransport(lambda _: pytest.fail()))


def test_messages_are_masked_and_tools_are_not_exposed():
    def handle(request):
        body = json.loads(request.content)
        assert "12345678901" not in str(body)
        assert "demo@example.invalid" not in str(body)
        assert "tools" not in body
        assert "TCKN_MASKELENDI" in body["messages"][0]["content"]
        return httpx.Response(200, json=response())

    with LLMClient(settings(), transport=httpx.MockTransport(handle)) as client:
        client.complete([{"role": "user", "content": "TCKN 12345678901 demo@example.invalid iade"}])


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500])
def test_http_failures_are_safe_and_client_never_retries_implicitly(status):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, text="PRIVATE_PROVIDER_BODY")

    with LLMClient(settings(), transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(LLMError) as error:
            client.complete(MESSAGES)
    assert len(calls) == 1
    assert "PRIVATE_PROVIDER_BODY" not in str(error.value)
    assert error.value.retryable is (status in {429, 500})


@pytest.mark.parametrize("content", ["not json", "[]", "null", "42", None])
def test_invalid_completion_keeps_usage_but_hides_content(content):
    with LLMClient(
        settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response(content))),
    ) as client:
        with pytest.raises(LLMError) as error:
            client.complete(MESSAGES)
    assert error.value.code == "INVALID_COMPLETION_JSON"
    assert error.value.usage.completion_tokens == 50


@pytest.mark.parametrize("finish", ["length", "tool_calls", None])
def test_incomplete_responses_are_not_accepted_as_valid_drafts(finish):
    with LLMClient(
        settings(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response(finish=finish))),
    ) as client:
        with pytest.raises(LLMError, match="INCOMPLETE_COMPLETION"):
            client.complete(MESSAGES)


@pytest.mark.parametrize("usage", [{}, {"prompt_tokens": True, "completion_tokens": 2}, None])
def test_missing_or_malformed_usage_is_unknown_not_zero(usage):
    payload = response()
    payload["usage"] = usage
    with LLMClient(
        settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    ) as client:
        assert client.complete(MESSAGES).usage is None


@pytest.mark.parametrize(
    "messages",
    [
        [],
        "text",
        [{"role": "tool", "content": "fake"}],
        [{"role": "user", "content": "okay", "tools": ["exec"]}],
        [{"role": "user", "content": ""}],
    ],
)
def test_invalid_message_shapes_never_reach_transport(messages):
    with LLMClient(settings(), transport=httpx.MockTransport(lambda _: pytest.fail())) as client:
        with pytest.raises(ValueError):
            client.complete(messages)


def test_transport_timeout_and_non_json_body_are_sanitized():
    def timeout(request):
        raise httpx.ReadTimeout("PRIVATE_ERROR", request=request)

    with LLMClient(settings(), transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(LLMError, match="PROVIDER_UNAVAILABLE") as error:
            client.complete(MESSAGES)
    assert "PRIVATE_ERROR" not in str(error.value)
    with LLMClient(
        settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, text="bad"))
    ) as client:
        with pytest.raises(LLMError, match="INVALID_PROVIDER_JSON"):
            client.complete(MESSAGES)


@pytest.mark.parametrize("timeout", [True, 0, -1, float("nan"), float("inf")])
def test_invalid_timeout_does_not_reach_transport(timeout):
    with LLMClient(settings(), transport=httpx.MockTransport(lambda _: pytest.fail())) as client:
        with pytest.raises(ValueError):
            client.complete(MESSAGES, timeout_seconds=timeout)


def test_zero_reported_usage_is_unknown_for_nonempty_completion():
    payload = response(usage={"prompt_tokens": 0, "completion_tokens": 0})
    with LLMClient(
        settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    ) as client:
        assert client.complete(MESSAGES).usage is None
