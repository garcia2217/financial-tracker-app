from pydantic_settings import BaseSettings, SettingsConfigDict

from urllib.parse import quote_plus

class Settings(BaseSettings):
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
    GEMINI_API_KEY: str
    DEBUG: bool = False

    @property
    def DATABASE_URL(self) -> str:
        # quote_plus safely encodes any special characters in the password (e.g., ?, $, @)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"postgresql+asyncpg://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
