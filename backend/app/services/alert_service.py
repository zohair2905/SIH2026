from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Alert, PredictionRun
from app.db.repositories import AlertRepository
from app.services.config import ALERT_RISK_FLOOR, severity_for_score


def create_prediction_alerts(
    session: Session,
    run: PredictionRun,
) -> list[Alert]:
    """Create alert rows for the run's ranked locations crossing the floor.

    Blueprint 17 semantics: severity below ALERT_RISK_FLOOR (low) is
    dashboard-only; medium and above materialise as notification/priority
    alert rows. Severity exists on every prediction, but only floor-crossing
    ones create an alert record. Alerts are never deleted: re-prediction
    appends new alerts and preserves the case's full alert history.
    """
    entries = []
    for prediction in run.predictions:
        score = float(prediction.risk_score)
        if score < ALERT_RISK_FLOOR:
            continue
        severity = prediction.risk_severity or severity_for_score(score)
        message = (
            f"{severity.upper()} ATM risk for {prediction.atm_id} "
            f"with model score {score:.2%}."
        )
        entries.append(
            {
                "case_id": run.case_id,
                "prediction_id": prediction.id,
                "transaction_id": run.transaction_id,
                "atm_id": prediction.atm_id,
                "risk_score": score,
                "severity": severity,
                "message": message,
            }
        )
    return AlertRepository(session).create_many(entries)