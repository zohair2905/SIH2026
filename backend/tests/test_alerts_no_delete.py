from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alert, PredictionRun
from app.db.repositories import AlertRepository, CaseRepository, PredictionRepository
from app.services.alert_service import create_prediction_alerts
from app.services.config import MODEL_NAME, MODEL_VERSION, prediction_window

_TX = "TXN000000294"

_PREDICTIONS = [
    {
        "atm_id": "ATM91001", "rank": 1, "risk_score": 0.85, "candidate_rank": 2,
        "risk_severity": "high", "confidence": 0.55,
        "evidence": {"top_factors": [], "driver": "test", "heuristic": True},
        "latitude": 18.5, "longitude": 73.8, "city": "Pune", "area_type": "Residential",
        "atm_status": "Active", "atm_density_1km": 900.0,
        "atm_withdrawal_count": 1.0, "atm_recent_activity": 0.0, "synthetic_location_data": True,
    },
    {
        "atm_id": "ATM91002", "rank": 2, "risk_score": 0.30, "candidate_rank": 1,
        "risk_severity": "low", "confidence": 0.0,
        "evidence": {"top_factors": [], "driver": "test", "heuristic": True},
        "latitude": 18.5, "longitude": 73.8, "city": "Pune", "area_type": "Residential",
        "atm_status": "Active", "atm_density_1km": 900.0,
        "atm_withdrawal_count": 1.0, "atm_recent_activity": 0.0, "synthetic_location_data": True,
    },
]


def _persist_run(session: Session, case_id: str) -> PredictionRun:
    start, end = prediction_window(datetime.now(UTC))
    return PredictionRepository(session).create_run(
        case_id=case_id,
        transaction_id=_TX,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=start,
        window_end=end,
        confidence=0.55,
        predictions=_PREDICTIONS,
    )


def _alert_count_for_case(session: Session, case_id: str) -> int:
    return session.execute(
        select(func.count()).select_from(Alert).where(Alert.case_id == case_id)
    ).scalar_one()


def test_rerun_predict_appends_alerts_and_preserves_history(session: Session) -> None:
    case_id = "CASE-ALERT01"
    CaseRepository(session).create(
        case_id=case_id,
        transaction_id=_TX,
        title="Title",
        description=None,
        priority="medium",
    )

    first_run = _persist_run(session, case_id)
    alerts_1 = create_prediction_alerts(session, first_run)
    assert len(alerts_1) == 1  # only the 0.85 candidate crosses the 0.50 floor
    assert alerts_1[0].prediction_id == first_run.predictions[0].id
    assert alerts_1[0].status == "new"
    assert _alert_count_for_case(session, case_id) == 1

    second_run = _persist_run(session, case_id)
    alerts_2 = create_prediction_alerts(session, second_run)
    assert len(alerts_2) == 1
    assert alerts_2[0].id != alerts_1[0].id

    rows = session.scalars(
        select(Alert).where(Alert.case_id == case_id).order_by(Alert.id)
    ).all()
    assert len(rows) == 2  # previous alert survives re-prediction
    assert {a.id for a in rows} == {alerts_1[0].id, alerts_2[0].id}
    assert any(a.status == "new" for a in rows)

    # Historical alerts must keep pointing at their originating prediction rows.
    assert alerts_1[0].prediction_id is not None
    assert alerts_2[0].prediction_id is not None
    assert alerts_1[0].prediction_id == first_run.predictions[0].id
    assert alerts_2[0].prediction_id == second_run.predictions[0].id
    assert first_run.predictions[0].run_id == first_run.id
    assert second_run.predictions[0].run_id == second_run.id

    # Both runs remain queryable; only the second is current.
    first = session.get(PredictionRun, first_run.id)
    second = session.get(PredictionRun, second_run.id)
    assert first is not None and first.superseded_at is not None
    assert second is not None and second.superseded_at is None
    assert second.seq == 2 and first.seq == 1


def test_severity_is_recorded_even_below_alert_floor(session: Session) -> None:
    """Every ranked location has severity; only medium+ materialise as alerts."""
    case_id = "CASE-ALERT03"
    CaseRepository(session).create(
        case_id=case_id,
        transaction_id=_TX,
        title="Title",
        description=None,
        priority="medium",
    )
    run = _persist_run(session, case_id)
    by_rank = {p.rank: p for p in run.predictions}
    assert by_rank[1].risk_severity == "high"
    assert by_rank[2].risk_severity == "low"


def test_acknowledge_and_status_update_preserved(session: Session) -> None:
    case_id = "CASE-ALERT02"
    CaseRepository(session).create(
        case_id=case_id,
        transaction_id=_TX,
        title="Title",
        description=None,
        priority="medium",
    )
    run = _persist_run(session, case_id)
    (alert,) = create_prediction_alerts(session, run)

    repo = AlertRepository(session)
    acknowledged = repo.acknowledge(alert.id, acknowledged_by=1)
    assert acknowledged is not None
    assert acknowledged.status == "acknowledged"
    assert acknowledged.acknowledged_by == 1
    assert acknowledged.acknowledged_at is not None

    resolved = repo.update_status(alert.id, "resolved")
    assert resolved is not None
    assert resolved.status == "resolved"