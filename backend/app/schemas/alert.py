from __future__ import annotations
from pydantic import BaseModel, Field

class AlertResponse(BaseModel):
    alert_id: int
    case_id: str
    transaction_id: str
    atm_id: str
    risk_score: float
    severity: str
    status: str
    message: str
    created_at: str
    updated_at: str

class AlertStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|acknowledged|dismissed|resolved)$")
