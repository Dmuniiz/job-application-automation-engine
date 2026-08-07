from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Job Application Automation Engine"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Flag global para alternar entre Mock e Scrapers Reais
    USE_MOCK: bool = False
    
    # Perfil Canônico Padrão
    DEFAULT_PROFILE_ID: str = "support_ops_engineer"
    MATCH_THRESHOLD: int = Field(default=80, ge=0, le=100)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()