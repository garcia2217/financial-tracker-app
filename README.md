# Financial Tracker App

A personal finance REST API built with FastAPI. Tracks income, expenses, wallets, budgets, and debts. Includes a Telegram bot interface powered by Google Gemini for natural-language transaction logging.

## Tech Stack

| Layer            | Technology                               |
| ---------------- | ---------------------------------------- |
| Runtime          | Python 3.14                              |
| Framework        | FastAPI + Uvicorn                        |
| Database         | PostgreSQL (Supabase), async via asyncpg |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic                 |
| Auth             | JWT (httponly cookie), Google OAuth2     |
| AI               | Google Gemini (Gemini API)               |
| Package manager  | uv                                       |
| Deployment       | Docker                                   |

## Features

- **Transactions** — log income, expenses, and internal transfers across multiple wallets
- **Budgets** — set default monthly templates with per-month overrides; track budgeted vs. actual spending
- **Debt ledger** — track money lent/borrowed (receivables & payables) independently from daily spending
- **Financial overview** — balance sheet summary and savings rate calculation
- **Telegram bot** — link your account and log transactions in plain language (e.g. "spent 50k on lunch"); Gemini parses and categorizes automatically
- **Google OAuth2** — sign in with Google in addition to username/password

## Project Structure

```
app/
  core/           # config, database session, custom exceptions
  models/         # SQLAlchemy ORM models
  schemas/        # Pydantic request/response schemas
  repositories/   # data access layer (DB queries only)
  services/       # business logic layer
  routers/        # FastAPI route handlers (thin controllers)
  dependencies/   # FastAPI dependency injection (auth, service factories)
alembic/          # database migrations
tests/
```

## Getting Started

### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager
- A PostgreSQL database (Supabase or local)

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

Copy the example below into a `.env` file at the project root:

```env
ENVIRONMENT=local

DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres

SECRET_KEY=your_secret_key

FRONTEND_URL=http://localhost:3000

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

GEMINI_API_KEY=your_gemini_api_key

# Optional — required for Google OAuth2
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the development server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8080`. Interactive docs at `http://localhost:8080/docs`.

## Running Tests

```bash
uv run pytest
```

## Docker

Build and run as a single container (single worker is required for in-process Telegram deduplication):

```bash
docker build -t financial-tracker .
docker run -p 8080:8080 --env-file .env financial-tracker
```

## API Overview

All routes are prefixed with `/api/v1/`. Authentication uses an httponly JWT cookie set on login.

| Resource                           | Prefix                       |
| ---------------------------------- | ---------------------------- |
| Auth (login, logout, Google OAuth) | `/api/v1/auth`               |
| Users                              | `/api/v1/users`              |
| Wallets                            | `/api/v1/wallets`            |
| Categories                         | `/api/v1/categories`         |
| Transactions                       | `/api/v1/transactions`       |
| Budgets                            | `/api/v1/budgets`            |
| Persons                            | `/api/v1/persons`            |
| Debts                              | `/api/v1/debts`              |
| Financial Overview                 | `/api/v1/financial-overview` |
| Telegram Webhook                   | `/api/v1/telegram/webhook`   |

See [API_SCHEMAS.md](./API_SCHEMAS.md) for full request/response shapes.

## Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the token.
2. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` in your `.env`.
3. Register the webhook with Telegram, passing your secret as the `secret_token` header:
   ```
   POST https://api.telegram.org/bot<TOKEN>/setWebhook
   { "url": "https://your-domain/api/v1/telegram/webhook", "secret_token": "<WEBHOOK_SECRET>" }
   ```
4. Users link their Telegram account from the web dashboard and then send `/link <code>` to the bot.

Once linked, send any natural-language message to the bot to log a transaction (e.g. "makan siang 45rb" or "received salary 5jt"). Gemini handles parsing and categorization.
