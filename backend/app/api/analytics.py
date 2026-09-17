from __future__ import annotations
from fastapi import APIRouter
from app.database.app_db import get_app_db
from app.database.database import get_store
from app.schemas.analytics import AnalyticsResponse, AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=AnalyticsSummaryResponse)
def summary():
    return get_app_db().analytics_summary()

@router.get("", response_model=AnalyticsResponse)
def analytics():
    return AnalyticsService(get_app_db(), get_store()).build()
