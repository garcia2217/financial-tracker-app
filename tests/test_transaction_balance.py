"""Unit tests for the pure balance-delta logic in the transaction service.

These cover the money math only (no DB). The row-locking/atomicity in
_apply_deltas requires a real Postgres and is left for integration tests.
"""
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.exceptions import AppDomainError
from app.services.transaction import (
    merge_deltas,
    negate_effect,
    transaction_effect,
)

WALLET_A = uuid4()
WALLET_B = uuid4()
WALLET_C = uuid4()


def test_expense_debits_source():
    assert transaction_effect("expense", WALLET_A, None, Decimal("100.00")) == {
        WALLET_A: Decimal("-100.00")
    }


def test_income_credits_source():
    assert transaction_effect("income", WALLET_A, None, Decimal("100.00")) == {
        WALLET_A: Decimal("100.00")
    }


def test_transfer_debits_source_and_credits_destination():
    assert transaction_effect("transfer", WALLET_A, WALLET_B, Decimal("40.00")) == {
        WALLET_A: Decimal("-40.00"),
        WALLET_B: Decimal("40.00"),
    }


def test_transfer_without_destination_raises():
    with pytest.raises(AppDomainError):
        transaction_effect("transfer", WALLET_A, None, Decimal("40.00"))


def test_invalid_type_raises():
    with pytest.raises(AppDomainError):
        transaction_effect("withdrawal", WALLET_A, None, Decimal("10.00"))


def test_negate_reverses_signs():
    effect = {WALLET_A: Decimal("-100.00"), WALLET_B: Decimal("100.00")}
    assert negate_effect(effect) == {
        WALLET_A: Decimal("100.00"),
        WALLET_B: Decimal("-100.00"),
    }


def test_merge_sums_per_wallet():
    a = {WALLET_A: Decimal("100.00")}
    b = {WALLET_A: Decimal("100.00")}
    assert merge_deltas(a, b) == {WALLET_A: Decimal("200.00")}


def test_merge_drops_zero_net_deltas():
    # Reversing then re-applying the same expense is a no-op on the wallet.
    old = negate_effect(transaction_effect("expense", WALLET_A, None, Decimal("50.00")))
    new = transaction_effect("expense", WALLET_A, None, Decimal("50.00"))
    assert merge_deltas(old, new) == {}


def test_update_changing_transfer_destination():
    # Old: A -> B 100.  New: A -> C 100.  A nets to zero and drops out.
    old = negate_effect(
        transaction_effect("transfer", WALLET_A, WALLET_B, Decimal("100.00"))
    )
    new = transaction_effect("transfer", WALLET_A, WALLET_C, Decimal("100.00"))
    assert merge_deltas(old, new) == {
        WALLET_B: Decimal("-100.00"),
        WALLET_C: Decimal("100.00"),
    }


def test_decimal_arithmetic_is_exact():
    # Three 0.10 debits sum to exactly -0.30 (float would give -0.30000000000000004).
    effects = [
        transaction_effect("expense", WALLET_A, None, Decimal("0.10")) for _ in range(3)
    ]
    assert merge_deltas(*effects) == {WALLET_A: Decimal("-0.30")}
