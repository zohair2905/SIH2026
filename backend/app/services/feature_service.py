from __future__ import annotations
import numpy as np
import pandas as pd
from app.database.database import DataStore
from app.services.config import MODEL_FEATURES

TX_COLUMNS = [
    "transaction_id", "account_type", "transaction_amount", "merchant_category", "state",
    "credit_score", "has_loan", "loan_type", "emi_amount", "channel", "kyc_status", "hour",
    "day_of_week", "is_weekend", "time_since_last_transaction", "time_since_last_transaction_available",
    "transaction_count_1h", "transaction_count_24h", "withdrawal_count_1h", "withdrawal_count_24h",
    "withdrawal_amount_1h", "withdrawal_amount_24h", "amount_velocity_1h", "amount_velocity_24h",
]

ATM_COLUMNS = ["atm_id", "latitude", "longitude", "area_type", "atm_status", "atm_density_1km"]


class FeatureService:
    """Reconstructs the exact 35 raw features used by train_rf_baseline.py."""
    def __init__(self, store: DataStore) -> None:
        self.store = store

    def build_candidate_features(self, transaction_id: str, candidates: pd.DataFrame) -> pd.DataFrame:
        tx = self.store.transactions()
        atms = self.store.atms()
        tx_row = tx.loc[tx["transaction_id"].astype(str) == str(transaction_id)].copy()
        if tx_row.empty:
            raise KeyError(f"Transaction not found: {transaction_id}")
        if len(tx_row) != 1:
            raise ValueError(f"Transaction ID is not unique: {transaction_id}")

        missing_tx = [c for c in TX_COLUMNS if c not in tx_row.columns]
        if missing_tx:
            raise ValueError(f"transactions.csv missing model fields: {missing_tx}")

        merged = candidates.merge(tx_row[TX_COLUMNS], on="transaction_id", how="left", validate="many_to_one")
        missing_atm = [c for c in ATM_COLUMNS if c not in atms.columns]
        if missing_atm:
            raise ValueError(f"atm_master.csv missing fields: {missing_atm}")
        merged = merged.merge(atms[ATM_COLUMNS], on="atm_id", how="left", validate="many_to_one")

        for col in [
            "atm_withdrawal_count", "atm_withdrawals_1h", "atm_withdrawals_24h", "atm_fraud_count",
            "atm_fraud_rate", "atm_recent_activity",
        ]:
            if col not in merged.columns:
                raise ValueError(f"Candidate data missing required feature: {col}")

        for col in MODEL_FEATURES:
            if col in merged.columns and col not in {
                "account_type", "merchant_category", "state", "loan_type", "channel", "kyc_status", "area_type", "atm_status"
            }:
                merged[col] = pd.to_numeric(merged[col], errors="coerce")

        X = merged[MODEL_FEATURES].copy().replace([np.inf, -np.inf], np.nan)
        if X.shape[1] != 35:
            raise RuntimeError(f"Expected 35 raw model features; built {X.shape[1]}")
        return X
