"""Unit tests for the Gemini extraction contract (no network).

The model is stubbed, so these cover what the service does with what it gets
back. Extraction reports the user's wording and validates the rest; deciding
which wallet that wording means belongs to resolve_wallet, which is why a
mention we do not recognise is passed on here rather than dropped.
"""
import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.gemini import GeminiService

WALLET_NAMES = ["BCA Debit", "Cash"]

VALID_EXTRACTION = {
    "amount": 50000,
    "type": "expense",
    "category": "Dining Out",
    "description": "lunch",
    "wallet_mention": "bca",
}


def gemini_returning(raw: str):
    """A GeminiService whose model replies with `raw`, recording what it was sent."""
    sent = {}

    async def generate_content(*, model, contents, config):
        sent["contents"] = contents
        return SimpleNamespace(text=raw)

    service = GeminiService.__new__(GeminiService)
    service.system_instructions = "stub"
    service.client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    )
    return service, sent


def gemini_returning_json(payload: dict):
    return gemini_returning(json.dumps(payload))


async def test_wallet_names_are_sent_with_the_message():
    service, sent = gemini_returning_json(VALID_EXTRACTION)
    await service.parse_transaction_text("lunch 50k pakai BCA", WALLET_NAMES)
    assert json.dumps(WALLET_NAMES) in sent["contents"]
    assert "lunch 50k pakai BCA" in sent["contents"]


async def test_mention_is_reported_in_the_users_own_words():
    service, _ = gemini_returning_json(VALID_EXTRACTION)
    result = await service.parse_transaction_text("lunch 50k pakai bca", WALLET_NAMES)
    assert result["wallet_mention"] == "bca"
    assert result["amount"] == Decimal("50000")


async def test_unrecognised_mention_is_passed_on_not_dropped():
    # The whole point of option B: "Jenius" has to reach the resolver, or a
    # message naming an unknown wallet is indistinguishable from one naming none
    # and lands silently in the default.
    service, _ = gemini_returning_json({**VALID_EXTRACTION, "wallet_mention": "Jenius"})
    result = await service.parse_transaction_text("lunch 50k pakai Jenius", WALLET_NAMES)
    assert result["wallet_mention"] == "Jenius"


async def test_casing_is_preserved_for_the_resolver_to_fold():
    service, _ = gemini_returning_json({**VALID_EXTRACTION, "wallet_mention": "BcA dEbIt"})
    result = await service.parse_transaction_text("lunch 50k", WALLET_NAMES)
    assert result["wallet_mention"] == "BcA dEbIt"


async def test_omitted_mention_is_no_mention():
    payload = {
        key: value for key, value in VALID_EXTRACTION.items() if key != "wallet_mention"
    }
    service, _ = gemini_returning_json(payload)
    result = await service.parse_transaction_text("lunch 50k", WALLET_NAMES)
    assert result["wallet_mention"] is None


async def test_user_with_no_wallets_sends_an_empty_list():
    service, sent = gemini_returning_json({**VALID_EXTRACTION, "wallet_mention": None})
    result = await service.parse_transaction_text("lunch 50k", [])
    assert "Available wallets: []" in sent["contents"]
    assert result["wallet_mention"] is None


async def test_markdown_fenced_response_is_still_parsed():
    service, _ = gemini_returning(f"```json\n{json.dumps(VALID_EXTRACTION)}\n```")
    result = await service.parse_transaction_text("lunch 50k", WALLET_NAMES)
    assert result["wallet_mention"] == "bca"


async def test_invented_key_is_rejected():
    service, _ = gemini_returning_json({**VALID_EXTRACTION, "wallet_id": "abc"})
    result = await service.parse_transaction_text("lunch 50k", WALLET_NAMES)
    assert "error" in result


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID_EXTRACTION, "amount": 0},
        {**VALID_EXTRACTION, "type": "transfer"},
        {**VALID_EXTRACTION, "description": ""},
        {**VALID_EXTRACTION, "wallet_mention": "x" * 101},
    ],
)
async def test_invalid_extraction_is_reported_as_an_error(payload):
    service, _ = gemini_returning_json(payload)
    result = await service.parse_transaction_text("lunch 50k", WALLET_NAMES)
    assert "error" in result


async def test_non_json_response_is_reported_as_an_error():
    service, _ = gemini_returning("I'm afraid I can't do that")
    result = await service.parse_transaction_text("lunch 50k", WALLET_NAMES)
    assert "error" in result


async def test_model_reported_error_passes_through():
    service, _ = gemini_returning_json({"error": "Not a transaction."})
    result = await service.parse_transaction_text("hello", WALLET_NAMES)
    assert result == {"error": "Not a transaction."}
