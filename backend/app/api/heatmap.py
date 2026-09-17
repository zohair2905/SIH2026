from __future__ import annotations
from fastapi import APIRouter
from app.database.app_db import get_app_db
from app.schemas.analytics import HeatmapResponse

router = APIRouter(prefix="/heatmap", tags=["heatmap"])

@router.get("", response_model=HeatmapResponse)
def get_heatmap(case_id: str | None = None):
    points = get_app_db().prediction_heatmap(case_id=case_id)
    return {"case_id": case_id, "points": points}
