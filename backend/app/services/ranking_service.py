from __future__ import annotations

import pandas as pd


class RankingService:
    @staticmethod
    def rank(candidates: pd.DataFrame, scores) -> pd.DataFrame:
        result = candidates[["transaction_id", "atm_id", "candidate_rank"]].copy()
        result["model_score"] = scores

        result = result.sort_values(
            by=["transaction_id", "model_score", "atm_id"],
            ascending=[True, False, True],
            kind="mergesort",
        ).reset_index(drop=True)

        result["predicted_rank"] = (
            result.groupby("transaction_id").cumcount() + 1
        )
        result["risk_score_percent"] = (result["model_score"] * 100.0).round(2)
        return result
