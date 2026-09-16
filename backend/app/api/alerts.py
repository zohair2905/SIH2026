from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.database.app_db import get_app_db
from app.schemas.alert import AlertResponse, AlertStatusUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=list[AlertResponse])
def list_alerts(status: str | None = None, severity: str | None = None):
    return get_app_db().list_alerts(status=status, severity=severity)

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int):
    row = get_app_db().get_alert(alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return row

@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, request: AlertStatusUpdate):
    row = get_app_db().update_alert_status(alert_id, request.status)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return row
