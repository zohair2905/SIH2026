from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Alert, Case, Prediction, User
from app.seeding import seed_demo


def _counts(session: Session) -> dict[str, int]:
    return {
        "cases": session.execute(select(func.count()).select_from(Case)).scalar_one(),
        "predictions": session.execute(select(func.count()).select_from(Prediction)).scalar_one(),
        "alerts": session.execute(select(func.count()).select_from(Alert)).scalar_one(),
        "users": session.execute(select(func.count()).select_from(User)).scalar_one(),
    }


def test_seed_golden_counts(session: Session) -> None:
    assert seed_demo.seed(session) == {
        "cases": 3,
        "predictions": 5,
        "alerts": 1,
        "users": 3,
    }


def test_seed_is_idempotent(session: Session) -> None:
    seed_demo.seed(session)
    before = _counts(session)
    seed_demo.seed(session)
    assert _counts(session) == before


def test_seed_demo_user_and_alert_link(session: Session) -> None:
    seed_demo.seed(session)
    email = session.execute(
        select(User).where(User.email == seed_demo.DEMO_EMAIL)
    ).scalar_one()
    assert email.role == "investigator"

    alert = session.scalars(select(Alert)).one()
    assert alert.prediction_id is not None