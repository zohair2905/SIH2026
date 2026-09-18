from __future__ import annotations

from typing import Any

from app.db.models import Alert, Case


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