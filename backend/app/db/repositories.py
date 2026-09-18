from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import Alert, Case, Prediction


class CaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        case_id: str,
        transaction_id: str,
        title: str,
        description: str | None,
        priority: str,
        case_type: str = "atm_withdrawal",
        amount: Any = None,
    ) -> Case:
        case = Case(
            case_id=case_id,
            case_type=case_type,
            transaction_id=transaction_id,
            title=title,
            description=description,
            priority=priority,
            amount=amount,
        )
        self.session.add(case)
        self.session.commit()
        self.session.refresh(case)
        return case

    def get(self, case_id: str) -> Case | None:
        return self.session.get(Case, case_id)

    def list(self, status: str | None = None) -> list[Case]:
        stmt = select(Case).order_by(Case.created_at.desc())
        if status:
            stmt = stmt.where(Case.status == status)
        return list(self.session.scalars(stmt))

    def update_status(self, case_id: str, status: str) -> Case | None:
        case = self.get(case_id)
        if case is None:
            return None
        from app.db.models import utcnow

        case.status = status
        case.updated_at = utcnow()
        self.session.commit()
        self.session.refresh(case)
        return case

    def transaction_ids(self, case_id: str) -> list[str]:
        case = self.get(case_id)
        if case is None or case.transaction_id is None:
            return []
        return [case.transaction_id]


class PredictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_for_case(
        self, case_id: str, transaction_id: str, predictions: list[dict[str, Any]]
    ) -> list[Prediction]:
        """Replace the case's top-K ranking with a fresh prediction run."""
        self.session.execute(delete(Prediction).where(Prediction.case_id == case_id))
        rows = [
            Prediction(
                case_id=case_id,
                transaction_id=transaction_id,
                atm_id=p["atm_id"],
                rank=p["rank"],
                risk_score=float(p["risk_score"]),
                candidate_rank=p["candidate_rank"],
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                city=p.get("city"),
                area_type=p.get("area_type"),
                atm_status=p.get("atm_status"),
                atm_density_1km=p.get("atm_density_1km"),
                atm_withdrawal_count=p.get("atm_withdrawal_count"),
                atm_recent_activity=p.get("atm_recent_activity"),
                synthetic_location_data=bool(p.get("synthetic_location_data", True)),
            )
            for p in predictions
        ]
        self.session.add_all(rows)
        self.session.flush()
        self.session.commit()
        return rows


class AlertRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, entries: list[dict[str, Any]]) -> list[Alert]:
        rows = [Alert(**entry) for entry in entries]
        if rows:
            self.session.add_all(rows)
            self.session.flush()
            self.session.commit()
        return rows

    def get(self, alert_id: int) -> Alert | None:
        return self.session.get(Alert, alert_id)

    def list(self, status: str | None = None, severity: str | None = None) -> list[Alert]:
        stmt = select(Alert).order_by(Alert.risk_score.desc(), Alert.created_at.desc())
        if status:
            stmt = stmt.where(Alert.status == status)
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        return list(self.session.scalars(stmt))

    def update_status(self, alert_id: int, status: str) -> Alert | None:
        alert = self.get(alert_id)
        if alert is None:
            return None
        from app.db.models import utcnow

        alert.status = status
        alert.updated_at = utcnow()
        self.session.commit()
        self.session.refresh(alert)
        return alert

    def acknowledge(self, alert_id: int, acknowledged_by: int | None = None) -> Alert | None:
        alert = self.get(alert_id)
        if alert is None:
            return None
        from app.db.models import utcnow

        alert.status = "acknowledged"
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = utcnow()
        alert.updated_at = utcnow()
        self.session.commit()
        self.session.refresh(alert)
        return alert


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def summary(self) -> dict[str, Any]:
        total_case = select(func.count()).select_from(Case)
        open_case = select(func.count()).select_from(Case).where(Case.status == "open")
        total_alert = select(func.count()).select_from(Alert)
        active_alert = (
            select(func.count())
            .select_from(Alert)
            .where(Alert.status.in_(["new", "acknowledged"]))
        )
        total_pred = select(func.count()).select_from(Prediction)
        avg_risk = select(func.avg(Prediction.risk_score)).select_from(Prediction)
        average_risk = self.session.execute(avg_risk).scalar()
        return {
            "cases": self.session.execute(total_case).scalar_one(),
            "open_cases": self.session.execute(open_case).scalar_one(),
            "alerts": self.session.execute(total_alert).scalar_one(),
            "active_alerts": self.session.execute(active_alert).scalar_one(),
            "predictions": self.session.execute(total_pred).scalar_one(),
            "average_prediction_risk": (
                float(average_risk) if average_risk is not None else None
            ),
        }

    def prediction_heatmap(self, case_id: str | None = None) -> list[dict[str, Any]]:
        stmt = select(
            Prediction.atm_id,
            Prediction.latitude,
            Prediction.longitude,
            func.max(Prediction.risk_score).label("risk_score"),
            func.min(Prediction.rank).label("best_rank"),
            func.count().label("observation_count"),
        )
        if case_id:
            stmt = stmt.where(Prediction.case_id == case_id)
        stmt = (
            stmt.group_by(Prediction.atm_id, Prediction.latitude, Prediction.longitude)
            .order_by(func.max(Prediction.risk_score).desc())
        )
        return [
            {
                "atm_id": row.atm_id,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "risk_score": float(row.risk_score),
                "best_rank": int(row.best_rank),
                "observation_count": int(row.observation_count),
            }
            for row in self.session.execute(stmt)
        ]