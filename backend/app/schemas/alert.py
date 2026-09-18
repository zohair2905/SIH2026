from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: int
    case_id: str
    prediction_id: int
    transaction_id: str
    atm_id: str
    risk_score: float
    severity: str
    status: str
    message: str
    acknowledged_by: int | None = None
    acknowledged_at: str | None = None
    created_at: str
    updated_at: str


class AlertStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|acknowledged|dismissed|resolved)$")