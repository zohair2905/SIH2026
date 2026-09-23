from __future__ import annotations
from pydantic import BaseModel, Field

class CaseCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    title: str = Field(default="ATM withdrawal investigation", min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")

class CaseResponse(BaseModel):
    case_id: str
    transaction_id: str
    title: str
    description: str | None
    status: str
    priority: str
    created_at: str
    updated_at: str

class CaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|investigating|resolved|closed)$")
