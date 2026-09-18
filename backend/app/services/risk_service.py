"""Risk enrichment layered over the unchanged ML ranking pipeline.

Adds per-ranked-location severity (blueprint 14/17), an uncalibrated confidence
heuristic (top-1 vs top-2 score margin, clamped to [0,1]), and a deterministic
rule-based evidence block.

This is heuristic/rule-based explainability, NOT a calibrated local
attribution method such as SHAP. The evidence block is explicitly self-labeled
as such and must never be presented as a causal feature contribution.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

from app.database.database import DataStore, get_store
from app.services.config import MODEL_FEATURES, NUMERIC_FEATURES, severity_for_score
from app.services.model_service import get_model_service

# Positional identifiers, not behavioral signals; excluded from the
# explanatory factor selection.
_NON_EXPLANATORY = {"latitude", "longitude"}

_FEATURE_LABELS = {
    "candidate_rank": "candidate selection position",
    "atm_density_1km": "ATM density within 1 km",
    "atm_withdrawal_count": "ATM cumulative withdrawal activity",
    "atm_withdrawals_1h": "ATM withdrawals in the last hour",
    "atm_withdrawals_24h": "ATM withdrawals in the last 24 hours",
    "atm_fraud_count": "ATM historical fraud count",
    "atm_fraud_rate": "ATM historical fraud rate",
    "atm_recent_activity": "recent ATM activity",
    "transaction_amount": "transaction amount",
    "credit_score": "customer credit score",
    "has_loan": "customer carries a loan",
    "emi_amount": "customer EMI obligation",
    "hour": "hour of day",
    "day_of_week": "day of week",
    "is_weekend": "weekend flag",
    "time_since_last_transaction": "time since the customer's last transaction",
    "time_since_last_transaction_available": "last-transaction history availability",
    "transaction_count_1h": "customer's transactions in the last hour",
    "transaction_count_24h": "customer's transactions in the last 24 hours",
    "withdrawal_count_1h": "customer's withdrawals in the last hour",
    "withdrawal_count_24h": "customer's withdrawals in the last 24 hours",
    "withdrawal_amount_1h": "customer's withdrawal volume (1 h)",
    "withdrawal_amount_24h": "customer's withdrawal volume (24 h)",
    "amount_velocity_1h": "transaction amount velocity (1 h)",
    "amount_velocity_24h": "transaction amount velocity (24 h)",
}


def _as_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if not np.isfinite(result) else result


@lru_cache(maxsize=1)
def _numeric_baseline(store) -> dict[str, tuple[float, float]]:
    """Dataset-level mean/std per numeric feature over the candidate frame.

    Used only to standardize candidate feature values for the heuristic
    explanation; it is a deterministic, data-derived baseline, not a
    calibrated statistical model.
    """
    from app.services.feature_service import ATM_COLUMNS, TX_COLUMNS

    tx = store.transactions()
    atms = store.atms()
    cand = store.candidates()
    merged = cand.merge(
        tx[TX_COLUMNS], on="transaction_id", how="left", validate="many_to_one"
    )
    merged = merged.merge(
        atms[ATM_COLUMNS], on="atm_id", how="left", validate="many_to_one"
    )
    stats: dict[str, tuple[float, float]] = {}
    for feature in NUMERIC_FEATURES:
        series = pd.to_numeric(merged[feature], errors="coerce")
        mean = series.mean()
        std = series.std()
        stats[feature] = (
            0.0 if pd.isna(mean) else float(mean),
            0.0 if pd.isna(std) else float(std),
        )
    return stats


class RiskService:
    """Severity/confidence/evidence enrichment for a ranked candidate frame."""

    def __init__(self, store: DataStore | None = None) -> None:
        self.store = store or get_store()

    def enrich(self, ranked: pd.DataFrame, features: pd.DataFrame) -> tuple[
        dict[int, dict[str, Any]], float
    ]:
        """Return (enrichment-per-rank, run_confidence) for the ranked set.

        `features` must be the 35-feature frame built by FeatureService, whose
        rows align 1:1 (by candidate_rank) with `ranked`.
        """
        feature_records = features.to_dict("records")
        importance = dict(
            zip(MODEL_FEATURES, get_model_service().feature_importances())
        )
        baseline = _numeric_baseline(self.store)

        scores = ranked["model_score"].to_numpy(dtype=float)
        confidences = [
            float(np.clip(s - (scores[i + 1] if i + 1 < len(scores) else 0.0), 0.0, 1.0))
            for i, s in enumerate(scores)
        ]
        run_confidence = confidences[0] if confidences else 0.0

        enrichment: dict[int, dict[str, Any]] = {}
        for i, row in ranked.iterrows():
            rank = int(row["predicted_rank"])
            raw = feature_records[int(row["candidate_rank"]) - 1]
            zscores = {
                feature: (
                    (_as_float(raw[feature]) - baseline[feature][0]) / baseline[feature][1]
                    if baseline[feature][1] > 0
                    else 0.0
                )
                for feature in NUMERIC_FEATURES
            }
            ranked_factors = sorted(
                (
                    (importance.get(feature, 0.0) * abs(zscores[feature]), feature)
                    for feature in NUMERIC_FEATURES
                    if feature not in _NON_EXPLANATORY
                ),
                reverse=True,
            )
            top = ranked_factors[:3]
            top_factors = [
                {
                    "feature": feature,
                    "value": _as_float(raw[feature]),
                    "label": _FEATURE_LABELS.get(feature, feature),
                }
                for _, feature in top
            ]
            driver = (
                "Ranked by top contributing signals: "
                + ", ".join(factor["label"] for factor in top_factors)
                + "."
                if top_factors
                else "No behavioral signals above baseline."
            )
            evidence = {
                "top_factors": top_factors,
                "driver": driver,
                "heuristic": True,
            }
            risk_score = float(row["model_score"])
            enrichment[rank] = {
                "risk_score": risk_score,
                "risk_score_percent": float(row["risk_score_percent"]),
                "severity": severity_for_score(risk_score),
                "confidence": confidences[i],
                "evidence": evidence,
            }
        return enrichment, run_confidence