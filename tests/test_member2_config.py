import pytest

from src.config import ConfigurationError, load_configuration


def values(**updates):
    return {
        "LLM_API_KEY": "not-a-real-credential",
        "LLM_BASE_URL": "https://provider.invalid/v1",
        "LLM_MODEL": "provider/model",
    } | updates


def test_no_prices_means_unknown_and_secret_is_not_in_settings_repr():
    settings, limits, price = load_configuration(values())
    assert price is None
    assert limits.max_steps == 6
    assert "not-a-real-credential" not in repr(settings)


def test_explicit_source_date_and_provider_are_bound_to_prices():
    settings, limits, price = load_configuration(
        values(
            PRICE_INPUT_USD_PER_MILLION="1",
            PRICE_OUTPUT_USD_PER_MILLION="2",
            PRICE_CHECKED_ON="2026-10-31",
            PRICE_SOURCE="https://provider.invalid/prices",
            PRICE_KIND="provider_published",
            AGENT_MAX_MODEL_CALLS="1",
        )
    )
    assert price.base_url == settings.base_url and price.model == settings.model
    assert limits.max_model_calls == 1


@pytest.mark.parametrize(
    "updates",
    [
        {"LLM_API_KEY": ""},
        {"AGENT_MAX_MODEL_CALLS": "100"},
        {"AGENT_MAX_STEPS": "NaN"},
        {"AGENT_MAX_USD": "-2"},
        {"PRICE_INPUT_USD_PER_MILLION": "1"},
        {"LLM_TIMEOUT_SECONDS": "PRIVATE_BAD_CONFIG"},
    ],
)
def test_invalid_configuration_is_rejected_without_echoing_values(updates):
    with pytest.raises(ConfigurationError) as caught:
        load_configuration(values(**updates))
    assert "PRIVATE_BAD_CONFIG" not in str(caught.value)
    assert "not-a-real-credential" not in str(caught.value)
