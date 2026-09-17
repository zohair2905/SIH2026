from __future__ import annotations
from collections import Counter
import pandas as pd
from app.database.app_db import AppDB
from app.database.database import DataStore

class AnalyticsService:
    def __init__(self, app_db: AppDB, store: DataStore) -> None:
        self.app_db = app_db
        self.store = store

    def build(self) -> dict:
        summary = self.app_db.analytics_summary()
        predictions = pd.DataFrame(self.app_db.prediction_heatmap())
        top_atms = predictions.head(10).to_dict(orient="records") if not predictions.empty else []

        tx = self.store.transactions().copy()
        tx_dist = []
        if "hour" in tx.columns:
            counts = tx.groupby("hour").size().reset_index(name="count").sort_values("hour")
            tx_dist = counts.to_dict(orient="records")

        area_dist = []
        atm = self.store.atms().copy()
        if "area_type" in atm.columns:
            area_dist = (
                atm.groupby("area_type").size().reset_index(name="atm_count")
                .sort_values("atm_count", ascending=False)
                .to_dict(orient="records")
            )

        return {
            "summary": summary,
            "top_atms": top_atms,
            "area_distribution": area_dist,
            "transaction_distribution": tx_dist,
        }
