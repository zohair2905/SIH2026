import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://sih:sih@localhost:5432/sihdb_test"
)

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.seeding import seed_demo

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session", autouse=True)
def database():
    """Create the test database on first run, then apply Alembic migrations."""
    from sqlalchemy import create_engine, text

    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'sihdb_test'")
        ).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE sihdb_test"))

    from app.db.migrate import upgrade

    upgrade()
    yield


@pytest.fixture()
def session():
    with SessionLocal() as s:
        seed_demo.seed(s)
        yield s


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c