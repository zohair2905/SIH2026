from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.security import generate_token, token_digest
from app.db.models import (
    Alert,
    AuditLog,
    AuthSession,
    Case,
    CaseNote,
    Prediction,
    PredictionRun,
    User,
    utcnow,
)
from app.services.config import PREDICTION_ID_PREFIX, severity_for_score


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


class CaseNoteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, case_id: str, note: str, actor: str | None) -> CaseNote:
        row = CaseNote(case_id=case_id, note=note, actor=actor)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_for(self, case_id: str) -> list[CaseNote]:
        stmt = (
            select(CaseNote)
            .where(CaseNote.case_id == case_id)
            .order_by(CaseNote.created_at.desc(), CaseNote.id.desc())
        )
        return list(self.session.scalars(stmt))


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

    # --- Investigation helpers ---------------------------------------------------

    def current_top_prediction(self, case_id: str) -> dict[str, Any] | None:
        """Return the highest-ranked prediction of the current run, or None."""
        run = self.current_run(case_id)
        if run is None:
            return None
        top = self.session.scalar(
            select(Prediction)
            .where(Prediction.run_id == run.id)
            .order_by(Prediction.rank)
            .limit(1)
        )
        if top is None:
            return None
        return {
            "prediction_id": run.prediction_id,
            "risk_score": float(top.risk_score),
            "severity": severity_for_score(float(top.risk_score)),
            "top_atm_id": top.atm_id,
            "city": top.city,
            "window_end": run.window_end.isoformat() if run.window_end else None,
        }

    def current_top_summaries(self) -> dict[str, dict[str, Any]]:
        """Case-id → top-1 current-run prediction summary across all cases."""
        rn = (
            select(
                Prediction.case_id,
                Prediction.atm_id,
                Prediction.risk_score,
                Prediction.city,
                PredictionRun.prediction_id,
                PredictionRun.window_end,
                func.row_number()
                .over(
                    partition_by=Prediction.case_id,
                    order_by=(Prediction.rank.asc(), Prediction.risk_score.desc()),
                )
                .label("rn"),
            )
            .join(PredictionRun, Prediction.run_id == PredictionRun.id)
            .where(PredictionRun.superseded_at.is_(None))
            .subquery()
        )
        rows = self.session.execute(select(rn).where(rn.c.rn == 1)).all()
        return {
            row.case_id: {
                "prediction_id": row.prediction_id,
                "risk_score": float(row.risk_score),
                "severity": severity_for_score(float(row.risk_score)),
                "top_atm_id": row.atm_id,
                "city": row.city,
                "window_end": row.window_end.isoformat() if row.window_end else None,
            }
            for row in rows
        }


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

    def recent(self, limit: int = 8) -> list[Alert]:
        stmt = (
            select(Alert)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit)
        )
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
        unacknowledged = (
            select(func.count()).select_from(Alert).where(Alert.status == "new")
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
            "unacknowledged_alerts": self.session.execute(unacknowledged).scalar_one(),
            "predictions": self.session.execute(scoped_pred).scalar_one(),
            "average_prediction_risk": (
                float(average_risk) if average_risk is not None else None
            ),
        }

    def alert_severity_distribution(self) -> dict[str, int]:
        """Alert counts grouped by severity; absent severities default to zero."""
        counts = dict.fromkeys(["critical", "high", "medium", "low"], 0)
        rows = self.session.execute(
            select(Alert.severity, func.count()).group_by(Alert.severity)
        ).all()
        for severity, count in rows:
            if severity in counts:
                counts[severity] = int(count)
        return counts

    def prediction_heatmap(self, case_id: str | None = None) -> list[dict[str, Any]]:
        """Heatmap points aggregated across current (non-superseded) runs.

        Each point is one ATM cluster (atm_id + coordinates) in the newest
        current run. The point carries the highest-risk observation's score,
        rank, confidence and stored evidence, plus the observation count from
        the run that owns it. Historical/superseded runs never contribute.
        """
        ranked = (
            select(
                Prediction.atm_id,
                Prediction.latitude,
                Prediction.longitude,
                Prediction.risk_score,
                Prediction.rank.label("best_rank"),
                Prediction.confidence,
                Prediction.evidence,
                Prediction.area_type,
                Prediction.synthetic_location_data,
                PredictionRun.window_start,
                PredictionRun.window_end,
                func.row_number()
                .over(
                    partition_by=(
                        Prediction.atm_id,
                        Prediction.latitude,
                        Prediction.longitude,
                    ),
                    order_by=Prediction.risk_score.desc(),
                )
                .label("rn"),
                func.count()
                .over(
                    partition_by=(
                        Prediction.atm_id,
                        Prediction.latitude,
                        Prediction.longitude,
                    )
                )
                .label("observation_count"),
            )
            .join(PredictionRun, Prediction.run_id == PredictionRun.id)
            .where(PredictionRun.superseded_at.is_(None))
        )
        if case_id:
            ranked = ranked.where(Prediction.case_id == case_id)
        ranked = ranked.subquery()

        rows = self.session.execute(
            select(ranked)
            .where(ranked.c.rn == 1)
            .order_by(ranked.c.risk_score.desc())
        )
        return [
            {
                "atm_id": row.atm_id,
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "risk_score": float(row.risk_score),
                "best_rank": int(row.best_rank),
                "observation_count": int(row.observation_count),
                "severity": severity_for_score(float(row.risk_score)),
                "confidence": float(row.confidence),
                "top_factors": (row.evidence or {}).get("top_factors", []),
                "area_type": row.area_type,
                "window_start": (
                    row.window_start.isoformat()
                    if row.window_start is not None
                    else None
                ),
                "window_end": (
                    row.window_end.isoformat() if row.window_end is not None else None
                ),
                "synthetic_location_data": bool(row.synthetic_location_data),
            }
            for row in rows
        ]

class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User).where(func.lower(User.email) == email.strip().lower())
        )

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)


class AuthRepository:
    def __init__(self, session: Session, ttl_hours: int = 12) -> None:
        self.session = session
        self.ttl_hours = ttl_hours

    def create_session(
        self, user_id: int, *, ip_address: str | None = None
    ) -> str:
        from datetime import timedelta

        token = generate_token()
        self.session.add(
            AuthSession(
                user_id=user_id,
                token_hash=token_digest(token),
                ip_address=ip_address,
                expires_at=utcnow() + timedelta(hours=self.ttl_hours),
            )
        )
        self.session.commit()
        return token

    def user_for_token(self, token: str) -> User | None:
        session_row = self.session.scalar(
            select(AuthSession).where(AuthSession.token_hash == token_digest(token))
        )
        if session_row is None:
            return None
        if session_row.revoked_at is not None:
            return None
        if session_row.expires_at is not None and session_row.expires_at <= utcnow():
            return None
        return self.session.scalar(
            select(User).where(
                User.id == session_row.user_id, User.is_active.is_(True)
            )
        )

    def revoke(self, token: str) -> None:
        session_row = self.session.scalar(
            select(AuthSession).where(AuthSession.token_hash == token_digest(token))
        )
        if session_row is not None and session_row.revoked_at is None:
            session_row.revoked_at = utcnow()
            self.session.commit()


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        user_id: int | None = None,
        actor: str | None = None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        row = AuditLog(
            user_id=user_id,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=metadata or {},
            ip_address=ip_address,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list(self, limit: int = 200) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(
            AuditLog.created_at.desc(), AuditLog.id.desc()
        )
        stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def count(self) -> int:
        return int(
            self.session.execute(
                select(func.count()).select_from(AuditLog)
            ).scalar_one()
        )
