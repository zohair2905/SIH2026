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

class EvidenceFactor(BaseModel):
    feature: str
    value: float
    label: str

class PredictionEvidence(BaseModel):
    top_factors: list[EvidenceFactor]
    driver: str
    heuristic: bool = True

class PredictionWindow(BaseModel):
    start: str
    end: str

class PredictionItem(BaseModel):
    rank: int
    atm_id: str
    risk_score: float
    risk_score_percent: float
    confidence: float
    severity: str
    candidate_rank: int
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    area_type: str | None = None
    atm_status: str | None = None
    atm_density_1km: float | None = None
    atm_withdrawal_count: float | None = None
    atm_recent_activity: float | None = None
    synthetic_location_data: bool = True
    evidence: PredictionEvidence | None = None

class PredictionResponse(BaseModel):
    transaction_id: str
    model_name: str
    model_version: str
    candidate_count: int
    predictions: list[PredictionItem]
    note: str
    prediction_id: str | None = None
    window: PredictionWindow | None = None

class PredictionRunResponse(BaseModel):
    prediction_id: str
    status: str = "completed"
    case_id: str
    transaction_id: str
    model_name: str
    model_version: str
    window: PredictionWindow
    confidence: float
    confidence_heuristic: str = "margin"
    generated_at: str
    superseded_at: str | None = None
    locations: list[PredictionItem]
    note: str
