from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.database.database import DataStore
from app.db.models import Case
from app.db.repositories import CaseRepository


class CaseService:
    def __init__(self, session: Session, data_store: DataStore) -> None:
        self.session = session
        self.data_store = data_store

    def create(
        self,
        transaction_id: str,
        title: str,
        description: str | None,
        priority: str,
        case_type: str = "atm_withdrawal",
        amount=None,
    ) -> Case:
        if self.data_store.get_transaction(transaction_id) is None:
            raise KeyError(f"Transaction not found: {transaction_id}")
        case_id = f"CASE-{uuid.uuid4().hex[:10].upper()}"
        return CaseRepository(self.session).create(
            case_id=case_id,
            transaction_id=transaction_id,
            title=title,
            description=description,
            priority=priority,
            case_type=case_type,
            amount=amount,
        )