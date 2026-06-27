"""Application settings — loaded from environment variables via Pydantic.

All configuration lives here so other modules stay env-agnostic.
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors(origins: str) -> list[str]:
    return [s.strip() for s in origins.split(",") if s.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Defaults are suitable for local development (Docker Compose).
    Override via `.env` files or environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Application ----------
    APP_NAME: str = "LabInherit"
    APP_ENV: str = "local"
    APP_DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ---------- CORS ----------
    APP_CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins. Use * for all in dev, specific domains in prod.",
    )

    @property
    def cors_origins(self) -> list[str]:
        return _parse_cors(self.APP_CORS_ORIGINS)

    # ---------- Base URL ----------
    APP_BASE_URL: str = "http://localhost:5173"

    # ---------- Database ----------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "labinherit"
    DB_PASSWORD: str = "labinherit_dev"
    DB_NAME: str = "labinherit"
    DB_ECHO: bool = False

    @property
    def database_url(self) -> str:
        """Async MySQL connection string for SQLAlchemy."""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync MySQL connection string for Alembic CLI."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # ---------- JWT ----------
    JWT_SECRET: str = Field(default="please-change-me-to-a-32-char-random-string")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ---------- SMTP ----------
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@labinherit.local"
    SMTP_TLS: bool = True

    # ---------- Board rules ----------
    STALE_DAYS: int = 90

    # ---------- Email worker ----------
    EMAIL_WORKER_POLL_INTERVAL: int = 5
    EMAIL_WORKER_BATCH_SIZE: int = 20
    EMAIL_WORKER_MAX_RETRIES: int = 5

    # ---------- Uploads ----------
    UPLOAD_DIR: str = "./uploads"

    # ---------- Validation helpers ----------
    @property
    def is_dev(self) -> bool:
        return self.APP_ENV in ("local", "development", "dev")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV in ("production", "prod")

    def ensure_jwt_secret(self) -> None:
        """Call at startup to guard against weak secrets in production."""
        weak = "please-change-me"
        if self.is_production and self.JWT_SECRET.startswith(weak):
            raise RuntimeError(
                f"JWT_SECRET must be set to a strong value in production "
                f"(must not start with '{weak}')."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Singleton instance used throughout the application
settings = get_settings()
