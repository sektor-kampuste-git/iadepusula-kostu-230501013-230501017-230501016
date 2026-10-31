from datetime import date
from decimal import Decimal

import pytest

from src.costs import (
    BudgetExceeded,
    PriceCard,
    RequestBudget,
    TokenUsage,
    money,
    monthly_estimate,
    request_cost,
)


def price():
    return PriceCard(
        base_url="https://offline.invalid/v1",
        model="demo-model",
        input_usd_per_million="1",
        output_usd_per_million="2",
        checked_on=date(2026, 10, 31),
        source="Ağsız test tarifesi; gerçek sağlayıcı fiyatı değildir",
        kind="test_fixture",
    )


def test_request_and_monthly_estimate_match_hand_calculation():
    cost = request_cost(TokenUsage(prompt_tokens=2100, completion_tokens=450), price())
    assert cost == Decimal("0.003")
    assert monthly_estimate(cost, 1000, 10) == Decimal("30")


@pytest.mark.parametrize("value", [True, 0.5, "NaN", "Infinity", "-0.1", "not money"])
def test_money_rejects_ambiguous_or_nonfinite_values(value):
    with pytest.raises(ValueError):
        money(value)


@pytest.mark.parametrize("value", [True, "12", 2.5, -1])
def test_token_counts_must_be_nonnegative_actual_integers(value):
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=value, completion_tokens=1)


def test_budget_reserves_before_call_and_settles_actual_usage():
    ledger = RequestBudget(Decimal("0.01"))
    ledger.reserve(Decimal("0.008"))
    ledger.settle(Decimal("0.002"))
    ledger.reserve(Decimal("0.008"))
    ledger.settle(None)
    assert ledger.used_usd == Decimal("0.01")
    assert ledger.known_usage_usd == Decimal("0.002")
    assert ledger.estimated is True
    with pytest.raises(BudgetExceeded):
        ledger.reserve(Decimal("0.001"))


def test_missing_usage_is_not_refunded_and_double_reserve_is_not_allowed():
    ledger = RequestBudget(Decimal("0.01"))
    ledger.reserve(Decimal("0.01"))
    with pytest.raises(RuntimeError):
        ledger.reserve(Decimal("0"))
    ledger.settle(None)
    with pytest.raises(BudgetExceeded):
        ledger.reserve(Decimal("0.001"))
    with pytest.raises(RuntimeError):
        ledger.settle(None)


@pytest.mark.parametrize("users,requests", [(-1, 10), (1000, -1), (True, 10), (1000, 2.5)])
def test_invalid_monthly_assumptions_are_rejected(users, requests):
    with pytest.raises(ValueError):
        monthly_estimate(Decimal("0.001"), users, requests)


def test_published_price_requires_traceable_url():
    raw = price().model_dump() | {"kind": "provider_published", "source": "unknown"}
    with pytest.raises(ValueError):
        PriceCard.model_validate(raw)
