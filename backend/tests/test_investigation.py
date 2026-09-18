"""Phase 4 investigation workspace: cases, network, notes and risk derivation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.database import get_store
from app.db.models import Case
from app.db.repositories import PredictionRepository
from app.seeding import seed_demo
from app.services.config import (
    MODEL_NAME,
    MODEL_VERSION,
    prediction_window,
)

CASE_ID = "CASE-E2CAEBEA64"
TXN_ID = "TXN000000294"

SEVERITIES = {"low", "medium", "high", "critical"}
RELATIONS = {"belongs_to", "same_customer", "candidate_withdrawal_point"}


def _five_items() -> list[dict]:
    scores = [0.70, 0.60, 0.50, 0.40, 0.30]
    return [
        {
            "atm_id": f"ATM0910{r}",
            "rank": r,
            "risk_score": scores[r - 1],
            "risk_severity": {
                0.70: "high",
                0.60: "medium",
                0.50: "medium",
                0.40: "low",
                0.30: "low",
            }[scores[r - 1]],
            "confidence": 0.10,
            "evidence": {"top_factors": [], "driver": "sequence test", "heuristic": True},
            "candidate_rank": r,
            "latitude": 18.5,
            "longitude": 73.8,
            "city": "Pune",
            "area_type": "Residential",
            "atm_status": "Active",
            "atm_density_1km": 900.0,
            "atm_withdrawal_count": 0.0,
            "atm_recent_activity": 0.0,
            "synthetic_location_data": True,
        }
        for r in range(1, 6)
    ]


def _persist_run(session: Session, case_id: str):
    start, end = prediction_window(datetime.now(UTC))
    return PredictionRepository(session).create_run(
        case_id=case_id,
        transaction_id=TXN_ID,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=start,
        window_end=end,
        confidence=0.10,
        predictions=_five_items(),
    )


def test_case_list_derives_current_prediction(session: Session, client: TestClient) -> None:
    seed_demo.seed(session)
    rows = client.get("/api/cases").json()
    by_id = {row["case_id"]: row for row in rows}

    seeded = by_id[CASE_ID]
    assert seeded["prediction"] is not None
    assert seeded["prediction"]["prediction_id"] == "PRED-CASE-E2CAEBEA64-1"
    assert seeded["prediction"]["risk_score"] == pytest.approx(0.7266666666666667)
    assert seeded["prediction"]["severity"] == "high"
    assert seeded["prediction"]["top_atm_id"] == "ATM00100"

    # Cases with transactions but no run honestly report no prediction.
    assert by_id["CASE-CE38F22859"]["prediction"] is None


def test_case_detail_and_status_update(session: Session, client: TestClient) -> None:
    seed_demo.seed(session)
    detail = client.get(f"/api/cases/{CASE_ID}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["transaction_id"] == TXN_ID
    assert body["prediction"]["prediction_id"] == "PRED-CASE-E2CAEBEA64-1"

    updated = client.patch(f"/api/cases/{CASE_ID}", json={"status": "investigating"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "investigating"
    assert updated.json()["prediction"] is not None

    assert (
        client.patch(f"/api/cases/{CASE_ID}", json={"status": "bogus"}).status_code
        == 422
    )
    assert (
        client.patch("/api/cases/CASE-UNKNOWN", json={"status": "open"}).status_code
        == 404
    )
    seed_demo.seed(session)


def test_transactions_are_real_case_transaction(session: Session, client: TestClient) -> None:
    seed_demo.seed(session)
    response = client.get(f"/api/cases/{CASE_ID}/transactions")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["transaction_id"] == TXN_ID
    assert rows[0]["customer_id"] == "CUST054241"
    assert client.get("/api/cases/CASE-UNKNOWN/transactions").status_code == 404


def test_network_contract_and_correctness(session: Session, client: TestClient) -> None:
    seed_demo.seed(session)
    response = client.get(f"/api/cases/{CASE_ID}/network")
    assert response.status_code == 200
    body = response.json()

    assert body["case_id"] == CASE_ID
    assert body["semantics"]

    kinds = {node["kind"] for node in body["nodes"]}
    assert {"transaction", "customer", "atm"} <= kinds
    assert {link["relation"] for link in body["links"]} <= RELATIONS

    # Nodes are the real transaction, its real customer and the real candidates.
    customer_nodes = [n for n in body["nodes"] if n["kind"] == "customer"]
    assert customer_nodes and customer_nodes[0]["id"] == "customer:CUST054241"

    expected_atms = {
        str(value) for value in get_store().get_candidates(TXN_ID)["atm_id"]
    }
    atm_nodes = {n["id"] for n in body["nodes"] if n["kind"] == "atm"}
    assert atm_nodes == expected_atms

    candidate_links = [
        link for link in body["links"] if link["relation"] == "candidate_withdrawal_point"
    ]
    assert {link["target"] for link in candidate_links} == expected_atms

    # Candidate counts are exposed as attributes, never elevated to findings.
    for node in body["nodes"]:
        if node["kind"] == "atm":
            assert "linked_account_count" in node["details"]
            assert "suspicious_account_count" in node["details"]
            assert node["risk"] is None

    # Every edge references a real node; no invented account-to-account edges.
    ids = {node["id"] for node in body["nodes"]}
    for link in body["links"]:
        assert link["source"] in ids and link["target"] in ids
        assert not (link["source"].startswith("customer:") and link["target"].startswith("customer:"))

    assert client.get("/api/cases/CASE-UNKNOWN/network").status_code == 404


def test_network_empty_when_case_has_no_transaction(
    session: Session, client: TestClient
) -> None:
    seed_demo.seed(session)
    session.add(
        Case(
            case_id="CASE-NO-TXN",
            case_type="complaint",
            transaction_id=None,
            title="Complaint without linked transaction",
            priority="medium",
        )
    )
    session.commit()

    response = client.get("/api/cases/CASE-NO-TXN/network")
    assert response.status_code == 200
    body = response.json()
    assert body["nodes"] == []
    assert body["links"] == []
    assert body["semantics"]
    # No notes exist until an investigator records one.
    assert client.get("/api/cases/CASE-NO-TXN/notes").json() == []
    seed_demo.seed(session)


def test_notes_get_post_and_validation(session: Session, client: TestClient) -> None:
    seed_demo.seed(session)
    assert client.get(f"/api/cases/{CASE_ID}/notes").json() == []

    created = client.post(
        f"/api/cases/{CASE_ID}/notes",
        json={"note": "Initial triage complete.", "actor": "A. Patil"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["case_id"] == CASE_ID
    assert body["actor"] == "A. Patil"
    assert body["note"] == "Initial triage complete."
    assert body["created_at"]

    client.post(f"/api/cases/{CASE_ID}/notes", json={"note": "Requested ATM logs."})
    rows = client.get(f"/api/cases/{CASE_ID}/notes").json()
    assert len(rows) == 2
    assert rows[0]["note"] == "Requested ATM logs."  # newest first
    assert rows[1]["actor"] == "A. Patil"

    assert (
        client.post(f"/api/cases/{CASE_ID}/notes", json={"note": ""}).status_code == 422
    )
    assert (
        client.post("/api/cases/CASE-UNKNOWN/notes", json={"note": "x"}).status_code
        == 404
    )
    assert client.get("/api/cases/CASE-UNKNOWN/notes").status_code == 404
    seed_demo.seed(session)


def test_new_prediction_becomes_current_and_history_is_preserved(
    session: Session, client: TestClient
) -> None:
    seed_demo.seed(session)
    before = client.get(f"/api/cases/{CASE_ID}").json()["prediction"]
    assert before["prediction_id"] == "PRED-CASE-E2CAEBEA64-1"

    run_b = _persist_run(session, CASE_ID)
    session.expire_all()

    after = client.get(f"/api/cases/{CASE_ID}").json()["prediction"]
    assert after["prediction_id"] == run_b.prediction_id
    assert after["risk_score"] == pytest.approx(0.70)
    assert after["severity"] == "high"
    assert after["top_atm_id"] == "ATM09101"

    # The historical run remains reachable and listed.
    assert client.get("/api/predictions/PRED-CASE-E2CAEBEA64-1").status_code == 200
    assert PredictionRepository(session).list_runs(CASE_ID) and {
        run.prediction_id for run in PredictionRepository(session).list_runs(CASE_ID)
    } == {"PRED-CASE-E2CAEBEA64-1", run_b.prediction_id}

    seed_demo.seed(session)