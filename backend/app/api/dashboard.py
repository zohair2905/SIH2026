from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.serializers import to_alert_response
from app.db.repositories import AlertRepository, AnalyticsRepository, PredictionRepository
from app.db.session import get_session
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

SessionDep = Annotated[Session, Depends(get_session)]

_SEVERITY_ORDER = ["critical", "high", "medium", "low"]


@router.get("", response_model=DashboardResponse)
def dashboard(session: SessionDep) -> dict:
    """Operational overview for the investigator dashboard.

    Prediction-derived metrics (predictions, average risk, top ATMs,
    per-case risk distribution) are scoped to the current run only;
    superseded runs never contribute. Alerts include full history.
    """
    analytics = AnalyticsRepository(session)

    summaries = PredictionRepository(session).current_top_summaries()
    case_risk = dict.fromkeys(_SEVERITY_ORDER, 0)
    for summary in summaries.values():
        severity = summary["severity"]
        if severity in case_risk:
            case_risk[severity] += 1

    alert_severity = analytics.alert_severity_distribution()
    return {
        "summary": analytics.summary(),
        "alert_severity_distribution": {
            severity: alert_severity.get(severity, 0)
            for severity in _SEVERITY_ORDER
        },
        "case_risk_distribution": case_risk,
        "top_atms": analytics.prediction_heatmap()[:10],
        "recent_alerts": [
            to_alert_response(a) for a in AlertRepository(session).recent(8)
        ],
    }