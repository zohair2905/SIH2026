"""Minimal in-process smoke test. Requires PostgreSQL and the model artifact."""
from fastapi.testclient import TestClient
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.main import app

TRANSACTION_ID = "TXN000000294"

with TestClient(app) as client:
    r = client.get("/health")
    print("GET /health", r.status_code, r.json())
    r = client.get(f"/api/transactions/{TRANSACTION_ID}")
    print("GET /api/transactions", r.status_code)
    payload = {
        "transaction_id": TRANSACTION_ID,
        "title": "Backend smoke-test case",
        "description": "Created by smoke_test_api.py",
        "priority": "high",
    }
    r = client.post("/api/cases", json=payload)
    print("POST /api/cases", r.status_code, r.json())
    case_id = r.json()["case_id"]
    r = client.post(
        f"/api/predictions/predict?case_id={case_id}",
        json={"transaction_id": TRANSACTION_ID},
    )
    print("POST /api/predictions/predict", r.status_code)
    print(r.json())
    r = client.get(f"/api/heatmap?case_id={case_id}")
    print("GET /api/heatmap", r.status_code, r.json())
    r = client.get("/api/alerts")
    print("GET /api/alerts", r.status_code, r.json())
    r = client.get("/api/analytics")
    print("GET /api/analytics", r.status_code)
    print(r.json())