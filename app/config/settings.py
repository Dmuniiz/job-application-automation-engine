from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Job Application Automation Engine"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    USE_MOCK: bool = False
    DEFAULT_PROFILE_ID: str = "support_ops_engineer"
    MATCH_THRESHOLD: int = Field(default=80, ge=0, le=100)

    # Pilar 1: Persistency
    # Dev:  sqlite:///./data/app.db
    # Prod: postgresql+psycopg2://user:pass@host:5432/jobs
    DATABASE_URL: str = Field(
        default="sqlite:///./data/app.db",
        description="SQLite for development, PostgreSQL for production via .env",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()