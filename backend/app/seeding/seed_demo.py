"""Deterministic demo seed mirroring the committed smoke state.

Reproduces the same scenario on every run (blueprint 29): 3 cases,
5 predictions, 1 alert, 1 demo investigator. Idempotent: wipes the
operational tables and reloads from the literals below.
"""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Alert, Case, Prediction, PredictionRun, User
from app.services.config import (
    MODEL_NAME,
    MODEL_VERSION,
    PREDICTION_ID_PREFIX,
    prediction_window,
    severity_for_score,
)

DEMO_EMAIL = "a.patil@cic.gov.in"
DEMO_PASSWORD_ENV = "DEMO_PASSWORD"


def _ts(iso: str) -> datetime:
    return datetime.fromisoformat(iso)

USER = {"badge": "A.PATIL", "name": "A. Patil", "email": DEMO_EMAIL, "role": "investigator"}

CASES = [
    {
        "case_id": "CASE-E2CAEBEA64",
        "transaction_id": "TXN000000294",
        "title": "Backend smoke-test case",
        "description": "Created by smoke_test_api.py",
        "status": "open",
        "priority": "high",
        "created_at": _ts("2026-09-15T13:43:18.470942+00:00"),
        "updated_at": _ts("2026-09-15T13:43:18.470942+00:00"),
    },
    {
        "case_id": "CASE-CE38F22859",
        "transaction_id": "TXN000000012",
        "title": "ATM withdrawal investigation",
        "description": "string",
        "status": "open",
        "priority": "medium",
        "created_at": _ts("2026-09-15T13:46:33.783528+00:00"),
        "updated_at": _ts("2026-09-15T13:46:33.783528+00:00"),
    },
    {
        "case_id": "CASE-0BA24F39F5",
        "transaction_id": "TXN000000012",
        "title": "ATM withdrawal investigation",
        "description": "string",
        "status": "open",
        "priority": "medium",
        "created_at": _ts("2026-09-15T13:46:35.562366+00:00"),
        "updated_at": _ts("2026-09-15T13:46:35.562366+00:00"),
    },
]

_SEED_TS = "2026-09-15T13:43:18.773248+00:00"

PREDICTIONS = [
    {"atm_id": "ATM00100", "rank": 1, "risk_score": 0.7266666666666667, "candidate_rank": 3,
     "latitude": 18.499804595640647, "longitude": 73.86368701364972, "city": "Pune",
     "area_type": "Residential", "atm_status": "Active", "atm_density_1km": 939.0,
     "atm_withdrawal_count": 0.0, "atm_recent_activity": 0.0},
    {"atm_id": "ATM09544", "rank": 2, "risk_score": 0.1, "candidate_rank": 5,
     "latitude": 18.525748519268344, "longitude": 73.85708063017397, "city": "Pune",
     "area_type": "Residential", "atm_status": "Active", "atm_density_1km": 833.0,
     "atm_withdrawal_count": 0.0, "atm_recent_activity": 0.0},
    {"atm_id": "ATM00665", "rank": 3, "risk_score": 0.09333333333333334, "candidate_rank": 2,
     "latitude": 18.5054940433128, "longitude": 73.80566046438389, "city": "Pune",
     "area_type": "Residential", "atm_status": "Active", "atm_density_1km": 862.0,
     "atm_withdrawal_count": 0.0, "atm_recent_activity": 0.0},
    {"atm_id": "ATM07825", "rank": 4, "risk_score": 0.07666666666666666, "candidate_rank": 4,
     "latitude": 18.559686594510264, "longitude": 73.88404663866567, "city": "Pune",
     "area_type": "Residential", "atm_status": "Active", "atm_density_1km": 491.0,
     "atm_withdrawal_count": 0.0, "atm_recent_activity": 0.0},
    {"atm_id": "ATM06172", "rank": 5, "risk_score": 0.06333333333333334, "candidate_rank": 1,
     "latitude": 18.512499980836765, "longitude": 73.81174289490555, "city": "Pune",
     "area_type": "Residential", "atm_status": "Active", "atm_density_1km": 557.0,
     "atm_withdrawal_count": 0.0, "atm_recent_activity": 0.0},
]

ALERT = {
    "transaction_id": "TXN000000294",
    "atm_id": "ATM00100",
    "risk_score": 0.7266666666666667,
    "severity": "high",
    "status": "new",
    "message": "HIGH ATM risk for ATM00100 with model score 72.67%.",
    "created_at": _ts("2026-09-15T13:43:18.778158+00:00"),
    "updated_at": _ts("2026-09-15T13:43:18.778158+00:00"),
}


def _truncate(session: Session) -> None:
    session.execute(
        text(
            "TRUNCATE audit_logs, auth_sessions, complaints, case_entities, "
            "case_notes, alerts, predictions, prediction_runs, entities, cases, "
            "users RESTART IDENTITY CASCADE"
        )
    )
    session.commit()


def _demo_user() -> dict:
    password = os.getenv(DEMO_PASSWORD_ENV)
    if not password:
        raise RuntimeError(
            "DEMO_PASSWORD must be set to seed the demo investigator. "
            "See backend/.env.example."
        )
    return {
        **USER,
        "password_hash": hash_password(password),
    }


def seed(session: Session) -> dict[str, int]:
    """Reload the deterministic demo state. Returns row counts."""
    _truncate(session)

    user = User(**_demo_user())
    session.add(user)
    cases = [Case(**row, case_type="atm_withdrawal") for row in CASES]
    session.add_all(cases)
    session.flush()

    window_start, window_end = prediction_window(_ts(_SEED_TS))
    ordered = sorted(PREDICTIONS, key=lambda row: row["rank"])
    run = PredictionRun(
        prediction_id=f"{PREDICTION_ID_PREFIX}-CASE-E2CAEBEA64-1",
        case_id="CASE-E2CAEBEA64",
        transaction_id="TXN000000294",
        seq=1,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=window_start,
        window_end=window_end,
        confidence=max(
            0.0, float(ordered[0]["risk_score"]) - float(ordered[1]["risk_score"])
        ),
        triggered_at=_ts(_SEED_TS),
    )
    session.add(run)
    session.flush()

    prediction_rows = []
    for position, row in enumerate(PREDICTIONS):
        next_score = (
            sorted(PREDICTIONS, key=lambda r: r["rank"])[position + 1]["risk_score"]
            if position + 1 < len(PREDICTIONS)
            else 0.0
        )
        confidence = max(0.0, float(row["risk_score"]) - float(next_score))
        prediction_rows.append(
            Prediction(
                run_id=run.id,
                case_id="CASE-E2CAEBEA64",
                transaction_id="TXN000000294",
                confidence=confidence,
                risk_severity=severity_for_score(float(row["risk_score"])),
                evidence={"top_factors": [], "driver": "Seeded demo state.", "heuristic": True},
                created_at=_ts(_SEED_TS),
                **row,
            )
        )
    session.add_all(prediction_rows)
    session.flush()

    top_prediction = next(p for p in prediction_rows if p.rank == 1)
    session.add(
        Alert(
            case_id="CASE-E2CAEBEA64",
            prediction_id=top_prediction.id,
            **ALERT,
        )
    )
    session.commit()

    return {
        "cases": len(cases),
        "predictions": len(prediction_rows),
        "alerts": 1,
        "users": 1,
    }


if __name__ == "__main__":
    from app.db.session import SessionLocal

    with SessionLocal() as s:
        print(seed(s))