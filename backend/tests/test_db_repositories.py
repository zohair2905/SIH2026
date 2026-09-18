from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alert, Prediction
from app.db.repositories import CaseRepository, PredictionRepository


def test_case_create_list_get_update(session: Session) -> None:
    repo = CaseRepository(session)
    created = repo.create(
        case_id="CASE-TEST0001",
        transaction_id="TXN000000294",
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

    assert repo.transaction_ids("CASE-TEST0001") == ["TXN000000294"]
    assert repo.transaction_ids("CASE-NOT-FOUND") == []


def test_prediction_rows_replaced_on_rerun(session: Session) -> None:
    repo = CaseRepository(session)
    pred_repo = PredictionRepository(session)
    repo.create(
        case_id="CASE-TEST0002",
        transaction_id="TXN000000294",
        title="Title",
        description=None,
        priority="medium",
    )
    rows = [
        {
            "atm_id": f"ATM9000{rank}", "rank": rank, "risk_score": 0.5, "candidate_rank": 1,
            "latitude": 18.5, "longitude": 73.8, "city": "Pune", "area_type": "Residential",
            "atm_status": "Active", "atm_density_1km": 100.0,
            "atm_withdrawal_count": 0.0, "atm_recent_activity": 0.0,
        }
        for rank in (1, 2)
    ]
    first = pred_repo.replace_for_case("CASE-TEST0002", "TXN000000294", rows)
    assert len(first) == 2

    second = pred_repo.replace_for_case("CASE-TEST0002", "TXN000000294", rows)
    assert len(second) == 2

    count = session.execute(
        select(func.count()).select_from(Prediction).where(Prediction.case_id == "CASE-TEST0002")
    ).scalar_one()
    assert count == 2  # replaced, not appended


def test_seeded_prediction_ids_link_to_alert(session: Session) -> None:
    from app.seeding import seed_demo

    seed_demo.seed(session)
    case_id = "CASE-E2CAEBEA64"
    preds = session.scalars(
        select(Prediction).where(Prediction.case_id == case_id).order_by(Prediction.rank)
    ).all()
    assert len(preds) == 5
    alert = session.scalars(
        select(Alert).where(Alert.case_id == case_id)
    ).one()
    assert alert.prediction_id == preds[0].id