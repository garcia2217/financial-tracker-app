from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

from urllib.parse import quote_plus

class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "production"] = "production"

    DB_USER: str = "postgres.zegamrtfnimzsfkpstmc"
    DB_PASSWORD: str
    DB_HOST: str = "aws-1-ap-southeast-1.pooler.supabase.com"
    DB_PORT: str = "6543"
    DB_NAME: str = "postgres"

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    FRONTEND_URL: str = "http://localhost:3000"

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_SECRET: str
    GEMINI_API_KEY: str

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def DEBUG(self) -> bool:
        return not self.is_production

    @property
    def DATABASE_URL(self) -> str:
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"postgresql+asyncpg://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
