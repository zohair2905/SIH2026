from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    """Minimal identity model. Authentication/authorization arrives in Phase 4."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin','investigator','analyst')", name="role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    badge: Mapped[str | None] = mapped_column(String(32), unique=True)
    name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="investigator"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    assigned_cases: Mapped[list[Case]] = relationship(back_populates="assigned_officer")  # type: ignore[name-defined]


class Case(Base):
    """Case-centered domain model per blueprint 12.1."""

    __tablename__ = "cases"
    __table_args__ = (
        CheckConstraint(
            "case_type IN ('atm_withdrawal','complaint')", name="case_type"
        ),
        CheckConstraint(
            "status IN ('open','investigating','resolved','closed')", name="status"
        ),
        CheckConstraint(
            "priority IN ('low','medium','high','critical')", name="priority"
        ),
        Index("ix_cases_transaction_id", "transaction_id"),
        Index("ix_cases_status", "status"),
        Index("ix_cases_created_at", "created_at"),
    )

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="atm_withdrawal"
    )
    transaction_id: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="open"
    )
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="medium"
    )
    location: Mapped[object | None] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=False)
    )
    assigned_officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    assigned_officer: Mapped[User | None] = relationship(back_populates="assigned_cases")
    complaints: Mapped[list[Complaint]] = relationship(back_populates="case")  # type: ignore[name-defined]
    predictions: Mapped[list[Prediction]] = relationship(  # type: ignore[name-defined]
        back_populates="case"
    )
    alerts: Mapped[list[Alert]] = relationship(back_populates="case")  # type: ignore[name-defined]
    entities: Mapped[list[Entity]] = relationship(  # type: ignore[name-defined]
        secondary="case_entities"
    )


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (Index("ix_complaints_case_id", "case_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    victim_location: Mapped[object | None] = mapped_column(
        Geometry("POINT", srid=4326, spatial_index=False)
    )
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    case: Mapped[Case] = relationship(back_populates="complaints")


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('account','phone','atm','ip')", name="entity_type"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    masked_identifier: Mapped[str | None] = mapped_column(String(255))
    risk_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class CaseEntity(Base):
    __tablename__ = "case_entities"

    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("cases.case_id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("rank BETWEEN 1 AND 5", name="rank"),
        CheckConstraint("risk_score BETWEEN 0 AND 1", name="risk_score"),
        UniqueConstraint("case_id", "rank"),
        Index("ix_predictions_case_id", "case_id"),
        Index("ix_predictions_atm_id", "atm_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[str] = mapped_column(String(32), nullable=False)
    atm_id: Mapped[str] = mapped_column(String(32), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[float] = mapped_column(nullable=False)
    candidate_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float | None] = mapped_column()
    longitude: Mapped[float | None] = mapped_column()
    city: Mapped[str | None] = mapped_column(String(100))
    area_type: Mapped[str | None] = mapped_column(String(64))
    atm_status: Mapped[str | None] = mapped_column(String(32))
    atm_density_1km: Mapped[float | None] = mapped_column()
    atm_withdrawal_count: Mapped[float | None] = mapped_column()
    atm_recent_activity: Mapped[float | None] = mapped_column()
    synthetic_location_data: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    case: Mapped[Case] = relationship(back_populates="predictions")
    alerts: Mapped[list[Alert]] = relationship(back_populates="prediction")  # type: ignore[name-defined]


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint("severity IN ('low','medium','high','critical')", name="severity"),
        CheckConstraint(
            "status IN ('new','acknowledged','dismissed','resolved')", name="status"
        ),
        Index("ix_alerts_case_id", "case_id"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_prediction_id", "prediction_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False
    )
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("predictions.id", ondelete="SET NULL")
    )
    transaction_id: Mapped[str] = mapped_column(String(32), nullable=False)
    atm_id: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_score: Mapped[float] = mapped_column(nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="new"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    case: Mapped[Case] = relationship(back_populates="alerts")
    prediction: Mapped[Prediction] = relationship(back_populates="alerts")