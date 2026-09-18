from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.serializers import to_case_response, to_transaction_response
from app.database.database import get_store
from app.db.repositories import CaseRepository
from app.db.session import get_session
from app.schemas.case import CaseCreate, CaseResponse, CaseStatusUpdate
from app.schemas.prediction import TransactionResponse
from app.services.case_service import CaseService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/cases", tags=["cases"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("", response_model=CaseResponse)
def create_case(request: CaseCreate, session: SessionDep):
    try:
        case = CaseService(session, get_store()).create(
            request.transaction_id,
            request.title,
            request.description,
            request.priority,
            request.case_type,
            request.amount,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return to_case_response(case)


@router.get("", response_model=list[CaseResponse])
def list_cases(session: SessionDep, status: str | None = None):
    return [to_case_response(c) for c in CaseRepository(session).list(status)]


@router.get("/{case_id}/transactions", response_model=list[TransactionResponse])
def case_transactions(case_id: str, session: SessionDep):
    transaction_ids = CaseRepository(session).transaction_ids(case_id)
    if not transaction_ids:
        raise HTTPException(status_code=404, detail="Case not found")
    service = TransactionService(get_store())
    try:
        rows = [service.get_transaction(t) for t in transaction_ids]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [to_transaction_response(row) for row in rows]


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, session: SessionDep):
    case = CaseRepository(session).get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return to_case_response(case)


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, request: CaseStatusUpdate, session: SessionDep):
    case = CaseRepository(session).update_status(case_id, request.status)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return to_case_response(case)