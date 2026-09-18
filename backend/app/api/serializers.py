from __future__ import annotations

from typing import Any

from app.db.models import Alert, Case, Prediction, PredictionRun


def optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def to_case_response(case: Case) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "transaction_id": case.transaction_id,
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "priority": case.priority,
        "case_type": case.case_type,
        "amount": float(case.amount) if case.amount is not None else None,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


def to_alert_response(alert: Alert) -> dict[str, Any]:
    return {
        "alert_id": alert.id,
        "case_id": alert.case_id,
        "prediction_id": alert.prediction_id,
        "transaction_id": alert.transaction_id,
        "atm_id": alert.atm_id,
        "risk_score": float(alert.risk_score),
        "severity": alert.severity,
        "status": alert.status,
        "message": alert.message,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": (
            alert.acknowledged_at.isoformat() if alert.acknowledged_at is not None else None
        ),
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
    }


def to_transaction_response(row: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime

    def as_str(value: Any) -> str | None:
        return None if value is None else str(value)

    date = row.get("transaction_date")
    time = row.get("transaction_time")
    timestamp: str | None = None
    if date is not None:
        text = f"{date} {time}" if time else str(date)
        try:
            timestamp = datetime.fromisoformat(text).isoformat()
        except ValueError:
            timestamp = text

    return {
        "transaction_id": str(row["transaction_id"]),
        "customer_id": as_str(row.get("customer_id")),
        "timestamp": timestamp,
        "account_type": as_str(row.get("account_type")),
        "transaction_type": as_str(row.get("transaction_type")),
        "transaction_amount": row.get("transaction_amount"),
        "account_balance": row.get("account_balance"),
        "state": as_str(row.get("state")),
        "credit_score": row.get("credit_score"),
        "has_loan": row.get("has_loan"),
        "kyc_status": as_str(row.get("kyc_status")),
        "channel": as_str(row.get("channel")),
    }


def to_prediction_item(prediction: Prediction) -> dict[str, Any]:
    return {
        "rank": prediction.rank,
        "atm_id": prediction.atm_id,
        "risk_score": float(prediction.risk_score),
        "risk_score_percent": round(prediction.risk_score * 100.0, 2),
        "confidence": float(prediction.confidence),
        "severity": prediction.risk_severity,
        "candidate_rank": prediction.candidate_rank,
        "latitude": optional_float(prediction.latitude),
        "longitude": optional_float(prediction.longitude),
        "city": prediction.city,
        "area_type": prediction.area_type,
        "atm_status": prediction.atm_status,
        "atm_density_1km": optional_float(prediction.atm_density_1km),
        "atm_withdrawal_count": optional_float(prediction.atm_withdrawal_count),
        "atm_recent_activity": optional_float(prediction.atm_recent_activity),
        "synthetic_location_data": bool(prediction.synthetic_location_data),
        "evidence": prediction.evidence or {},
    }


def to_prediction_run_response(
    run: PredictionRun, items: list[dict[str, Any]], *, note: str
) -> dict[str, Any]:
    return {
        "prediction_id": run.prediction_id,
        "status": "completed",
        "case_id": run.case_id,
        "transaction_id": run.transaction_id,
        "model_name": run.model_name,
        "model_version": run.model_version,
        "window": {
            "start": run.window_start.isoformat(),
            "end": run.window_end.isoformat(),
        },
        "confidence": float(run.confidence),
        "confidence_heuristic": "margin",
        "generated_at": run.triggered_at.isoformat(),
        "superseded_at": (
            run.superseded_at.isoformat() if run.superseded_at is not None else None
        ),
        "locations": items,
        "note": note,
    }