from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "LedgerPilot API"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://ledger:ledger@localhost:5432/ledgerpilot"

    # Security
    secret_key: str = "change-me-in-production"

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
