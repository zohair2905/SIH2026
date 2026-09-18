from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.serializers import to_prediction_item, to_prediction_run_response
from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.db.models import Prediction
from app.db.repositories import PredictionRepository
from app.db.session import get_session
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionRunResponse,
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

SessionDep = Annotated[Session, Depends(get_session)]

RUN_NOTE = (
    "Prediction uses the pre-generated five-candidate set from the controlled "
    "synthetic benchmark. Risk scores are model probabilities for candidate "
    "ranking, not real-world guarantees. Confidence is an uncalibrated "
    "top-1 vs top-2 margin heuristic; evidence is rule-based heuristic "
    "explainability, not SHAP or causal attribution."
)


def raise_http_from(exc: Exception) -> None:
    """Map service exceptions onto the Phase 0 HTTP error envelope."""
    if isinstance(exc, (KeyError, NotFoundError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if isinstance(exc, AppError):
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if isinstance(exc, (ValueError, TypeError, RuntimeError)):
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise exc


def _items_for_run(session: Session, run_id: int) -> list[dict]:
    predictions = session.scalars(
        select(Prediction).where(Prediction.run_id == run_id).order_by(Prediction.rank)
    ).all()
    return [to_prediction_item(p) for p in predictions]


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    session: SessionDep,
    case_id: str | None = None,
):
    """Compatibility-suffixed endpoint; persists a run only when case_id is given."""
    service = PredictionService(session)
    try:
        payload = service.run(request.transaction_id)
        run = service.persist(case_id, payload) if case_id else None
    except (
        KeyError,
        NotFoundError,
        FileNotFoundError,
        ValidationError,
        AppError,
        ValueError,
        TypeError,
        RuntimeError,
    ) as exc:
        raise_http_from(exc)

    return PredictionResponse(
        transaction_id=payload["transaction_id"],
        model_name=payload["model_name"],
        model_version=payload["model_version"],
        candidate_count=len(payload["items"]),
        predictions=payload["items"],
        note=RUN_NOTE,
        prediction_id=run.prediction_id if run else None,
        window=(
            {"start": run.window_start.isoformat(), "end": run.window_end.isoformat()}
            if run
            else None
        ),
    )


@router.get("/{prediction_id}", response_model=PredictionRunResponse)
def get_prediction(prediction_id: str, session: SessionDep):
    run = PredictionRepository(session).get_run(prediction_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return to_prediction_run_response(
        run, _items_for_run(session, run.id), note=RUN_NOTE
    )