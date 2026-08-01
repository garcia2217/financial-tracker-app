"""Tests for the Telegram transaction handler's wallet routing (no DB, no network).

The original bug was that this handler took whichever wallet came back first and
invented a "Cash" wallet for users who had none. These pin the behaviour that
replaced it: money is only ever recorded against a wallet the resolution names,
and nothing is created as a side effect of an ambiguous message.
"""
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.wallet import Wallet
from app.routers.telegram import _handle_transaction

CHAT_ID = 42
USER_ID = uuid4()


def make_wallet(name: str, is_default: bool = False) -> Wallet:
    return Wallet(
        id=uuid4(),
        user_id=USER_ID,
        name=name,
        balance=Decimal("1000"),
        is_default=is_default,
    )


class FakeGemini:
    def __init__(self, mention: str | None):
        self.extraction = {
            "amount": Decimal("50000"),
            "type": "expense",
            "category": "Dining Out",
            "description": "lunch",
            "wallet_mention": mention,
        }

    async def parse_transaction_text(self, text, wallet_names):
        self.wallet_names = wallet_names
        return self.extraction


class FakeWalletService:
    def __init__(self, wallets):
        self.wallets = wallets
        self.created = []

    async def get_user_wallets(self, user_id):
        return self.wallets

    async def get_wallet(self, wallet_id):
        return next(wallet for wallet in self.wallets if wallet.id == wallet_id)

    async def create_wallet(self, wallet_in):
        self.created.append(wallet_in)
        raise AssertionError("the handler must never create a wallet")


class FakeCategoryService:
    def __init__(self):
        self.calls = []

    async def get_or_create_by_name(self, user_id, name, txn_type):
        self.calls.append(name)
        return type("Category", (), {"id": uuid4(), "name": name})()


class FakeTransactionService:
    def __init__(self):
        self.created = []

    async def create_transaction(self, txn_create):
        self.created.append(txn_create)


class FakeTelegram:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text):
        self.messages.append(text)


async def run_handler(wallets, mention, text="lunch 50k"):
    gemini = FakeGemini(mention)
    wallet_service = FakeWalletService(wallets)
    category_service = FakeCategoryService()
    transaction_service = FakeTransactionService()
    telegram = FakeTelegram()

    await _handle_transaction(
        CHAT_ID,
        USER_ID,
        text,
        gemini,
        category_service,
        wallet_service,
        transaction_service,
        telegram,
    )
    return wallet_service, category_service, transaction_service, telegram


@pytest.fixture
def wallets() -> list[Wallet]:
    return [make_wallet("BCA Debit", is_default=True), make_wallet("Cash")]


async def test_mentioned_wallet_receives_the_transaction(wallets):
    _, _, transactions, telegram = await run_handler(wallets, "cash")
    assert transactions.created[0].wallet_id == wallets[1].id
    assert "Recorded" in telegram.messages[0]


async def test_no_mention_uses_the_default(wallets):
    _, _, transactions, _ = await run_handler(wallets, None)
    assert transactions.created[0].wallet_id == wallets[0].id


async def test_wallet_names_are_handed_to_the_model(wallets):
    gemini = FakeGemini(None)
    await _handle_transaction(
        CHAT_ID,
        USER_ID,
        "lunch 50k",
        gemini,
        FakeCategoryService(),
        FakeWalletService(wallets),
        FakeTransactionService(),
        FakeTelegram(),
    )
    assert gemini.wallet_names == ["BCA Debit", "Cash"]


async def test_unknown_mention_records_nothing_and_lists_wallets(wallets):
    _, categories, transactions, telegram = await run_handler(wallets, "Jenius")
    assert transactions.created == []
    reply = telegram.messages[0]
    assert "Jenius" in reply
    assert "BCA Debit" in reply and "Cash" in reply
    # Asking must not leave a category behind for a transaction that never was.
    assert categories.calls == []


async def test_ambiguous_mention_records_nothing_and_names_the_matches():
    wallets = [
        make_wallet("BCA Debit", is_default=True),
        make_wallet("BCA Credit"),
        make_wallet("GoPay"),
    ]
    _, _, transactions, telegram = await run_handler(wallets, "bca")
    assert transactions.created == []
    reply = telegram.messages[0]
    assert "BCA Debit" in reply and "BCA Credit" in reply
    assert "GoPay" not in reply


async def test_user_without_wallets_gets_asked_to_create_one():
    wallet_service, _, transactions, telegram = await run_handler([], None)
    assert transactions.created == []
    assert wallet_service.created == []
    assert "create" in telegram.messages[0].lower()


async def test_extraction_error_is_reported_and_records_nothing(wallets):
    gemini = FakeGemini(None)
    gemini.extraction = {"error": "Not a transaction."}
    transactions = FakeTransactionService()
    telegram = FakeTelegram()

    await _handle_transaction(
        CHAT_ID,
        USER_ID,
        "hello",
        gemini,
        FakeCategoryService(),
        FakeWalletService(wallets),
        transactions,
        telegram,
    )
    assert transactions.created == []
    assert "Not a transaction." in telegram.messages[0]
