from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Alert, Prediction
from app.db.repositories import AlertRepository

HIGH_RISK_THRESHOLD = 0.70


def create_prediction_alerts(
    session: Session,
    case_id: str,
    transaction_id: str,
    predictions: list[Prediction],
    threshold: float = HIGH_RISK_THRESHOLD,
) -> list[Alert]:
    """Create alerts for qualifying predictions.

    Alerts are never deleted: re-prediction appends new alerts and preserves
    the case's full alert history.
    """
    entries = []
    for prediction in predictions:
        score = float(prediction.risk_score)
        if score < threshold:
            continue
        severity = (
            "critical"
            if score >= 0.90
            else "high"
            if score >= 0.70
            else "medium"
        )
        message = (
            f"{severity.upper()} ATM risk for {prediction.atm_id} "
            f"with model score {score:.2%}."
        )
        entries.append(
            {
                "case_id": case_id,
                "prediction_id": prediction.id,
                "transaction_id": transaction_id,
                "atm_id": prediction.atm_id,
                "risk_score": score,
                "severity": severity,
                "message": message,
            }
        )
    return AlertRepository(session).create_many(entries)