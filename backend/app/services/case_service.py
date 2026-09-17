from __future__ import annotations
import uuid
from app.database.app_db import AppDB
from app.database.database import DataStore

class CaseService:
    def __init__(self, app_db: AppDB, data_store: DataStore) -> None:
        self.app_db = app_db
        self.data_store = data_store

    def create(self, transaction_id: str, title: str, description: str | None, priority: str) -> dict:
        if self.data_store.get_transaction(transaction_id) is None:
            raise KeyError(f"Transaction not found: {transaction_id}")
        case_id = f"CASE-{uuid.uuid4().hex[:10].upper()}"
        return self.app_db.create_case(case_id, transaction_id, title, description, priority)
