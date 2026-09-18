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
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/sih_app.db")
    )


settings = Settings()