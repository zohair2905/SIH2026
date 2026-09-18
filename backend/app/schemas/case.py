from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    title: str = Field(default="ATM withdrawal investigation", min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    case_type: str = Field(default="atm_withdrawal", pattern="^(atm_withdrawal|complaint)$")
    amount: Decimal | None = Field(default=None, gt=0)


class CasePredictionSummary(BaseModel):
    """Risk/score of the case's current (non-superseded) run top location.

    Derived from stored predictions only; never fabricated when a case has no
    prediction history.
    """

    prediction_id: str
    risk_score: float
    severity: str
    top_atm_id: str | None = None
    city: str | None = None
    window_end: str | None = None


class CaseResponse(BaseModel):
    case_id: str
    transaction_id: str | None
    title: str
    description: str | None
    status: str
    priority: str
    case_type: str
    amount: float | None
    created_at: str
    updated_at: str
    prediction: CasePredictionSummary | None = None


class CaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|investigating|resolved|closed)$")


class CaseNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=2000)
    actor: str | None = Field(default=None, max_length=100)


class CaseNoteResponse(BaseModel):
    note_id: int
    case_id: str
    actor: str | None
    note: str
    created_at: str


class NetworkNode(BaseModel):
    id: str
    kind: str
    label: str
    details: dict[str, Any] = {}
    risk: str | None = None


class NetworkLink(BaseModel):
    source: str
    target: str
    relation: str


class CaseNetwork(BaseModel):
    case_id: str
    semantics: str
    nodes: list[NetworkNode]
    links: list[NetworkLink]