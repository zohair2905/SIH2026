from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import Alert, Case, Prediction, PredictionRun, utcnow
from app.services.config import PREDICTION_ID_PREFIX


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

    def _next_seq(self, case_id: str) -> int:
        max_seq = self.session.execute(
            select(func.max(PredictionRun.seq)).where(PredictionRun.case_id == case_id)
        ).scalar()
        return (max_seq or 0) + 1

    def create_run(
        self,
        *,
        case_id: str,
        transaction_id: str,
        model_name: str,
        model_version: str,
        window_start: Any,
        window_end: Any,
        confidence: float,
        predictions: list[dict[str, Any]],
    ) -> PredictionRun:
        """Persist one complete top-K run.

        Re-prediction appends a new run and supersedes the previous one;
        historical runs, prediction rows and alerts are never deleted.
        """
        seq = self._next_seq(case_id)
        run = PredictionRun(
            prediction_id=f"{PREDICTION_ID_PREFIX}-{case_id}-{seq}",
            case_id=case_id,
            transaction_id=transaction_id,
            seq=seq,
            model_name=model_name,
            model_version=model_version,
            window_start=window_start,
            window_end=window_end,
            confidence=confidence,
            triggered_at=window_start,
        )
        self.session.add(run)
        self.session.flush()

        for p in predictions:
            self.session.add(
                Prediction(
                    run_id=run.id,
                    case_id=case_id,
                    transaction_id=transaction_id,
                    atm_id=p["atm_id"],
                    rank=p["rank"],
                    risk_score=float(p["risk_score"]),
                    risk_severity=p.get("risk_severity") or p.get("severity"),
                    confidence=float(p["confidence"]),
                    evidence=p["evidence"],
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
            )

        previous = select(PredictionRun.id).where(
            PredictionRun.case_id == case_id,
            PredictionRun.superseded_at.is_(None),
            PredictionRun.id != run.id,
        )
        self.session.execute(
            update(PredictionRun)
            .where(PredictionRun.id.in_(previous))
            .values(superseded_at=utcnow())
        )
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_run(self, prediction_id: str) -> PredictionRun | None:
        return self.session.scalar(
            select(PredictionRun).where(PredictionRun.prediction_id == prediction_id)
        )

    def current_run(self, case_id: str) -> PredictionRun | None:
        return self.session.scalar(
            select(PredictionRun)
            .where(
                PredictionRun.case_id == case_id,
                PredictionRun.superseded_at.is_(None),
            )
            .order_by(PredictionRun.triggered_at.desc(), PredictionRun.id.desc())
            .limit(1)
        )

    def list_runs(self, case_id: str | None = None) -> list[PredictionRun]:
        stmt = select(PredictionRun).order_by(
            PredictionRun.triggered_at.desc(), PredictionRun.id.desc()
        )
        if case_id:
            stmt = stmt.where(PredictionRun.case_id == case_id)
        return list(self.session.scalars(stmt))


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
        current_runs = (
            select(PredictionRun.id).where(PredictionRun.superseded_at.is_(None)).subquery()
        )
        scoped_pred = (
            select(func.count())
            .select_from(Prediction)
            .join(current_runs, Prediction.run_id == current_runs.c.id)
        )
        avg_risk = (
            select(func.avg(Prediction.risk_score))
            .select_from(Prediction)
            .join(current_runs, Prediction.run_id == current_runs.c.id)
        )
        average_risk = self.session.execute(avg_risk).scalar()
        return {
            "cases": self.session.execute(total_case).scalar_one(),
            "open_cases": self.session.execute(open_case).scalar_one(),
            "alerts": self.session.execute(total_alert).scalar_one(),
            "active_alerts": self.session.execute(active_alert).scalar_one(),
            "predictions": self.session.execute(scoped_pred).scalar_one(),
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
        ).join(
            PredictionRun, Prediction.run_id == PredictionRun.id
        ).where(PredictionRun.superseded_at.is_(None))
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