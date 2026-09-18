from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.repositories import AnalyticsRepository
from app.db.session import get_session
from app.schemas.analytics import HeatmapResponse

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=HeatmapResponse)
def get_heatmap(session: SessionDep, case_id: str | None = None):
    points = AnalyticsRepository(session).prediction_heatmap(case_id=case_id)
    return {"case_id": case_id, "points": points}