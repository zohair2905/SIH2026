from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.serializers import to_alert_response
from app.db.repositories import AlertRepository
from app.db.session import get_session
from app.schemas.alert import AlertResponse, AlertStatusUpdate

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    session: SessionDep,
    status: str | None = None,
    severity: str | None = None,
):
    return [
        to_alert_response(a)
        for a in AlertRepository(session).list(status=status, severity=severity)
    ]


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, session: SessionDep):
    alert = AlertRepository(session).get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return to_alert_response(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, request: AlertStatusUpdate, session: SessionDep):
    alert = AlertRepository(session).update_status(alert_id, request.status)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return to_alert_response(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, session: SessionDep):
    alert = AlertRepository(session).acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return to_alert_response(alert)