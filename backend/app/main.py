from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.analytics import router as analytics_router
from app.api.audit_logs import router as audit_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.compat import router as compat_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.heatmap import router as heatmap_router
from app.api.predictions import router as predictions_router
from app.api.transactions import router as transactions_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import AuthMiddleware, RequestIDMiddleware
from app.db.session import check_database
from app.services.config import MODEL_VERSION
from app.services.model_service import get_model_service

configure_logging(settings.log_level)
log = get_logger("main")

app = FastAPI(
    title="SIH 26184 - Proactive ATM Withdrawal Intelligence API",
    version=MODEL_VERSION,
    description=(
        "Prototype backend for cases, ATM candidate ranking, alerts, heatmap data and analytics. "
        "The supplied benchmark uses controlled synthetic ATM linkage/location data."
    ),
)

# Starlette builds the stack outside-in from the last added middleware:
# CORSMiddleware (outermost) -> RequestIDMiddleware -> AuthMiddleware (innermost),
# so every response, including Auth's 401/403 short-circuits, carries a
# request_id and CORS headers.
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(cases_router)
app.include_router(predictions_router)
app.include_router(alerts_router)
app.include_router(heatmap_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)
app.include_router(audit_router)
app.include_router(compat_router)

register_exception_handlers(app)


@app.on_event("startup")
def startup_event() -> None:
    try:
        check_database()
    except Exception:
        log.exception("Application database unreachable; API running without persistence.")
    try:
        get_model_service().load()
    except Exception:
        log.exception("Model artifact unavailable; API running without ML inference.")
