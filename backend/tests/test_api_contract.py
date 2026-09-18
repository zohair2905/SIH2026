from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

CASE_ID = "CASE-E2CAEBEA64"
TXN_ID = "TXN000000294"


def test_cases_contract(session: Session, client: TestClient) -> None:
    rows = client.get("/api/cases").json()
    assert len(rows) == 3
    assert rows[0]["case_type"] == "atm_withdrawal"

    created = client.post(
        "/api/cases",
        json={
            "transaction_id": TXN_ID,
            "title": "Contract title",
            "description": "Contract description",
            "priority": "high",
        },
    )
    assert created.status_code == 200
    body = created.json()
    case_id = body["case_id"]
    assert body["amount"] is None
    assert body["status"] == "open"
    assert body["created_at"]

    assert client.get(f"/api/cases/{case_id}").status_code == 200

    tx = client.get(f"/api/cases/{case_id}/transactions")
    assert tx.status_code == 200
    assert tx.json()[0]["transaction_id"] == TXN_ID

    assert client.get("/api/cases/CASE-UNKNOWN").status_code == 404


def test_alerts_contract(session: Session, client: TestClient) -> None:
    rows = client.get("/api/alerts").json()
    assert len(rows) == 1
    alert = rows[0]
    alert_id = alert["alert_id"]
    assert alert["prediction_id"] is not None
    assert alert["message"]

    ack = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert ack.status_code == 200
    body = ack.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_at"] is not None

    resolved = client.patch(f"/api/alerts/{alert_id}", json={"status": "resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    assert client.get("/api/alerts/999999").status_code == 404


def test_heatmap_analytics_contract(session: Session, client: TestClient) -> None:
    heatmap = client.get(f"/api/heatmap?case_id={CASE_ID}")
    assert heatmap.status_code == 200
    assert len(heatmap.json()["points"]) == 5

    summary = client.get("/api/analytics/summary").json()
    assert summary["cases"] == 3
    assert summary["predictions"] == 5
    assert summary["alerts"] == 1

    analytics = client.get("/api/analytics").json()
    assert analytics["summary"]["cases"] == 3
    assert len(analytics["top_atms"]) <= 10


def test_transactions_contract(client: TestClient) -> None:
    row = client.get(f"/api/transactions/{TXN_ID}")
    assert row.status_code == 200
    assert row.json()["transaction_id"] == TXN_ID
    assert client.get("/api/transactions/TXN-DOES-NOT-EXIST").status_code == 404


def test_legacy_compat_paths_delegate(client: TestClient) -> None:
    assert client.get("/cases").status_code == 200
    assert client.get(f"/cases/{CASE_ID}").status_code == 200
    assert client.get("/alerts").status_code == 200
    assert client.get("/heatmap").status_code == 200
    assert client.get("/analytics").status_code == 200
    assert client.get("/analytics/summary").status_code == 200
    assert client.get(f"/transactions/{TXN_ID}").status_code == 200

    created = client.post(
        "/cases", json={"transaction_id": TXN_ID, "title": "Compat title"}
    )
    assert created.status_code == 200
    assert created.json()["case_id"]