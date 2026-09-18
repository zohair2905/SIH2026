from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_store
from app.db.repositories import AnalyticsRepository
from app.db.session import get_session
from app.schemas.analytics import AnalyticsResponse, AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def summary(session: SessionDep):
    return AnalyticsRepository(session).summary()


@router.get("", response_model=AnalyticsResponse)
def analytics(session: SessionDep):
    return AnalyticsService(AnalyticsRepository(session), get_store()).build()