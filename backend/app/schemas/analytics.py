from __future__ import annotations
from typing import Any
from pydantic import BaseModel

class AnalyticsSummaryResponse(BaseModel):
    cases: int
    open_cases: int
    alerts: int
    active_alerts: int
    predictions: int
    average_prediction_risk: float | None

class HeatmapPoint(BaseModel):
    atm_id: str
    latitude: float
    longitude: float
    risk_score: float
    best_rank: int
    observation_count: int

class HeatmapResponse(BaseModel):
    case_id: str | None
    points: list[HeatmapPoint]

class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummaryResponse
    top_atms: list[dict[str, Any]]
    area_distribution: list[dict[str, Any]]
    transaction_distribution: list[dict[str, Any]]
