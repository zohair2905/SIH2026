"""Phase 6: authentication, RBAC and audit-logging contract tests."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AuditLog
from app.db.repositories import AuditRepository

DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo#2026")
DEMO_EMAIL = "a.patil@cic.gov.in"


def _count(session: Session) -> int:
    return int(
        session.execute(select(func.count()).select_from(AuditLog)).scalar_one()
    )


# --- Authentication -----------------------------------------------------------


def test_login_success_returns_token_and_user_never_password(session, anon_client):
    response = anon_client.post(
        "/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == DEMO_EMAIL
    assert body["user"]["role"] == "investigator"
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()


def test_login_wrong_password_and_unknown_email_identical(session, anon_client):
    unknown = anon_client.post(
        "/api/auth/login",
        json={"email": "nobody@cic.gov.in", "password": DEMO_PASSWORD},
    )
    wrong = anon_client.post(
        "/api/auth/login", json={"email": DEMO_EMAIL, "password": "wrong-password"}
    )
    for response in (unknown, wrong):
        assert response.status_code == 401
    # Same error code and message (no user enumeration); request_id differs.
    assert unknown.json()["detail"] == wrong.json()["detail"]
    assert unknown.json()["error"] == wrong.json()["error"]


def test_login_missing_and_invalid_input(anon_client):
    assert anon_client.post("/api/auth/login", json={}).status_code == 422
    assert (
        anon_client.post(
            "/api/auth/login", json={"email": "", "password": ""}
        ).status_code
        == 422
    )


def test_me_authenticated_and_unauthenticated(client, anon_client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == DEMO_EMAIL
    assert user["role"] == "investigator"
    assert "password" not in response.text.lower()

    assert anon_client.get("/api/auth/me").status_code == 401

    bad = TestClient(__import__("app.main", fromlist=["app"]).app)
    bad.headers["Authorization"] = "Bearer invalid-token"
    with bad:
        assert bad.get("/api/auth/me").status_code == 401


def test_logout_revokes_session(session, anon_client):
    login = anon_client.post(
        "/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    authed = TestClient(__import__("app.main", fromlist=["app"]).app)
    authed.headers["Authorization"] = f"Bearer {token}"
    with authed as c:
        assert c.get("/api/auth/me").status_code == 200
        assert c.post("/api/auth/logout").status_code == 200
        # The session is invalidated server-side, not just on the client.
        assert c.get("/api/auth/me").status_code == 401
        assert c.get("/api/dashboard").status_code == 401

    # Logout is idempotent.
    assert anon_client.post("/api/auth/logout").status_code == 200


# --- RBAC ---------------------------------------------------------------------


def test_protected_routes_unauthenticated_401(anon_client):
    for method, path in [
        ("get", "/api/dashboard"),
        ("get", "/api/cases"),
        ("get", "/api/alerts"),
        ("get", "/api/analytics"),
        ("get", "/api/heatmap"),
        ("get", "/api/transactions/TXN000000294"),
        ("get", "/api/predictions/PRED-CASE-E2CAEBEA64-1"),
    ]:
        assert getattr(anon_client, method)(path).status_code == 401, path


def test_investigator_read_access(client):
    for method, path in [
        ("get", "/api/dashboard"),
        ("get", "/api/cases"),
        ("get", "/api/alerts"),
        ("get", "/api/analytics"),
        ("get", "/api/heatmap"),
        ("get", "/api/transactions/TXN000000294"),
        ("get", "/api/predictions/PRED-CASE-E2CAEBEA64-1"),
        ("get", "/api/cases/CASE-E2CAEBEA64/notes"),
    ]:
        assert getattr(client, method)(path).status_code == 200, path


def test_analyst_reads_but_cannot_operate(analyst_client):
    assert analyst_client.get("/api/dashboard").status_code == 200
    assert analyst_client.get("/api/alerts").status_code == 200

    assert analyst_client.post("/api/alerts/1/acknowledge").status_code == 403
    assert (
        analyst_client.patch("/api/alerts/1", json={"status": "resolved"}).status_code
        == 403
    )
    assert (
        analyst_client.patch(
            "/api/cases/CASE-E2CAEBEA64", json={"status": "investigating"}
        ).status_code
        == 403
    )
    assert (
        analyst_client.post(
            "/api/cases/CASE-E2CAEBEA64/notes", json={"note": "x"}
        ).status_code
        == 403
    )
    assert (
        analyst_client.post(
            "/api/predictions/predict?case_id=CASE-E2CAEBEA64",
            json={"transaction_id": "TXN000000294"},
        ).status_code
        == 403
    )


def test_investigator_privileged_actions(client):
    acknowledged = client.post("/api/alerts/1/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    resolved = client.patch("/api/alerts/1", json={"status": "resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    status = client.patch(
        "/api/cases/CASE-E2CAEBEA64", json={"status": "investigating"}
    )
    assert status.status_code == 200
    assert status.json()["status"] == "investigating"


def test_audit_logs_admin_only(anon_client, client, analyst_client, admin_client):
    assert anon_client.get("/api/audit-logs").status_code == 401
    assert client.get("/api/audit-logs").status_code == 403
    assert analyst_client.get("/api/audit-logs").status_code == 403
    admin_response = admin_client.get("/api/audit-logs")
    assert admin_response.status_code == 200
    assert isinstance(admin_response.json(), list)


# --- Audit trail --------------------------------------------------------------


def test_actions_produce_audit_records_with_actor(client, session):
    before = _count(session)

    client.post("/api/alerts/1/acknowledge")
    client.patch("/api/alerts/1", json={"status": "resolved"})
    client.patch("/api/cases/CASE-E2CAEBEA64", json={"status": "investigating"})
    client.post("/api/cases/CASE-E2CAEBEA64/notes", json={"note": "Observed activity."})
    session.expire_all()

    actions = {
        row.action for row in session.execute(select(AuditLog)).scalars().all()
    }
    assert {
        "alert.acknowledged",
        "alert.resolved",
        "case.status_changed",
        "case.note_created",
    }.issubset(actions)
    assert _count(session) >= before + 4

    for row in session.execute(select(AuditLog)).scalars():
        assert row.actor == DEMO_EMAIL
        assert row.user_id is not None
        assert row.resource_type in {"alert", "case", "case_note"}


def test_login_failure_and_success_are_audited(anon_client, session):
    anon_client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "nope"})
    anon_client.post(
        "/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    )
    session.expire_all()
    actions = {
        row.action for row in session.execute(select(AuditLog)).scalars().all()
    }
    assert {"auth.login_failed", "auth.login_succeeded"}.issubset(actions)


def test_audit_records_never_store_secrets(client, session):
    client.post("/api/alerts/1/acknowledge")
    client.post("/api/auth/logout")
    session.expire_all()
    for row in session.execute(select(AuditLog)).scalars():
        serialized = str(row.details or {}).lower() + str(row.actor or "").lower()
        assert "password" not in serialized
        assert "token" not in serialized


def test_historical_audit_records_preserved(client, session):
    count_after_work = _count(session)
    client.post("/api/alerts/1/acknowledge")
    AuditRepository(session).record(
        action="test.synthetic", resource_type="probe"
    )
    session.expire_all()
    rows = session.execute(select(AuditLog)).scalars().all()
    assert _count(session) == count_after_work + 2
    assert all(row.created_at is not None for row in rows)
    assert [row.id for row in rows] == sorted(row.id for row in rows)