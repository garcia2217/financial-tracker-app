"""Unit tests for wallet resolution (no DB).

Every branch of the resolution table gets a case, including the ones the schema
invariants are supposed to make unreachable — those are exactly the ones that
would silently mis-attribute money if an invariant ever broke.
"""
from uuid import uuid4

import pytest

from app.models.wallet import Wallet
from app.services.wallet import (
    ChoiceReason,
    NeedsChoice,
    Resolved,
    resolve_wallet,
)


def make_wallet(name: str, is_default: bool = False) -> Wallet:
    return Wallet(id=uuid4(), user_id=uuid4(), name=name, is_default=is_default)


@pytest.fixture
def wallets() -> list[Wallet]:
    return [
        make_wallet("BCA Debit", is_default=True),
        make_wallet("Cash"),
        make_wallet("GoPay"),
    ]


def test_mention_matching_a_wallet_wins_over_the_default(wallets):
    assert resolve_wallet(wallets, "GoPay") == Resolved(wallets[2])


def test_mention_matches_regardless_of_casing(wallets):
    assert resolve_wallet(wallets, "bca debit") == Resolved(wallets[0])


def test_mention_ignores_surrounding_whitespace(wallets):
    assert resolve_wallet(wallets, "  Cash ") == Resolved(wallets[1])


def test_partial_mention_reaches_the_full_name(wallets):
    # "lunch 50k pakai bca" -> the model reports "bca", we do the matching.
    assert resolve_wallet(wallets, "bca") == Resolved(wallets[0])


def test_exact_match_beats_a_longer_partial_match():
    petty = make_wallet("Petty Cash")
    cash = make_wallet("Cash", is_default=True)
    assert resolve_wallet([petty, cash], "Cash") == Resolved(cash)


def test_ambiguous_mention_asks_between_the_matches():
    debit = make_wallet("BCA Debit", is_default=True)
    credit = make_wallet("BCA Credit")
    cash = make_wallet("Cash")
    result = resolve_wallet([debit, credit, cash], "bca")
    assert result == NeedsChoice(
        reason=ChoiceReason.AMBIGUOUS_WALLET, candidates=[debit, credit]
    )


def test_no_mention_falls_back_to_the_default(wallets):
    assert resolve_wallet(wallets, None) == Resolved(wallets[0])


def test_blank_mention_is_treated_as_no_mention(wallets):
    # Nothing to ask about — "I don't know a wallet called ''" helps nobody.
    assert resolve_wallet(wallets, "   ") == Resolved(wallets[0])


def test_single_wallet_needs_no_default():
    only = [make_wallet("Cash")]
    assert resolve_wallet(only, None) == Resolved(only[0])


def test_no_wallets_asks_the_user_to_create_one():
    result = resolve_wallet([], None)
    assert result == NeedsChoice(reason=ChoiceReason.NO_WALLETS)
    assert result.candidates == ()


def test_no_wallets_with_a_mention_still_asks_for_creation():
    assert resolve_wallet([], "BCA Debit") == NeedsChoice(reason=ChoiceReason.NO_WALLETS)


def test_unknown_mention_asks_rather_than_using_the_default(wallets):
    # The user named an account; recording against the default anyway is the
    # mis-attribution this whole resolution exists to prevent.
    result = resolve_wallet(wallets, "Jenius")
    assert result == NeedsChoice(reason=ChoiceReason.UNKNOWN_WALLET, candidates=wallets)


def test_a_mention_can_never_invent_a_wallet(wallets):
    # Whatever the model emits is matched against this user's own rows, so the
    # worst case is a question — never a wallet id we were handed.
    result = resolve_wallet(wallets, "0f9a1c3e-0000-4000-8000-000000000000")
    assert result == NeedsChoice(reason=ChoiceReason.UNKNOWN_WALLET, candidates=wallets)


def test_multiple_wallets_without_a_default_asks(wallets):
    # Unreachable while the one-default-per-user invariant holds; asserted so a
    # broken backfill surfaces as a question, not an arbitrary wallet.
    for wallet in wallets:
        wallet.is_default = False
    assert resolve_wallet(wallets, None) == NeedsChoice(
        reason=ChoiceReason.NO_DEFAULT, candidates=wallets
    )


def test_resolution_is_stable_across_repeated_calls(wallets):
    # Same text twice must land in the same wallet — the original bug was that
    # it did not.
    assert resolve_wallet(wallets, None) == resolve_wallet(wallets, None)
    assert resolve_wallet(wallets, "cash") == resolve_wallet(wallets, "cash")
