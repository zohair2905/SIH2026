from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.serializers import to_transaction_response
from app.database.database import get_store
from app.db.session import get_session
from app.schemas.prediction import TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, session: SessionDep):
    service = TransactionService(get_store())
    try:
        row = service.get_transaction(transaction_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return to_transaction_response(row)