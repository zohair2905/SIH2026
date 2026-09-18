"""Initial schema for the case-centered domain model.

Revision ID: 0001
Revises:
Create Date: 2026-09-18
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("badge", sa.String(32), unique=True),
        sa.Column("name", sa.String(100)),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "role",
            sa.String(32),
            server_default="investigator",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "role IN ('admin','investigator','analyst')", name="ck_users_role"
        ),
    )

    op.create_table(
        "cases",
        sa.Column("case_id", sa.String(64), primary_key=True),
        sa.Column(
            "case_type",
            sa.String(32),
            server_default="atm_withdrawal",
            nullable=False,
        ),
        sa.Column("transaction_id", sa.String(32)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("amount", sa.Numeric(14, 2)),
        sa.Column(
            "status", sa.String(16), server_default="open", nullable=False
        ),
        sa.Column(
            "priority", sa.String(16), server_default="medium", nullable=False
        ),
        sa.Column("location", Geometry("POINT", srid=4326)),
        sa.Column("assigned_officer_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "case_type IN ('atm_withdrawal','complaint')", name="ck_cases_case_type"
        ),
        sa.CheckConstraint(
            "status IN ('open','investigating','resolved','closed')",
            name="ck_cases_status",
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high','critical')", name="ck_cases_priority"
        ),
    )
    op.create_index("ix_cases_transaction_id", "cases", ["transaction_id"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_created_at", "cases", ["created_at"])
    op.create_index(
        "ix_cases_location", "cases", ["location"], postgresql_using="gist"
    )

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(64)),
        sa.Column("description", sa.Text()),
        sa.Column("victim_location", Geometry("POINT", srid=4326)),
        sa.Column("reported_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(64)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_complaints_case_id", "complaints", ["case_id"])
    op.create_index(
        "ix_complaints_victim_location",
        "complaints",
        ["victim_location"],
        postgresql_using="gist",
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("masked_identifier", sa.String(255)),
        sa.Column("risk_metadata", sa.dialects.postgresql.JSONB()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "entity_type IN ('account','phone','atm','ip')",
            name="ck_entities_entity_type",
        ),
    )

    op.create_table(
        "case_entities",
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "entity_id",
            sa.Integer(),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_id", sa.String(32), nullable=False),
        sa.Column("atm_id", sa.String(32), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("candidate_rank", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("city", sa.String(100)),
        sa.Column("area_type", sa.String(64)),
        sa.Column("atm_status", sa.String(32)),
        sa.Column("atm_density_1km", sa.Float()),
        sa.Column("atm_withdrawal_count", sa.Float()),
        sa.Column("atm_recent_activity", sa.Float()),
        sa.Column(
            "synthetic_location_data",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("rank BETWEEN 1 AND 5", name="ck_predictions_rank"),
        sa.CheckConstraint(
            "risk_score BETWEEN 0 AND 1", name="ck_predictions_risk_score"
        ),
        sa.UniqueConstraint("case_id", "rank", name="uq_predictions_case_rank"),
    )
    op.create_index("ix_predictions_case_id", "predictions", ["case_id"])
    op.create_index("ix_predictions_atm_id", "predictions", ["atm_id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "prediction_id",
            sa.Integer(),
            sa.ForeignKey("predictions.id", ondelete="SET NULL"),
        ),
        sa.Column("transaction_id", sa.String(32), nullable=False),
        sa.Column("atm_id", sa.String(32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), server_default="new", nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "severity IN ('low','medium','high','critical')", name="ck_alerts_severity"
        ),
        sa.CheckConstraint(
            "status IN ('new','acknowledged','dismissed','resolved')",
            name="ck_alerts_status",
        ),
    )
    op.create_index("ix_alerts_case_id", "alerts", ["case_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_prediction_id", "alerts", ["prediction_id"])


def downgrade() -> None:
    op.drop_index("ix_alerts_prediction_id", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_case_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_predictions_atm_id", table_name="predictions")
    op.drop_index("ix_predictions_case_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_table("case_entities")
    op.drop_table("entities")
    op.drop_index("ix_complaints_victim_location", table_name="complaints")
    op.drop_index("ix_complaints_case_id", table_name="complaints")
    op.drop_table("complaints")
    op.drop_index("ix_cases_location", table_name="cases")
    op.drop_index("ix_cases_created_at", table_name="cases")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_index("ix_cases_transaction_id", table_name="cases")
    op.drop_table("cases")
    op.drop_table("users")