"""Prediction orchestration over the unchanged ML chain.

transaction -> candidates -> features -> Random Forest -> Top-K ranking,
then risk enrichment and run persistence. A `PredictionRun` is the unit of
one complete top-K execution and holds the full ranked result set.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.database.database import DataStore, get_store
from app.db.models import PredictionRun, utcnow
from app.db.repositories import CaseRepository, PredictionRepository
from app.services.alert_service import create_prediction_alerts
from app.services.candidate_service import CandidateService
from app.services.config import (
    MODEL_NAME,
    MODEL_VERSION,
    prediction_window,
)
from app.services.feature_service import FeatureService
from app.services.model_service import get_model_service
from app.services.ranking_service import RankingService
from app.services.risk_service import RiskService
from app.services.transaction_service import TransactionService


class PredictionService:
    """Builds ranked item payloads and persists prediction runs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def run(self, transaction_id: str) -> dict[str, Any]:
        """Run the ML chain and return the ranked item payload (no side effects)."""
        store: DataStore = get_store()
        TransactionService(store).get_transaction(transaction_id)
        candidates = CandidateService(store).get_five_candidates(transaction_id)
        features = FeatureService(store).build_candidate_features(
            transaction_id, candidates
        )
        scores = get_model_service().predict(features)
        ranked = RankingService.rank(candidates, scores)
        enrichment, run_confidence = RiskService(store).enrich(ranked, features)

        atms = store.atms().set_index("atm_id", drop=False)
        candidate_lookup = candidates.set_index("atm_id", drop=False)
        items: list[dict[str, Any]] = []
        for _, row in ranked.iterrows():
            atm_id = str(row["atm_id"])
            if atm_id not in atms.index or atm_id not in candidate_lookup.index:
                raise RuntimeError(f"ATM not found: {atm_id}")
            atm = atms.loc[atm_id]
            cand = candidate_lookup.loc[atm_id]
            rank = int(row["predicted_rank"])
            enrichment_rank = enrichment[rank]

            def optional(value: Any) -> Any:
                return None if value is None or pd.isna(value) else value

            items.append(
                {
                    "rank": rank,
                    "atm_id": atm_id,
                    "risk_score": enrichment_rank["risk_score"],
                    "risk_score_percent": enrichment_rank["risk_score_percent"],
                    "confidence": enrichment_rank["confidence"],
                    "severity": enrichment_rank["severity"],
                    "evidence": enrichment_rank["evidence"],
                    "candidate_rank": int(row["candidate_rank"]),
                    "latitude": optional(atm["latitude"]),
                    "longitude": optional(atm["longitude"]),
                    "city": optional(atm["city"]) if "city" in atm else None,
                    "area_type": optional(atm["area_type"]),
                    "atm_status": optional(atm["atm_status"]),
                    "atm_density_1km": optional(atm["atm_density_1km"]),
                    "atm_withdrawal_count": float(cand["atm_withdrawal_count"]),
                    "atm_recent_activity": float(cand["atm_recent_activity"]),
                    "synthetic_location_data": (
                        str(atm.get("data_source", "")) == "synthetic_expanded"
                    ),
                }
            )
        return {
            "transaction_id": transaction_id,
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "run_confidence": run_confidence,
            "items": items,
        }

    def persist(self, case_id: str, payload: dict[str, Any]) -> PredictionRun:
        """Persist a prediction run for a case and raise alerts for it."""
        case = CaseRepository(self.session).get(case_id)
        if case is None:
            raise NotFoundError(f"Case not found: {case_id}")
        if case.transaction_id is None:
            raise ValidationError(f"Case has no transaction_id: {case_id}")
        if str(case.transaction_id) != str(payload["transaction_id"]):
            raise AppError(
                "Case transaction_id does not match prediction transaction_id",
                status_code=400,
                code="validation_error",
            )

        now = utcnow()
        window_start, window_end = prediction_window(now)
        run = PredictionRepository(self.session).create_run(
            case_id=case_id,
            transaction_id=payload["transaction_id"],
            model_name=payload["model_name"],
            model_version=payload["model_version"],
            window_start=window_start,
            window_end=window_end,
            confidence=payload["run_confidence"],
            predictions=payload["items"],
        )
        create_prediction_alerts(self.session, run)
        return run