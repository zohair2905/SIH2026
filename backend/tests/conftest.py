import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://sih:sih@localhost:5432/sihdb_test"
)
os.environ.setdefault("DEMO_PASSWORD", "Demo#2026")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import User
from app.db.repositories import AuthRepository
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


def _token_client(session, user: User) -> TestClient:
    token = AuthRepository(session).create_session(user.id)
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class _AutoAuthClient(TestClient):
    """TestClient that stays logged in as the seeded demo user even when a
    test re-seeds the database (seed_demo truncates auth_sessions)."""

    def __init__(self, session, user: User) -> None:
        super().__init__(app)
        self._user = user
        self._bearer = AuthRepository(session).create_session(user.id)
        self.headers["Authorization"] = f"Bearer {self._bearer}"

    def _ensure_auth(self) -> None:
        from app.db.repositories import AuthRepository as Repo
        from app.db.session import SessionLocal
        from app.seeding import seed_demo as seed

        with SessionLocal() as s:
            if Repo(s).user_for_token(self._bearer) is not None:
                return
            user = s.get(User, self._user.id)
            if user is None or not user.is_active:
                user = s.scalars(
                    select(User).where(User.email == self._user.email)
                ).first()
                if user is None:
                    # The test truncated the whole DB (empty-state coverage);
                    # the authenticated investigator must still exist.
                    user = User(**seed._demo_user())
                    s.add(user)
                    s.commit()
                user = s.get(User, user.id)
            self._bearer = Repo(s).create_session(user.id)
            self.headers["Authorization"] = f"Bearer {self._bearer}"

    def request(self, *args, **kwargs):
        self._ensure_auth()
        return super().request(*args, **kwargs)


@pytest.fixture()
def client(session):
    """Authenticated investigator client (the seeded demo user)."""
    user = session.scalars(
        select(User).where(User.email == seed_demo.DEMO_EMAIL)
    ).one()
    with _AutoAuthClient(session, user) as c:
        yield c


@pytest.fixture()
def anon_client():
    """Unauthenticated client, for 401/403 contract tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_client(session):
    """Authenticated admin client (the seeded admin user)."""
    user = session.scalars(
        select(User).where(User.email == seed_demo.ADMIN_EMAIL)
    ).one()
    with _token_client(session, user) as c:
        yield c


@pytest.fixture()
def analyst_client(session):
    """Authenticated analyst client (the seeded analyst user)."""
    user = session.scalars(
        select(User).where(User.email == seed_demo.ANALYST_EMAIL)
    ).one()
    with _token_client(session, user) as c:
        yield c