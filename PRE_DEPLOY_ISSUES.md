# Pre-Deploy Issues

## Critical — Fix Before Deploy

### 1. Wallet ownership never checked in transaction creation or update
**Files:** `app/services/transaction.py:52–69`, `:107–123`

The service verifies the wallet exists but never checks `wallet.user_id == transaction_in.user_id`. Any authenticated user who knows or guesses a wallet UUID can create transactions against it and manipulate its balance.

Fix for `create_transaction` — add after fetching the wallet:
```python
if wallet.user_id != transaction_in.user_id:
    raise ResourceNotFoundError(resource="Wallet", id=str(transaction_in.wallet_id))
```

Apply the same check in `update_transaction` when validating the new `wallet_id` and `destination_wallet_id`.

---

### 2. Unconstrained `limit` on `/transactions/recent`
**File:** `app/routers/transactions.py:58`

The `limit` query param is forwarded directly to the DB with no cap. A client can send `limit=10000000` and trigger a massive query.

```python
limit: int = Query(default=10, ge=1, le=100),
```

---

## Important — Fix Soon

### 3. Global in-memory dedup set breaks with multiple workers
**File:** `app/routers/telegram.py:27`

`processed_updates: set[int]` is module-level, so each uvicorn worker has its own copy. Telegram retries go to any worker, meaning duplicates will be processed by different workers. This causes duplicate transactions — the worst possible outcome for a finance app.

Move deduplication to a shared store (Redis, or a short-lived DB table). At minimum, document that you must run single-worker.

---

### 4. `GeminiService` reads from disk on every request
**File:** `app/dependencies/services.py:37`

`get_gemini_service()` calls `GeminiService()` which opens and reads `SYSTEM_INSTRUCTIONS.md` in `_load_instructions()` on every Telegram webhook. Make it a module-level singleton or use `lru_cache`.

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_gemini_service() -> GeminiService:
    return GeminiService()
```

---

### 5. `AppDomainError` global handler uses a different response format
**File:** `app/main.py:119–124`

All other exception handlers use `build_error_response()`, but `AppDomainError` returns `{"detail": str(exc)}` — breaking the API contract. The frontend receives a structurally different error object for this case.

```python
@app.exception_handler(AppDomainError)
async def app_domain_error_handler(request: Request, exc: AppDomainError):
    return JSONResponse(
        status_code=400,
        content=build_error_response(
            message=str(exc),
            code=ApiErrorCode.VALIDATION_ERROR,
            request_id="",
        ),
    )
```

---

### 6. `TelegramBotService` silently swallows all exceptions
**File:** `app/services/telegram_bot.py:19–21`

`except Exception: pass` makes delivery failures completely invisible. Log the error at minimum.

```python
except Exception as e:
    logger.error("Failed to send Telegram message to %s: %s", chat_id, e)
```

---

## Minor — Polish

### 7. `request_id` is always `""` in global exception handlers
**File:** `app/main.py:89, 101, 111`

Every router handler generates `request_id = str(uuid.uuid4())`, but the global exception handlers pass `request_id=""` to `build_error_response()`. This prevents error log correlation. Generate one at the top of each handler.
