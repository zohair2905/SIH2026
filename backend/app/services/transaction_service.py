from __future__ import annotations

from typing import Any

from app.database.database import DataStore


class TransactionService:
    def __init__(self, store: DataStore) -> None:
        self.store = store

    def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        transaction = self.store.get_transaction(transaction_id)
        if transaction is None:
            raise KeyError(f"Transaction not found: {transaction_id}")
        return transaction
