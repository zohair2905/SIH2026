from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    title: str = Field(default="ATM withdrawal investigation", min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    case_type: str = Field(default="atm_withdrawal", pattern="^(atm_withdrawal|complaint)$")
    amount: Decimal | None = Field(default=None, gt=0)


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


class CaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|investigating|resolved|closed)$")