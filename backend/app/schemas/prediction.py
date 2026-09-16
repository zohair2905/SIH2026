from __future__ import annotations
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    model_name: str
    model_version: str
    model_loaded: bool

class TransactionResponse(BaseModel):
    transaction_id: str
    customer_id: str | None = None
    timestamp: str | None = None
    account_type: str | None = None
    transaction_type: str | None = None
    transaction_amount: float | None = None
    account_balance: float | None = None
    state: str | None = None
    credit_score: float | None = None
    has_loan: int | None = None
    kyc_status: str | None = None
    channel: str | None = None

class PredictionRequest(BaseModel):
    transaction_id: str = Field(..., min_length=1)

class PredictionItem(BaseModel):
    rank: int
    atm_id: str
    risk_score: float
    risk_score_percent: float
    candidate_rank: int
    latitude: float
    longitude: float
    city: str | None = None
    area_type: str | None = None
    atm_status: str | None = None
    atm_density_1km: float | None = None
    atm_withdrawal_count: float | None = None
    atm_recent_activity: float | None = None
    synthetic_location_data: bool = True

class PredictionResponse(BaseModel):
    transaction_id: str
    model_name: str
    model_version: str
    candidate_count: int
    predictions: list[PredictionItem]
    note: str
