from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "RevTrace API"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Database
    # PostgreSQL (Docker / production): postgresql+asyncpg://user:pass@host:5432/db
    # SQLite (local dev fallback):      sqlite+aiosqlite:///./revtrace.db
    database_url: str = "sqlite+aiosqlite:///./revtrace.db"

    # Security
    secret_key: str = "change-me-in-production"

    # Phase 7 — AI Investigation Agent
    # Get a free key at https://aistudio.google.com/app/apikey
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # CORS — comma-separated string in .env; parsed to list by property
    allowed_origins_str: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins_str.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
