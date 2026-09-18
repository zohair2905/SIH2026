from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.audit_logs import audit_action
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
def update_alert(
    alert_id: int, request: AlertStatusUpdate, http: Request, session: SessionDep
):
    alert = AlertRepository(session).update_status(alert_id, request.status)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    audit_action(
        http,
        session,
        action=f"alert.{request.status}",
        resource_type="alert",
        resource_id=str(alert_id),
        metadata={"status": request.status},
    )
    return to_alert_response(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, http: Request, session: SessionDep):
    user = getattr(http.state, "user", None)
    alert = AlertRepository(session).acknowledge(
        alert_id, acknowledged_by=user.id if user is not None else None
    )
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    audit_action(
        http,
        session,
        action="alert.acknowledged",
        resource_type="alert",
        resource_id=str(alert_id),
    )
    return to_alert_response(alert)