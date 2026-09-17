from __future__ import annotations

import pandas as pd

from app.database.database import DataStore


class CandidateService:
    """Provides the controlled candidate set used by the trained baseline.

    The current public/sanitized project data already contains five candidates
    per transaction. The backend therefore reuses those candidates exactly;
    it does not invent a different candidate-generation algorithm at inference.

    For a production deployment with unseen transactions, replace this service
    with the same candidate-generation logic used to build the training data.
    """

    def __init__(self, store: DataStore) -> None:
        self.store = store

    def get_five_candidates(self, transaction_id: str) -> pd.DataFrame:
        candidates = self.store.get_candidates(transaction_id)
        if candidates.empty:
            raise KeyError(
                f"No pre-generated ATM candidates found for transaction: {transaction_id}"
            )

        if len(candidates) != 5:
            raise ValueError(
                f"Expected exactly 5 candidates for {transaction_id}; found {len(candidates)}"
            )

        if candidates["atm_id"].duplicated().any():
            raise ValueError(
                f"Duplicate ATM candidates found for transaction: {transaction_id}"
            )

        expected_ranks = [1, 2, 3, 4, 5]
        actual_ranks = sorted(candidates["candidate_rank"].astype(int).tolist())
        if actual_ranks != expected_ranks:
            raise ValueError(
                f"Expected candidate_rank 1..5 for {transaction_id}; found {actual_ranks}"
            )

        return candidates
