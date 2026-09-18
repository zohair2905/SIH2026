from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
ML_DIR = BASE_DIR / "ml"

TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
ATM_FILE = DATA_DIR / "atm_master.csv"
CANDIDATES_FILE = DATA_DIR / "transaction_atm_candidates.csv"
MODEL_FILE = ML_DIR / "rf_baseline_model.joblib"

MODEL_NAME = "Random Forest Baseline"
MODEL_VERSION = "RF_baseline_v1"

# Human-readable, globally unique external prediction identifier.
# <prefix>-<case_id>-<per-case sequence>; the case_id component is unique in
# the cases table and the sequence is unique per case/subject.
PREDICTION_ID_PREFIX = "PRED"

# Deterministic prediction horizon for blueprint 12.1/19 `time_window`.
# A run predicts the ranking state for [triggered_at, triggered_at + window].
PREDICTION_WINDOW_HOURS = 24


def prediction_window(start: datetime) -> tuple[datetime, datetime]:
    end = start + timedelta(hours=PREDICTION_WINDOW_HOURS)
    return (start, end)


# Blueprint 14/17 risk->severity mapping. Applied to the RAW model probability
# (risk_score); it does not replace it.
RISK_SEVERITY_BANDS = [
    ("critical", 0.90),
    ("high", 0.70),
    ("medium", 0.50),
    ("low", 0.0),
]


def severity_for_score(risk_score: float) -> str:
    for severity, floor in RISK_SEVERITY_BANDS:
        if risk_score >= floor:
            return severity
    return "low"


# Blueprint 17: low severity is dashboard-only; medium and above materialise
# as notification/alert rows. This is the alert-creation floor, distinct from
# per-prediction severity (severity exists on every ranked location).
ALERT_RISK_FLOOR = 0.50

NUMERIC_FEATURES = [
    "candidate_rank",
    "latitude",
    "longitude",
    "atm_density_1km",
    "atm_withdrawal_count",
    "atm_withdrawals_1h",
    "atm_withdrawals_24h",
    "atm_fraud_count",
    "atm_fraud_rate",
    "atm_recent_activity",
    "transaction_amount",
    "credit_score",
    "has_loan",
    "emi_amount",
    "hour",
    "day_of_week",
    "is_weekend",
    "time_since_last_transaction",
    "time_since_last_transaction_available",
    "transaction_count_1h",
    "transaction_count_24h",
    "withdrawal_count_1h",
    "withdrawal_count_24h",
    "withdrawal_amount_1h",
    "withdrawal_amount_24h",
    "amount_velocity_1h",
    "amount_velocity_24h",
]

CATEGORICAL_FEATURES = [
    "account_type",
    "merchant_category",
    "state",
    "loan_type",
    "channel",
    "kyc_status",
    "area_type",
    "atm_status",
]

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# These fields are identifiers/output metadata, never model inputs.
NON_MODEL_COLUMNS = {
    "transaction_id",
    "customer_id",
    "atm_id",
    "target",
    "candidate_selection_score",
    "target_generation_score",
    "target_selection_probability",
    "is_fraud",
    "data_source",
    "linkage_type",
    "distance_method",
    "distance_to_atm",
    "distance_from_recent_activity",
    "distance_available",
    "atm_history_available",
    "local_fraud_density",
    "local_fraud_density_available",
    "linked_account_count",
    "suspicious_account_count",
    "network_features_available",
    "transaction_date",
    "transaction_time",
    "transaction_datetime",
    "split",
}
