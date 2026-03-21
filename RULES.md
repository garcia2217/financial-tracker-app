# CLAUDE.md — AI Agent Rules & Constraints

> This file defines the rules, conventions, and boundaries for the AI agent working on this project.
> Read this file completely before writing any code, creating any file, or making any changes.

---

## 🧠 Agent Behavior

### Before Writing Code

1. **Always produce a plan first.** For any non-trivial task, output a brief technical plan (schema, endpoints, edge cases) and wait for approval before implementing.
2. **Ask when uncertain.** If the requirement is ambiguous, ask one focused clarifying question. Do not guess and proceed.
3. **List affected files first.** Before any refactor or multi-file change, list all files you intend to modify and explain why.

### During Implementation

- Implement **one logical unit at a time** (one endpoint, one model, one migration).
- After each unit, summarize what was done and what comes next.
- Never silently skip edge cases — flag them as `# TODO:` with a short explanation.

### Hard Stops (Do NOT proceed — ask first)

- Any change to an existing database migration file
- Deleting or renaming a database column
- Modifying auth/permission logic
- Changing environment variable names or `.env` structure
- Any change that touches more than 5 files at once

---

## 🐍 Python & Project Setup

### Runtime & Package Manager

- **Python version:** 3.14+
- **Package manager:** `uv` exclusively. Never use `pip`, `poetry`, or `conda`.
- Install packages: `uv add <package>`
- Run scripts: `uv run python <script.py>`
- Sync dependencies: `uv sync`

### Project Structure

```
project/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── core/
│   │   ├── config.py        # Settings via pydantic-settings
│   │   └── database.py      # SQLAlchemy engine & session
│   ├── models/              # SQLAlchemy ORM models (one file per domain)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # FastAPI routers (one file per domain)
│   ├── services/            # Business logic layer (no DB calls in routers)
│   ├── repositories/        # Database access layer (all queries live here)
│   └── dependencies/        # FastAPI Depends() functions
├── alembic/                 # Database migrations
├── tests/
├── .env
├── pyproject.toml
└── CLAUDE.md
```

### Naming Conventions

| Entity                | Convention            | Example                      |
| --------------------- | --------------------- | ---------------------------- |
| Files & folders       | `snake_case`          | `user_service.py`            |
| Classes               | `PascalCase`          | `UserService`                |
| Functions & variables | `snake_case`          | `get_current_user`           |
| Constants             | `UPPER_SNAKE_CASE`    | `MAX_RETRY_COUNT`            |
| Pydantic schemas      | `PascalCase` + suffix | `UserCreate`, `UserResponse` |
| ORM models            | `PascalCase`          | `User`, `Order`              |
| Router prefixes       | `kebab-case`          | `/api/v1/user-profiles`      |

---

## ⚡ FastAPI Rules

### Routing

- All routers must be versioned under `/api/v1/`.
- Group routes by domain in separate files under `app/routers/`.
- Use `APIRouter` with `prefix` and `tags`.
- Router functions must be **thin** — delegate all logic to the service layer.

```python
# ✅ Correct
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(payload)

# ❌ Wrong — business logic in router
@router.post("/users")
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    # ... 30 lines of logic
```

### Request & Response Schemas

- Always define separate `Create`, `Update`, and `Response` Pydantic schemas. Never expose ORM models directly.
- Use `model_config = ConfigDict(from_attributes=True)` on response schemas.
- Validate inputs strictly — use `Field(...)` with constraints where applicable.

### Error Handling

- Use `HTTPException` with meaningful `detail` messages.
- Define custom exception classes in `app/core/exceptions.py` for domain errors.
- Add a global exception handler in `main.py` for unhandled errors — never expose raw tracebacks to clients.

```python
# app/core/exceptions.py
class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, id: int | str):
        self.resource = resource
        self.id = id
```

### Dependency Injection

- Database sessions must be injected via `Depends()`, never instantiated inside functions.
- Auth dependencies (`get_current_user`) must be applied at the router level, not inside individual endpoints.

---

## 🗄️ SQLAlchemy Rules

### General

- Use **async SQLAlchemy** (`AsyncSession`, `create_async_engine`).
- All models must inherit from a `Base` declarative class defined in `app/core/database.py`.
- Always define `__tablename__` explicitly.
- Every model must have a primary key column named `id` of type `UUID` (default `uuid4`) or `Integer`.

### Model Definition

```python
# ✅ Correct model structure
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

### Query Rules

- All DB queries live in the **repository layer** only (`app/repositories/`).
- Never use `db.execute()` with raw SQL strings — always use SQLAlchemy ORM or `text()` with bound parameters.
- Always use `select()` from `sqlalchemy` — never use legacy `db.query()` style.
- Add indexes on all columns used in `WHERE` or `JOIN` conditions.

### Relationships

- Always use `Mapped[]` type hints for relationships.
- Use `lazy="selectin"` or `lazy="joined"` explicitly — never rely on default lazy loading in async context (it will raise errors).

---

## 🐘 PostgreSQL via Supabase Rules

### Connection

- Always use the **connection pooler URL** (port `6543`) from Supabase for the application, not the direct connection (port `5432`).
- Store the connection string in `.env` as `DATABASE_URL`. Never hardcode credentials.
- Use `asyncpg` as the async driver: `postgresql+asyncpg://...`

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

### Migrations (Alembic)

- **Never edit an already-applied migration file.** Create a new one.
- Every migration must have a descriptive message: `alembic revision --autogenerate -m "add_index_to_users_email"`.
- Review autogenerated migrations before applying — Alembic sometimes misses changes or generates incorrect diffs.
- Test migrations both `upgrade` and `downgrade` locally before committing.
- **Never use `CASCADE DELETE` without explicit approval.** Flag it and ask.

### Supabase-Specific

- Row Level Security (RLS) policies are managed in Supabase — do not attempt to replicate them in application code.
- Use Supabase service role key only in server-side code, never expose it to clients.
- For file storage, use Supabase Storage SDK — do not store binary files in PostgreSQL columns.

---

## 🔐 Security Rules

- **Never log sensitive data:** passwords, tokens, API keys, PII.
- **Never store plain-text passwords.** Use `passlib` with `bcrypt`.
- All secret values must come from environment variables via `pydantic-settings`.
- JWT tokens must have an expiry (`exp` claim). Default access token lifetime: 30 minutes.
- Rate limiting must be applied to all auth endpoints (`/login`, `/register`, `/refresh`).
- Validate and sanitize all user-provided data before it reaches the DB layer.

---

## ✅ Testing Rules

- Write tests alongside every new feature — not after.
- Use `pytest` + `pytest-asyncio` for async tests.
- Use a separate test database — never run tests against the development or production DB.
- Every new endpoint must have at minimum:
  - 1 happy path test
  - 1 validation error test (invalid input)
  - 1 auth/permission test (if the endpoint is protected)
- Repository functions must have unit tests with a mocked DB session.
- Target **≥ 80% coverage** on the `app/services/` and `app/repositories/` layers.

---

## 🚫 Never Do These

| Rule                                            | Reason                                        |
| ----------------------------------------------- | --------------------------------------------- |
| `import *`                                      | Pollutes namespace, makes dependencies opaque |
| Raw SQL strings without `text()` + bound params | SQL injection risk                            |
| Returning ORM models directly from endpoints    | Leaks internal schema, breaks serialization   |
| Hardcoded secrets or connection strings         | Security                                      |
| `db.query()` legacy style                       | Deprecated, breaks with async                 |
| Business logic inside routers                   | Untestable, violates separation of concerns   |
| Bare `except:` clauses                          | Swallows all errors silently                  |
| Modifying applied migration files               | Breaks migration history                      |
| `print()` for logging                           | Use `logging` module or `structlog`           |
| Committing `.env` files                         | Exposes secrets                               |

---

## 📋 Pre-Commit Checklist

Before marking any task as complete, verify:

- [ ] All new functions have type hints
- [ ] No hardcoded values (use constants or env vars)
- [ ] Error cases are handled explicitly
- [ ] New endpoints have corresponding tests
- [ ] No secrets or credentials in code
- [ ] Migration files reviewed (if DB changes were made)
- [ ] `uv sync` runs without errors
- [ ] All tests pass: `uv run pytest`
