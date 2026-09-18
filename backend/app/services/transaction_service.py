from __future__ import annotations

from typing import Any

import pandas as pd

from app.database.database import DataStore

NETWORK_SEMANTICS = (
    "This graph is derived only from the case transaction's real records: the "
    "transaction itself, its account holder (customer_id), the customer's other "
    "transactions in the dataset, and the candidate ATMs recorded for the case "
    "transaction. A transaction-to-ATM edge is a model-derived candidate "
    "withdrawal point, not an established account, criminal or beneficiary "
    "relationship. No edge is drawn where the dataset records no link."
)

_RELATION_BELONGS_TO = "belongs_to"
_RELATION_SAME_CUSTOMER = "same_customer"
_RELATION_CANDIDATE = "candidate_withdrawal_point"


def _clean(value: Any) -> Any:
    """Convert pandas/NumPy scalars to JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


class TransactionService:
    def __init__(self, store: DataStore) -> None:
        self.store = store

    def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        transaction = self.store.get_transaction(transaction_id)
        if transaction is None:
            raise KeyError(f"Transaction not found: {transaction_id}")
        return transaction

    def customer_transactions(self, customer_id: str) -> list[dict[str, Any]]:
        rows = self.store.transactions()
        match = rows.loc[rows["customer_id"].astype(str) == str(customer_id)]
        return [
            {key: _clean(value) for key, value in row.items()}
            for _, row in match.iterrows()
        ]

    def _transaction_node(self, row: dict[str, Any]) -> dict[str, Any]:
        date = row.get("transaction_date")
        time = row.get("transaction_time")
        timestamp = f"{date} {time}" if date and time else date
        return {
            "id": str(row["transaction_id"]),
            "kind": "transaction",
            "label": f"Transaction {row['transaction_id']}",
            "details": {
                "transaction_id": str(row["transaction_id"]),
                "customer_id": _clean(row.get("customer_id")),
                "timestamp": _clean(timestamp),
                "amount": _clean(row.get("transaction_amount")),
                "channel": _clean(row.get("channel")),
                "transaction_type": _clean(row.get("transaction_type")),
                "state": _clean(row.get("state")),
            },
            "risk": None,
        }

    def network_for(self, transaction_id: str) -> dict[str, Any]:
        """Build the honest case network around one real transaction."""
        transaction = self.get_transaction(transaction_id)
        nodes: list[dict[str, Any]] = [self._transaction_node(transaction)]
        links: list[dict[str, Any]] = []

        customer_id = _clean(transaction.get("customer_id"))
        if customer_id is not None:
            customer_node_id = f"customer:{customer_id}"
            nodes.append(
                {
                    "id": customer_node_id,
                    "kind": "customer",
                    "label": f"Customer {customer_id}",
                    "details": {"customer_id": customer_id},
                    "risk": None,
                }
            )
            links.append(
                {
                    "source": customer_node_id,
                    "target": str(transaction["transaction_id"]),
                    "relation": _RELATION_BELONGS_TO,
                }
            )
            for other in self.customer_transactions(customer_id):
                other_id = str(other["transaction_id"])
                if other_id == str(transaction_id):
                    continue
                nodes.append(self._transaction_node(other))
                links.append(
                    {
                        "source": customer_node_id,
                        "target": other_id,
                        "relation": _RELATION_SAME_CUSTOMER,
                    }
                )

        candidates = self.store.get_candidates(transaction_id)
        for _, candidate in candidates.iterrows():
            atm_id = str(candidate["atm_id"])
            atm = self.store.get_atm(atm_id) or {}
            nodes.append(
                {
                    "id": atm_id,
                    "kind": "atm",
                    "label": f"{atm.get('atm_name') or atm_id} ({atm_id})",
                    "details": {
                        "atm_id": atm_id,
                        "candidate_rank": _clean(candidate.get("candidate_rank")),
                        "candidate_selection_score": _clean(
                            candidate.get("candidate_selection_score")
                        ),
                        "distance_to_atm": _clean(candidate.get("distance_to_atm")),
                        "linked_account_count": _clean(
                            candidate.get("linked_account_count")
                        ),
                        "suspicious_account_count": _clean(
                            candidate.get("suspicious_account_count")
                        ),
                        "city": _clean(atm.get("city")),
                        "area_type": _clean(atm.get("area_type")),
                        "latitude": _clean(atm.get("latitude")),
                        "longitude": _clean(atm.get("longitude")),
                    },
                    "risk": None,
                }
            )
            links.append(
                {
                    "source": str(transaction["transaction_id"]),
                    "target": atm_id,
                    "relation": _RELATION_CANDIDATE,
                }
            )

        return {
            "case_id": None,
            "semantics": NETWORK_SEMANTICS,
            "nodes": nodes,
            "links": links,
        }