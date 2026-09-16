from fastapi import APIRouter

from app.schemas.prediction import HealthResponse
from app.services.config import MODEL_NAME, MODEL_VERSION
from app.services.model_service import get_model_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    model_service = get_model_service()
    try:
        model_service.load()
        loaded = True
    except Exception:
        loaded = False

    return HealthResponse(
        status="ok" if loaded else "degraded",
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        model_loaded=loaded,
    )
