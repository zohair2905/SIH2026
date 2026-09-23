from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.config import (
    ATM_FILE,
    CANDIDATES_FILE,
    TRANSACTIONS_FILE,
)


class DataStore:
    """CSV-backed repository for the SIH 26184 prototype.

    This intentionally uses the supplied static CSVs rather than inventing a
    transactional database layer. It is suitable for the 10,000-transaction
    prototype and can later be replaced with PostgreSQL/PostGIS without
    changing the API/service contracts.
    """

    def __init__(
        self,
        transactions_file: Path = TRANSACTIONS_FILE,
        atm_file: Path = ATM_FILE,
        candidates_file: Path = CANDIDATES_FILE,
    ) -> None:
        self.transactions_file = Path(transactions_file)
        self.atm_file = Path(atm_file)
        self.candidates_file = Path(candidates_file)
        self._validate_files()

    def _validate_files(self) -> None:
        missing = [
            str(p)
            for p in (
                self.transactions_file,
                self.atm_file,
                self.candidates_file,
            )
            if not p.exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing required data file(s): " + ", ".join(missing)
            )

    @lru_cache(maxsize=1)
    def transactions(self) -> pd.DataFrame:
        df = pd.read_csv(self.transactions_file)
        if "transaction_id" not in df.columns:
            raise ValueError("transactions.csv must contain transaction_id")
        return df

    @lru_cache(maxsize=1)
    def atms(self) -> pd.DataFrame:
        df = pd.read_csv(self.atm_file)
        required = {"atm_id", "latitude", "longitude", "area_type", "atm_status", "atm_density_1km"}
        missing = sorted(required - set(df.columns))
        if missing:
            raise ValueError(f"atm_master.csv missing columns: {missing}")
        return df

    @lru_cache(maxsize=1)
    def candidates(self) -> pd.DataFrame:
        df = pd.read_csv(self.candidates_file)
        required = {"transaction_id", "atm_id", "candidate_rank"}
        missing = sorted(required - set(df.columns))
        if missing:
            raise ValueError(
                f"transaction_atm_candidates.csv missing columns: {missing}"
            )
        return df

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        rows = self.transactions()
        match = rows.loc[rows["transaction_id"].astype(str) == str(transaction_id)]
        if match.empty:
            return None
        return match.iloc[0].where(pd.notna(match.iloc[0]), None).to_dict()

    def get_atm(self, atm_id: str) -> dict[str, Any] | None:
        rows = self.atms()
        match = rows.loc[rows["atm_id"].astype(str) == str(atm_id)]
        if match.empty:
            return None
        return match.iloc[0].where(pd.notna(match.iloc[0]), None).to_dict()

    def get_candidates(self, transaction_id: str) -> pd.DataFrame:
        rows = self.candidates()
        match = rows.loc[
            rows["transaction_id"].astype(str) == str(transaction_id)
        ].copy()
        if match.empty:
            return match
        return match.sort_values("candidate_rank").reset_index(drop=True)


_store: DataStore | None = None


def get_store() -> DataStore:
    global _store
    if _store is None:
        _store = DataStore()
    return _store
