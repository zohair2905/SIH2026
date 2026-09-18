from __future__ import annotations

"""Backward-compatible aliases for the pre-Phase-1 route layout.

These routes delegate to the /api/* handlers and stay until the Phase 5
cutover, when the legacy contract is retired.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api import (
    alerts as api_alerts,
    analytics as api_analytics,
    cases as api_cases,
    heatmap as api_heatmap,
    predictions as api_predictions,
    transactions as api_transactions,
)
from app.db.session import get_session
from app.schemas.alert import AlertStatusUpdate
from app.schemas.case import CaseCreate, CaseStatusUpdate
from app.schemas.prediction import PredictionRequest

router = APIRouter(include_in_schema=False)

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/cases", name="legacy_list_cases")
def _legacy_list_cases(session: SessionDep, status: str | None = None):
    return api_cases.list_cases(status=status, session=session)


@router.post("/cases", name="legacy_create_case")
def _legacy_create_case(request: CaseCreate, session: SessionDep, http: Request):
    return api_cases.create_case(request, session, http)


@router.get("/cases/{case_id}", name="legacy_get_case")
def _legacy_get_case(case_id: str, session: SessionDep):
    return api_cases.get_case(case_id, session)


@router.patch("/cases/{case_id}", name="legacy_update_case")
def _legacy_update_case(
    case_id: str, request: CaseStatusUpdate, session: SessionDep, http: Request
):
    return api_cases.update_case(case_id, request, session, http)


@router.get("/alerts", name="legacy_list_alerts")
def _legacy_list_alerts(
    session: SessionDep,
    status: str | None = None,
    severity: str | None = None,
):
    return api_alerts.list_alerts(status=status, severity=severity, session=session)


@router.get("/alerts/{alert_id}", name="legacy_get_alert")
def _legacy_get_alert(alert_id: int, session: SessionDep):
    return api_alerts.get_alert(alert_id, session)


@router.patch("/alerts/{alert_id}", name="legacy_update_alert")
def _legacy_update_alert(
    alert_id: int, request: AlertStatusUpdate, session: SessionDep, http: Request
):
    return api_alerts.update_alert(alert_id, request, http, session)


@router.get("/heatmap", name="legacy_get_heatmap")
def _legacy_get_heatmap(session: SessionDep, case_id: str | None = None):
    return api_heatmap.get_heatmap(case_id=case_id, session=session)


@router.get("/analytics/summary", name="legacy_analytics_summary")
def _legacy_analytics_summary(session: SessionDep):
    return api_analytics.summary(session)


@router.get("/analytics", name="legacy_analytics")
def _legacy_analytics(session: SessionDep):
    return api_analytics.analytics(session)


@router.post("/cases/{case_id}/predict", name="legacy_predict_case")
def _legacy_predict_case(case_id: str, session: SessionDep, http: Request):
    return api_cases.predict_case(case_id, session, http)


@router.get("/predictions/{prediction_id}", name="legacy_get_prediction")
def _legacy_get_prediction(prediction_id: str, session: SessionDep):
    return api_predictions.get_prediction(prediction_id, session)


@router.get("/transactions/{transaction_id}", name="legacy_get_transaction")
def _legacy_get_transaction(transaction_id: str, session: SessionDep):
    return api_transactions.get_transaction(transaction_id, session=session)


@router.post("/predictions/predict", name="legacy_predict")
def _legacy_predict(
    request: PredictionRequest,
    session: SessionDep,
    http: Request,
    case_id: str | None = None,
):
    return api_predictions.predict(request, session, http, case_id=case_id)