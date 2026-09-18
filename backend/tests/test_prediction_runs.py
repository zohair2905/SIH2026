from datetime import UTC, datetime

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import PredictionRun
from app.db.repositories import AnalyticsRepository, PredictionRepository
from app.seeding import seed_demo
from app.services.alert_service import create_prediction_alerts
from app.services.config import (
    MODEL_FEATURES,
    MODEL_FILE,
    MODEL_NAME,
    MODEL_VERSION,
    prediction_window,
)
from app.services.model_service import ModelService


def _five_items() -> list[dict]:
    scores = [0.70, 0.60, 0.50, 0.40, 0.30]
    return [
        {
            "atm_id": f"ATM0910{r}",
            "rank": r,
            "risk_score": scores[r - 1],
            "risk_severity": {
                0.70: "high",
                0.60: "medium",
                0.50: "medium",
                0.40: "low",
                0.30: "low",
            }[scores[r - 1]],
            "confidence": 0.10,
            "evidence": {"top_factors": [], "driver": "sequence test", "heuristic": True},
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


def _persist_run(session: Session, case_id: str):
    start, end = prediction_window(datetime.now(UTC))
    return PredictionRepository(session).create_run(
        case_id=case_id,
        transaction_id="TXN000000294",
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=start,
        window_end=end,
        confidence=0.10,
        predictions=_five_items(),
    )


def test_get_prediction_run_endpoint(client: TestClient) -> None:
    response = client.get("/api/predictions/PRED-CASE-E2CAEBEA64-1")
    assert response.status_code == 200
    body = response.json()
    assert body["prediction_id"] == "PRED-CASE-E2CAEBEA64-1"
    assert body["status"] == "completed"
    assert body["case_id"] == "CASE-E2CAEBEA64"
    assert body["model_version"] == MODEL_VERSION
    assert len(body["locations"]) == 5
    assert body["window"]["start"]
    assert body["window"]["end"] > body["window"]["start"]  # ISO strings compare lexically here
    assert body["superseded_at"] is None
    assert body["confidence_heuristic"] == "margin"
    for location in body["locations"]:
        assert location["severity"] in {"low", "medium", "high", "critical"}
        assert 0.0 <= location["confidence"] <= 1.0
        assert location["evidence"]["heuristic"] is True
        assert location["risk_score_percent"] == round(
            location["risk_score"] * 100, 2
        )

    assert client.get("/api/predictions/PRED-NO-SUCH-0").status_code == 404


def test_case_predict_model_present_returns_prediction(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Model present: POST predict succeeds with a real prediction response.

    The model artifact is gitignored, so CI never ships it. To keep this
    state tested everywhere, use the real artifact when it exists and else
    substitute a deterministic in-memory model (no skipif, no dependence on
    whether a local file happens to exist).
    """
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

    response = client.post("/api/cases/CASE-E2CAEBEA64/predict")
    assert response.status_code == 200
    body = response.json()
    assert body["prediction_id"].startswith("PRED-CASE-E2CAEBEA64-")
    assert body["model_name"] == MODEL_NAME
    assert body["model_version"] == MODEL_VERSION
    assert body["status"] == "completed"
    assert len(body["locations"]) == 5
    assert [loc["rank"] for loc in body["locations"]] == [1, 2, 3, 4, 5]
    for location in body["locations"]:
        assert 0.0 <= location["risk_score"] <= 1.0
        assert location["severity"] in {"low", "medium", "high", "critical"}
        assert 0.0 <= location["confidence"] <= 1.0
        assert location["risk_score_percent"] == round(
            location["risk_score"] * 100, 2
        )
        assert location["latitude"] is not None
        assert location["longitude"] is not None
        assert location["candidate_rank"] >= 1
        assert location["evidence"]["heuristic"] is True
    end = datetime.fromisoformat(body["window"]["end"])
    start = datetime.fromisoformat(body["window"]["start"])
    assert (end - start).total_seconds() == 24 * 3600


def test_case_predict_model_absent_returns_503(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Model absent: deterministic 503 with the model_unavailable contract.

    Stubs model availability by making load() raise FileNotFoundError, rather
    than relying on whether the (gitignored) artifact happens to exist. This
    is the exact error the real route raises when the artifact is missing.
    """
    seed_demo.seed(session)

    def _raise_missing_artifact(_self) -> None:
        raise FileNotFoundError("Model artifact not found (test stub).")

    monkeypatch.setattr(ModelService, "load", _raise_missing_artifact)

    response = client.post("/api/cases/CASE-E2CAEBEA64/predict")
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] in {"model_unavailable", "http_503"}
    assert body["request_id"]

    assert client.post("/api/cases/CASE-UNKNOWN/predict").status_code == 404


def test_full_reprediction_sequence_preserves_history(session: Session) -> None:
    """Requirement 8: run A -> run B, old alerts stay on A, analytics use B."""
    seed_demo.seed(session)
    pred_repo = PredictionRepository(session)
    case_id = "CASE-E2CAEBEA64"

    run_a = pred_repo.current_run(case_id)
    assert run_a is not None and run_a.prediction_id == "PRED-CASE-E2CAEBEA64-1"
    alerts_a = create_prediction_alerts(session, run_a)
    assert alerts_a and all(a.prediction_id == run_a.predictions[0].id for a in alerts_a)

    run_b = _persist_run(session, case_id)
    assert run_b.seq == 2
    session.expire_all()
    run_a = session.get(PredictionRun, run_a.id)
    assert run_a.superseded_at is not None

    alerts_b = create_prediction_alerts(session, run_b)
    assert alerts_b

    assert pred_repo.current_run(case_id).id == run_b.id
    assert {r.prediction_id for r in pred_repo.list_runs(case_id)} == {
        run_a.prediction_id,
        run_b.prediction_id,
    }
    assert all(a.prediction_id is not None for a in alerts_a + alerts_b)

    summary = AnalyticsRepository(session).summary()
    assert summary["predictions"] == 5  # current run only, run A excluded
    heatmap = AnalyticsRepository(session).prediction_heatmap(case_id)
    assert len(heatmap) == 5