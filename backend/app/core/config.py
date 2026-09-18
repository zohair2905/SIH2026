from __future__ import annotations

import os
from dataclasses import dataclass, field

APP_NAME = "SIH 26184 - Proactive ATM Withdrawal Intelligence API"


@dataclass(frozen=True)
class Settings:
    app_name: str = APP_NAME
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://sih:sih@localhost:5432/sihdb",
        )
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        )
    )
    token_ttl_hours: int = field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_TTL_HOURS", "12"))
    )
    session_cookie_name: str = field(
        default_factory=lambda: os.getenv("SESSION_COOKIE_NAME", "sih_access_token")
    )
    secure_cookies: bool = field(
        default_factory=lambda: os.getenv("AUTH_COOKIE_SECURE", "false").lower()
        in {"1", "true", "yes", "on"}
    )


settings = Settings()