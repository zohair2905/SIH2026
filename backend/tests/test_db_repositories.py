from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alert, Prediction, PredictionRun
from app.db.repositories import CaseRepository, PredictionRepository
from app.services.config import MODEL_NAME, MODEL_VERSION, prediction_window

_TX = "TXN000000294"


def _items(n: int) -> list[dict]:
    return [
        {
            "atm_id": f"ATM9000{rank}",
            "rank": rank,
            "risk_score": round(0.9 - rank * 0.05, 4),
            "risk_severity": "high",
            "confidence": 0.05,
            "evidence": {"top_factors": [], "driver": "test", "heuristic": True},
            "candidate_rank": 1,
            "latitude": 18.5,
            "longitude": 73.8,
            "city": "Pune",
            "area_type": "Residential",
            "atm_status": "Active",
            "atm_density_1km": 100.0,
            "atm_withdrawal_count": 0.0,
            "atm_recent_activity": 0.0,
        }
        for rank in range(1, n + 1)
    ]


def _new_run(pred_repo: PredictionRepository, case_id: str, n: int) -> PredictionRun:
    start, end = prediction_window(datetime.now(UTC))
    return pred_repo.create_run(
        case_id=case_id,
        transaction_id=_TX,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        window_start=start,
        window_end=end,
        confidence=0.4,
        predictions=_items(n),
    )


def test_case_create_list_get_update(session: Session) -> None:
    repo = CaseRepository(session)
    created = repo.create(
        case_id="CASE-TEST0001",
        transaction_id=_TX,
        title="Title",
        description="Description",
        priority="high",
    )
    assert created.case_id == "CASE-TEST0001"
    assert repo.get("CASE-TEST0001") is not None
    assert len(repo.list()) == 4  # 3 seeded + 1
    assert repo.list(status="open")

    updated = repo.update_status("CASE-TEST0001", "investigating")
    assert updated is not None
    assert updated.status == "investigating"

    assert repo.transaction_ids("CASE-TEST0001") == [_TX]
    assert repo.transaction_ids("CASE-NOT-FOUND") == []


def test_rerun_appends_runs_and_supersedes_previous(session: Session) -> None:
    repo = CaseRepository(session)
    pred_repo = PredictionRepository(session)
    repo.create(
        case_id="CASE-TEST0002",
        transaction_id=_TX,
        title="Title",
        description=None,
        priority="medium",
    )
    first = _new_run(pred_repo, "CASE-TEST0002", 2)
    second = _new_run(pred_repo, "CASE-TEST0002", 2)

    assert first.prediction_id == "PRED-CASE-TEST0002-1"
    assert second.prediction_id == "PRED-CASE-TEST0002-2"
    assert second.seq == 2

    count = session.execute(
        select(func.count()).select_from(Prediction).where(Prediction.case_id == "CASE-TEST0002")
    ).scalar_one()
    assert count == 4  # both runs retained; history is never deleted

    current = pred_repo.current_run("CASE-TEST0002")
    assert current is not None
    assert current.id == second.id
    assert first.superseded_at is not None
    assert second.superseded_at is None

    runs = pred_repo.list_runs("CASE-TEST0002")
    assert [r.prediction_id for r in runs] == [
        second.prediction_id,
        first.prediction_id,
    ]


def test_prediction_runs_globally_unique_ids(session: Session) -> None:
    case_repo = CaseRepository(session)
    pred_repo = PredictionRepository(session)
    for cid in ("CASE-UNIQUE1", "CASE-UNIQUE2"):
        case_repo.create(
            case_id=cid,
            transaction_id=_TX,
            title="Title",
            description=None,
            priority="low",
        )
    a = _new_run(pred_repo, "CASE-UNIQUE1", 1)
    b = _new_run(pred_repo, "CASE-UNIQUE2", 1)
    c = _new_run(pred_repo, "CASE-UNIQUE1", 1)
    assert len({a.prediction_id, b.prediction_id, c.prediction_id}) == 3
    assert pred_repo.get_run(b.prediction_id) is not None
    assert pred_repo.get_run("PRED-UNKNOWN-0") is None


def test_seeded_prediction_ids_link_to_alert(session: Session) -> None:
    from app.seeding import seed_demo

    seed_demo.seed(session)
    case_id = "CASE-E2CAEBEA64"
    run = PredictionRepository(session).current_run(case_id)
    assert run is not None
    preds = session.scalars(
        select(Prediction).where(Prediction.case_id == case_id).order_by(Prediction.rank)
    ).all()
    assert len(preds) == 5
    assert all(p.run_id == run.id for p in preds)
    alert = session.scalars(
        select(Alert).where(Alert.case_id == case_id)
    ).one()
    assert alert.prediction_id == preds[0].id