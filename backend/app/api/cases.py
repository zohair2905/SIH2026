from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.database.app_db import get_app_db
from app.database.database import get_store
from app.schemas.case import CaseCreate, CaseResponse, CaseStatusUpdate
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("", response_model=CaseResponse)
def create_case(request: CaseCreate):
    try:
        return CaseService(get_app_db(), get_store()).create(
            request.transaction_id, request.title, request.description, request.priority
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("", response_model=list[CaseResponse])
def list_cases(status: str | None = None):
    return get_app_db().list_cases(status)

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str):
    case = get_app_db().get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, request: CaseStatusUpdate):
    updated = get_app_db().update_case_status(case_id, request.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return updated
