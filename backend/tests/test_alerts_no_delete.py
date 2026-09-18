from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alert
from app.db.repositories import AlertRepository, CaseRepository, PredictionRepository
from app.services.alert_service import create_prediction_alerts

_PREDICTIONS = [
    {
        "atm_id": "ATM91001", "rank": 1, "risk_score": 0.85, "candidate_rank": 2,
        "latitude": 18.5, "longitude": 73.8, "city": "Pune", "area_type": "Residential",
        "atm_status": "Active", "atm_density_1km": 900.0,
        "atm_withdrawal_count": 1.0, "atm_recent_activity": 0.0, "synthetic_location_data": True,
    },
    {
        "atm_id": "ATM91002", "rank": 2, "risk_score": 0.30, "candidate_rank": 1,
        "latitude": 18.5, "longitude": 73.8, "city": "Pune", "area_type": "Residential",
        "atm_status": "Active", "atm_density_1km": 900.0,
        "atm_withdrawal_count": 1.0, "atm_recent_activity": 0.0, "synthetic_location_data": True,
    },
]


def _alert_count_for_case(session: Session, case_id: str) -> int:
    return session.execute(
        select(func.count()).select_from(Alert).where(Alert.case_id == case_id)
    ).scalar_one()


def test_rerun_predict_appends_alerts_and_preserves_history(session: Session) -> None:
    case_id = "CASE-ALERT01"
    CaseRepository(session).create(
        case_id=case_id,
        transaction_id="TXN000000294",
        title="Title",
        description=None,
        priority="medium",
    )

    first = PredictionRepository(session).replace_for_case(
        case_id, "TXN000000294", _PREDICTIONS
    )
    alerts_1 = create_prediction_alerts(session, case_id, "TXN000000294", first)
    assert len(alerts_1) == 1  # only the 0.85 candidate crosses the 0.70 threshold
    assert alerts_1[0].prediction_id == first[0].id
    assert alerts_1[0].status == "new"
    assert _alert_count_for_case(session, case_id) == 1

    second = PredictionRepository(session).replace_for_case(
        case_id, "TXN000000294", _PREDICTIONS
    )
    alerts_2 = create_prediction_alerts(session, case_id, "TXN000000294", second)
    assert len(alerts_2) == 1
    assert alerts_2[0].id != alerts_1[0].id

    rows = session.scalars(
        select(Alert).where(Alert.case_id == case_id).order_by(Alert.id)
    ).all()
    assert len(rows) == 2  # previous alert survives re-prediction
    assert {a.id for a in rows} == {alerts_1[0].id, alerts_2[0].id}
    assert any(a.status == "new" for a in rows)


def test_acknowledge_and_status_update_preserved(session: Session) -> None:
    case_id = "CASE-ALERT02"
    CaseRepository(session).create(
        case_id=case_id,
        transaction_id="TXN000000294",
        title="Title",
        description=None,
        priority="medium",
    )
    predictions = PredictionRepository(session).replace_for_case(
        case_id, "TXN000000294", _PREDICTIONS
    )
    (alert,) = create_prediction_alerts(session, case_id, "TXN000000294", predictions)

    repo = AlertRepository(session)
    acknowledged = repo.acknowledge(alert.id, acknowledged_by=1)
    assert acknowledged is not None
    assert acknowledged.status == "acknowledged"
    assert acknowledged.acknowledged_by == 1
    assert acknowledged.acknowledged_at is not None

    resolved = repo.update_status(alert.id, "resolved")
    assert resolved is not None
    assert resolved.status == "resolved"