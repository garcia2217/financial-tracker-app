FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY app/ ./app/
COPY SYSTEM_INSTRUCTIONS.md ./

ENV PATH="/app/.venv/bin:$PATH"

# Single worker — in-memory Telegram dedup requires process-local state
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
