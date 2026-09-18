from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_store
from app.db.repositories import CaseRepository, PredictionRepository
from app.db.session import get_session
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.alert_service import create_prediction_alerts
from app.services.candidate_service import CandidateService
from app.services.config import MODEL_NAME, MODEL_VERSION
from app.services.feature_service import FeatureService
from app.services.model_service import get_model_service
from app.services.ranking_service import RankingService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    session: SessionDep,
    case_id: str | None = None,
):
    store = get_store()
    transaction_service = TransactionService(store)
    candidate_service = CandidateService(store)
    feature_service = FeatureService(store)
    model_service = get_model_service()

    try:
        transaction_service.get_transaction(request.transaction_id)
        candidates = candidate_service.get_five_candidates(request.transaction_id)
        features = feature_service.build_candidate_features(request.transaction_id, candidates)
        scores = model_service.predict(features)
        ranked = RankingService.rank(candidates, scores)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, TypeError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    atms = store.atms().set_index("atm_id", drop=False)
    candidate_lookup = candidates.set_index("atm_id", drop=False)
    predictions = []
    for _, row in ranked.iterrows():
        atm_id = str(row["atm_id"])
        if atm_id not in atms.index or atm_id not in candidate_lookup.index:
            raise HTTPException(status_code=500, detail=f"ATM not found: {atm_id}")
        atm = atms.loc[atm_id]
        cand = candidate_lookup.loc[atm_id]
        predictions.append({
            "rank": int(row["predicted_rank"]),
            "atm_id": atm_id,
            "risk_score": float(row["model_score"]),
            "risk_score_percent": float(row["risk_score_percent"]),
            "candidate_rank": int(row["candidate_rank"]),
            "latitude": float(atm["latitude"]),
            "longitude": float(atm["longitude"]),
            "city": str(atm["city"]) if "city" in atm and atm["city"] == atm["city"] else None,
            "area_type": str(atm["area_type"]) if atm["area_type"] == atm["area_type"] else None,
            "atm_status": str(atm["atm_status"]) if atm["atm_status"] == atm["atm_status"] else None,
            "atm_density_1km": float(atm["atm_density_1km"]) if atm["atm_density_1km"] == atm["atm_density_1km"] else None,
            "atm_withdrawal_count": float(cand["atm_withdrawal_count"]),
            "atm_recent_activity": float(cand["atm_recent_activity"]),
            "synthetic_location_data": str(atm.get("data_source", "")) == "synthetic_expanded",
        })

    if case_id:
        case = CaseRepository(session).get(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")
        if str(case.transaction_id) != str(request.transaction_id):
            raise HTTPException(status_code=400, detail="Case transaction_id does not match prediction transaction_id")
        created = PredictionRepository(session).replace_for_case(
            case_id, request.transaction_id, predictions
        )
        create_prediction_alerts(session, case_id, request.transaction_id, created)

    return PredictionResponse(
        transaction_id=request.transaction_id,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        candidate_count=len(predictions),
        predictions=predictions,
        note=(
            "Prediction uses the pre-generated five-candidate set from the controlled synthetic benchmark. "
            "Risk scores are model probabilities for candidate ranking, not real-world guarantees."
        ),
    )