from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.audit_logs import audit_action
from app.api.predictions import _items_for_run, raise_http_from, RUN_NOTE
from app.api.serializers import (
    to_case_note_response,
    to_case_response,
    to_prediction_run_response,
    to_transaction_response,
)
from app.core.exceptions import (
    AppError,
    NotFoundError,
    ValidationError,
)
from app.database.database import get_store
from app.db.repositories import CaseNoteRepository, CaseRepository, PredictionRepository
from app.db.session import get_session
from app.schemas.case import (
    CaseCreate,
    CaseNetwork,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseResponse,
    CaseStatusUpdate,
)
from app.schemas.prediction import PredictionRunResponse, TransactionResponse
from app.services.case_service import CaseService
from app.services.prediction_service import PredictionService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/cases", tags=["cases"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("", response_model=CaseResponse)
def create_case(request: CaseCreate, session: SessionDep, http: Request):
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
    audit_action(
        http,
        session,
        action="case.created",
        resource_type="case",
        resource_id=case.case_id,
        metadata={"priority": request.priority, "case_type": request.case_type},
    )
    return to_case_response(case)


@router.get("", response_model=list[CaseResponse])
def list_cases(session: SessionDep, status: str | None = None):
    summaries = PredictionRepository(session).current_top_summaries()
    return [
        to_case_response(c, summaries.get(c.case_id))
        for c in CaseRepository(session).list(status)
    ]


@router.post("/{case_id}/predict", response_model=PredictionRunResponse)
def predict_case(case_id: str, session: SessionDep, http: Request):
    """Run a full top-K prediction for a case (blueprint 19)."""
    case = CaseRepository(session).get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.transaction_id is None:
        raise HTTPException(status_code=422, detail="Case has no transaction_id")

    service = PredictionService(session)
    try:
        payload = service.run(case.transaction_id)
        run = service.persist(case_id, payload)
    except (
        KeyError,
        NotFoundError,
        FileNotFoundError,
        ValidationError,
        AppError,
        ValueError,
        TypeError,
        RuntimeError,
    ) as exc:
        raise_http_from(exc)

    audit_action(
        http,
        session,
        action="prediction.executed",
        resource_type="prediction",
        resource_id=run.prediction_id,
        metadata={"case_id": case_id, "model_name": run.model_name},
    )
    return to_prediction_run_response(
        run, _items_for_run(session, run.id), note=RUN_NOTE
    )


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


@router.get("/{case_id}/network", response_model=CaseNetwork)
def case_network(case_id: str, session: SessionDep):
    """Relationship view built only from the case transaction's real records."""
    case = CaseRepository(session).get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    service = TransactionService(get_store())
    if case.transaction_id is None:
        from app.services.transaction_service import NETWORK_SEMANTICS

        return {
            "case_id": case.case_id,
            "semantics": NETWORK_SEMANTICS,
            "nodes": [],
            "links": [],
        }

    network = service.network_for(case.transaction_id)
    network["case_id"] = case.case_id
    return network


@router.get("/{case_id}/notes", response_model=list[CaseNoteResponse])
def list_case_notes(case_id: str, session: SessionDep):
    if CaseRepository(session).get(case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return [
        to_case_note_response(n)
        for n in CaseNoteRepository(session).list_for(case_id)
    ]


@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
def create_case_note(
    case_id: str, request: CaseNoteCreate, session: SessionDep, http: Request
):
    if CaseRepository(session).get(case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    user = getattr(http.state, "user", None)
    actor_label = user.email if user is not None else None
    actor = request.actor.strip() if request.actor else actor_label
    note = CaseNoteRepository(session).add(case_id, request.note, actor or None)
    audit_action(
        http,
        session,
        action="case.note_created",
        resource_type="case_note",
        resource_id=str(note.id),
        metadata={"case_id": case_id},
    )
    return to_case_note_response(note)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, session: SessionDep):
    case = CaseRepository(session).get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    prediction = PredictionRepository(session).current_top_prediction(case_id)
    return to_case_response(case, prediction)


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str, request: CaseStatusUpdate, session: SessionDep, http: Request
):
    case = CaseRepository(session).update_status(case_id, request.status)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    audit_action(
        http,
        session,
        action="case.status_changed",
        resource_type="case",
        resource_id=case_id,
        metadata={"status": request.status},
    )
    prediction = PredictionRepository(session).current_top_prediction(case_id)
    return to_case_response(case, prediction)