from datetime import UTC, datetime

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.repositories import AlertRepository, PredictionRepository
from app.seeding import seed_demo
from app.services.config import (
    MODEL_FEATURES,
    MODEL_FILE,
    MODEL_NAME,
    MODEL_VERSION,
    prediction_window,
)
from app.services.model_service import ModelService

_CASE_ID = "CASE-E2CAEBEA64"
_TX = "TXN000000294"


def _five_items(scores: list[float] | None = None) -> list[dict]:
    scores = scores or [0.90, 0.55, 0.30, 0.20, 0.10]
    return [
        {
            "atm_id": f"ATM090{r}",
            "rank": r,
            "risk_score": scores[r - 1],
            "risk_severity": "high" if scores[r - 1] >= 0.70 else (
                "medium" if scores[r - 1] >= 0.50 else "low"
            ),
            "confidence": 0.1,
            "evidence": {"top_factors": [], "driver": "dashboard test", "heuristic": True},
            "candidate_rank": r,
            "latitude": 18.5,
            "longitude": 73.8,
            "city": "Pune",
            "area_type": "Residential",
            "atm_status": "Active",
            "atm_density_1km": 900.0,
            "atm_withdrawal_count": 0.0,
            "atm_recent_activity": 0.0,
            "synthetic_location_data": True,
        }
        for r in range(1, 6)
    ]


def _persist_run(session: Session, case_id: str) -> None:
    start, end = prediction_window(datetime.now(UTC))
    PredictionRepository(session).create_run(
        case_id=case_id,
        transaction_id=_TX,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=start,
        window_end=end,
        confidence=0.2,
        predictions=_five_items([0.99, 0.88, 0.30, 0.20, 0.10]),
    )


def test_dashboard_contract(client: TestClient, session: Session) -> None:
    body = client.get("/api/dashboard").json()

    summary = body["summary"]
    assert summary["cases"] == 3
    assert summary["open_cases"] == 3
    assert summary["alerts"] == 1
    assert summary["active_alerts"] == 1
    assert summary["unacknowledged_alerts"] == 1
    assert summary["predictions"] == 5
    assert summary["average_prediction_risk"] == pytest.approx(0.212, abs=1e-6)

    assert body["alert_severity_distribution"] == {
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
    }
    # Only CASE-E2CAEBEA64 has a current run; its top-1 severity is high.
    assert body["case_risk_distribution"] == {
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
    }

    top_atms = body["top_atms"]
    assert len(top_atms) <= 10
    assert top_atms[0]["atm_id"] == "ATM00100"
    assert top_atms[0]["risk_score"] == pytest.approx(0.7266666666666667)
    assert top_atms[0]["severity"] == "high"

    assert len(body["recent_alerts"]) == 1
    alert = body["recent_alerts"][0]
    assert alert["case_id"] == _CASE_ID
    assert alert["prediction_id"] is not None


def test_dashboard_current_run_scoping(client: TestClient, session: Session) -> None:
    seed_demo.seed(session)
    _persist_run(session, _CASE_ID)  # supersedes the seeded run

    body = client.get("/api/dashboard").json()
    summary = body["summary"]
    assert summary["predictions"] == 5  # only the current run's rows count
    assert summary["average_prediction_risk"] == pytest.approx(
        (0.99 + 0.88 + 0.30 + 0.20 + 0.10) / 5
    )
    assert body["top_atms"][0]["atm_id"] == "ATM0901"
    assert body["top_atms"][0]["risk_score"] == pytest.approx(0.99)
    assert body["case_risk_distribution"]["critical"] == 1

    seed_demo.seed(session)  # restore seeded state for order-dependent tests


def test_alert_listing_contract_and_filters(client: TestClient, session: Session) -> None:
    rows = client.get("/api/alerts").json()
    assert len(rows) == 1
    alert = rows[0]
    assert alert["alert_id"] == 1
    assert alert["case_id"] == _CASE_ID
    assert alert["prediction_id"] is not None
    assert alert["transaction_id"] == _TX
    assert alert["atm_id"] == "ATM00100"
    assert alert["risk_score"] == pytest.approx(0.7266666666666667)
    assert alert["severity"] == "high"
    assert alert["status"] == "new"
    assert alert["message"]
    assert alert["acknowledged_at"] is None
    assert alert["created_at"]
    assert alert["updated_at"]

    assert len(client.get("/api/alerts?status=new").json()) == 1
    assert client.get("/api/alerts?status=acknowledged").json() == []
    assert len(client.get("/api/alerts?severity=high").json()) == 1
    assert client.get("/api/alerts?severity=critical").json() == []

    detail = client.get("/api/alerts/1")
    assert detail.status_code == 200
    assert detail.json()["alert_id"] == 1
    assert client.get("/api/alerts/999999").status_code == 404


def test_alert_acknowledge_resolve_and_unknown(
    client: TestClient, session: Session
) -> None:
    ack = client.post("/api/alerts/1/acknowledge")
    assert ack.status_code == 200
    body = ack.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_at"] is not None

    persisted = AlertRepository(session).get(1)
    session.expire_all()
    assert persisted is not None
    assert persisted.status == "acknowledged"
    assert persisted.acknowledged_at is not None

    resolved = client.patch("/api/alerts/1", json={"status": "resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    session.expire_all()
    assert AlertRepository(session).get(1).status == "resolved"

    assert client.post("/api/alerts/999999/acknowledge").status_code == 404
    assert client.patch("/api/alerts/999999", json={"status": "resolved"}).status_code == 404


def test_reprediction_via_api_preserves_historical_alerts(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_demo.seed(session)
    if not MODEL_FILE.exists():
        importances = np.full(len(MODEL_FEATURES), 0.1 / len(MODEL_FEATURES))

        def _predict(_self, features):
            return np.linspace(0.75, 0.15, len(features))

        monkeypatch.setattr(ModelService, "load", lambda _self: None)
        monkeypatch.setattr(ModelService, "predict", _predict)
        monkeypatch.setattr(
            ModelService, "feature_importances", lambda _self: importances
        )

    before = client.get("/api/predictions/PRED-CASE-E2CAEBEA64-1").json()
    assert before["superseded_at"] is None

    response = client.post("/api/cases/CASE-E2CAEBEA64/predict")
    assert response.status_code == 200

    after = client.get("/api/predictions/PRED-CASE-E2CAEBEA64-1").json()
    assert after["superseded_at"] is not None
    assert response.json()["prediction_id"] != "PRED-CASE-E2CAEBEA64-1"

    alerts = client.get("/api/alerts").json()
    assert len(alerts) >= 2  # seeded alert survives; new run appended its own
    assert any(a["alert_id"] == 1 for a in alerts)
    assert all(a["prediction_id"] is not None for a in alerts)


def test_dashboard_and_alerts_empty_state(
    client: TestClient, session: Session
) -> None:
    seed_demo._truncate(session)
    body = client.get("/api/dashboard").json()

    summary = body["summary"]
    assert summary["cases"] == 0
    assert summary["open_cases"] == 0
    assert summary["alerts"] == 0
    assert summary["active_alerts"] == 0
    assert summary["unacknowledged_alerts"] == 0
    assert summary["predictions"] == 0
    assert summary["average_prediction_risk"] is None
    assert body["alert_severity_distribution"] == {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    assert body["case_risk_distribution"] == {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    assert body["top_atms"] == []
    assert body["recent_alerts"] == []
    assert client.get("/api/alerts").json() == []