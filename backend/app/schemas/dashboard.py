from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.alert import AlertResponse


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class DashboardSummary(BaseModel):
    cases: int
    open_cases: int
    alerts: int
    active_alerts: int
    unacknowledged_alerts: int
    predictions: int
    average_prediction_risk: float | None


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    alert_severity_distribution: SeverityCounts
    case_risk_distribution: SeverityCounts
    top_atms: list[dict[str, Any]]
    recent_alerts: list[AlertResponse]