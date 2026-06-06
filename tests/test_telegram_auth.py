import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.dependencies.telegram import verify_telegram_secret

SECRET = "test-secret-value"


@pytest.fixture
def configured_secret(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", SECRET)


async def test_passes_when_secret_matches(configured_secret):
    # Correct header → dependency returns without raising.
    assert await verify_telegram_secret(secret_token=SECRET) is None


async def test_rejects_wrong_secret(configured_secret):
    with pytest.raises(HTTPException) as exc:
        await verify_telegram_secret(secret_token="wrong")
    assert exc.value.status_code == 403


async def test_rejects_missing_header(configured_secret):
    with pytest.raises(HTTPException) as exc:
        await verify_telegram_secret(secret_token=None)
    assert exc.value.status_code == 403


async def test_fails_closed_when_secret_not_configured(monkeypatch):
    # No secret configured → every request is rejected, even with a header.
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
    with pytest.raises(HTTPException) as exc:
        await verify_telegram_secret(secret_token=SECRET)
    assert exc.value.status_code == 403
