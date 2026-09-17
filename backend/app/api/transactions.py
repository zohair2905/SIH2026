from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.database.database import get_store
from app.schemas.prediction import TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _timestamp(row: dict[str, Any]) -> str | None:
    date = row.get("transaction_date")
    time = row.get("transaction_time")
    if date is None:
        return None
    text = f"{date} {time}" if time else str(date)
    try:
        return datetime.fromisoformat(text).isoformat()
    except ValueError:
        return text


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str) -> TransactionResponse:
    service = TransactionService(get_store())
    try:
        row = service.get_transaction(transaction_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def as_str(value: Any) -> str | None:
        return None if value is None else str(value)

    return TransactionResponse(
        transaction_id=str(row["transaction_id"]),
        customer_id=as_str(row.get("customer_id")),
        timestamp=_timestamp(row),
        account_type=as_str(row.get("account_type")),
        transaction_type=as_str(row.get("transaction_type")),
        transaction_amount=row.get("transaction_amount"),
        account_balance=row.get("account_balance"),
        state=as_str(row.get("state")),
        credit_score=row.get("credit_score"),
        has_loan=row.get("has_loan"),
        kyc_status=as_str(row.get("kyc_status")),
        channel=as_str(row.get("channel")),
    )
