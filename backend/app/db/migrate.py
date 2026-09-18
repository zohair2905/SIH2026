from __future__ import annotations

import argparse
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_DIR = BASE_DIR / "alembic"
ALEMBIC_INI = BASE_DIR / "alembic.ini"


def alembic_config():
    from alembic.config import Config

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    return cfg


def upgrade() -> None:
    """Apply all pending migrations to the configured database."""
    from alembic import command

    command.upgrade(alembic_config(), "head")


def status() -> None:
    from alembic import command

    command.current(alembic_config())


def main() -> None:
    parser = argparse.ArgumentParser(prog="migrate")
    parser.add_argument("action", choices=["upgrade", "status"], default="upgrade", nargs="?")
    args = parser.parse_args()

    # Only override the URL setting if the environment did not provide one, so
    # tests can pin DATABASE_URL externally without touching this file.
    if "DATABASE_URL" not in os.environ:
        from app.core.config import settings

        os.environ["DATABASE_URL"] = settings.database_url

    if args.action == "upgrade":
        upgrade()
    elif args.action == "status":
        status()


if __name__ == "__main__":
    main()