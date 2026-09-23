from __future__ import annotations
from app.database.app_db import AppDB

HIGH_RISK_THRESHOLD = 0.70

def create_prediction_alerts(db: AppDB, case_id: str, transaction_id: str, predictions: list[dict]) -> list[dict]:
    return db.create_alerts(case_id, transaction_id, predictions, HIGH_RISK_THRESHOLD)
