from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.repositories import AnalyticsRepository, PredictionRepository
from app.seeding import seed_demo
from app.services.config import MODEL_NAME, MODEL_VERSION, prediction_window


def _persist_run(session: Session, case_id: str, atm_ids: list[str], scores: list[float]):
    start, end = prediction_window(datetime.now(UTC))
    predictions = [
        {
            "atm_id": atm_id,
            "rank": rank,
            "risk_score": score,
            "risk_severity": "high",
            "confidence": 0.4,
            "evidence": {
                "top_factors": [
                    {"feature": "hour", "value": 15.0, "label": "hour of day"}
                ],
                "driver": "heatmap test",
                "heuristic": True,
            },
            "candidate_rank": rank,
            "latitude": 18.50 + rank * 0.01,
            "longitude": 73.80 + rank * 0.01,
            "city": "Pune",
            "area_type": "Commercial",
            "atm_status": "Active",
            "atm_density_1km": 500.0,
            "atm_withdrawal_count": 0.0,
            "atm_recent_activity": 0.0,
        }
        for rank, (atm_id, score) in enumerate(zip(atm_ids, scores), start=1)
    ]
    return PredictionRepository(session).create_run(
        case_id=case_id,
        transaction_id="TXN000000294",
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=start,
        window_end=end,
        confidence=0.4,
        predictions=predictions,
    )


def test_heatmap_endpoint_returns_enriched_points(
    client: TestClient, session: Session
) -> None:
    seed_demo.seed(session)
    response = client.get("/api/heatmap")
    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] is None
    assert body["points"]
    for point in body["points"]:
        assert point["atm_id"]
        assert point["latitude"] is not None
        assert point["longitude"] is not None
        assert 0.0 <= point["risk_score"] <= 1.0
        assert point["best_rank"] >= 1
        assert point["observation_count"] >= 1
        assert point["severity"] in {"low", "medium", "high", "critical"}
        assert 0.0 <= point["confidence"] <= 1.0
        assert isinstance(point["top_factors"], list)
        assert point["window_start"] is not None
        assert point["window_end"] is not None
        assert isinstance(point["synthetic_location_data"], bool)


def test_heatmap_scoped_to_current_run(session: Session) -> None:
    seed_demo.seed(session)
    case_id = "CASE-E2CAEBEA64"
    repo = AnalyticsRepository(session)

    seeded = repo.prediction_heatmap(case_id)
    assert [p["atm_id"] for p in seeded] == [
        "ATM00100",
        "ATM09544",
        "ATM00665",
        "ATM07825",
        "ATM06172",
    ]
    assert seeded[0]["risk_score"] == 0.7266666666666667

    _persist_run(session, case_id, ["ATM77777", "ATM77778"], [0.99, 0.88])

    current = repo.prediction_heatmap(case_id)
    assert [p["atm_id"] for p in current] == ["ATM77777", "ATM77778"]
    assert current[0]["risk_score"] == 0.99
    assert current[0]["severity"] == "critical"
    assert current[0]["best_rank"] == 1
    assert current[0]["observation_count"] == 1
    assert current[0]["top_factors"] == [
        {"feature": "hour", "value": 15.0, "label": "hour of day"}
    ]
    assert current[1]["severity"] == "high"
    assert {p["atm_id"] for p in current}.isdisjoint(
        {p["atm_id"] for p in seeded}
    )

    seed_demo.seed(session)  # restore seeded state for order-dependent tests


def test_heatmap_empty_for_unknown_case(client: TestClient) -> None:
    response = client.get("/api/heatmap?case_id=CASE-NOT-REAL")
    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "CASE-NOT-REAL"
    assert body["points"] == []