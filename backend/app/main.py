from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.analytics import router as analytics_router
from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.health import router as health_router
from app.api.heatmap import router as heatmap_router
from app.api.predictions import router as predictions_router
from app.api.transactions import router as transactions_router
from app.database.app_db import get_app_db
from app.services.config import MODEL_VERSION
from app.services.model_service import get_model_service

app = FastAPI(
    title="SIH 26184 - Proactive ATM Withdrawal Intelligence API",
    version=MODEL_VERSION,
    description=(
        "Prototype backend for cases, ATM candidate ranking, alerts, heatmap data and analytics. "
        "The supplied benchmark uses controlled synthetic ATM linkage/location data."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(cases_router)
app.include_router(predictions_router)
app.include_router(alerts_router)
app.include_router(heatmap_router)
app.include_router(analytics_router)

@app.on_event("startup")
def startup_event() -> None:
    get_app_db()
    get_model_service().load()
