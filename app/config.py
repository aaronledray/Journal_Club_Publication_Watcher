"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Journal Club Publication Watcher"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8000"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"

    # Database
    DATABASE_URL: str = "sqlite:///./journal_watcher.db"

    # JWT Settings
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7

    # Magic Link Settings
    MAGIC_LINK_EXPIRATION_MINUTES: int = 15

    # Email Settings (for production)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
