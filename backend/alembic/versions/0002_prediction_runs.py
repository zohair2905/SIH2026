"""Prediction run history: PredictionRun + risk fields on predictions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-18

Every prediction execution persists as a PredictionRun holding the complete
top-K result set. Existing predictions are backfilled into a single run per
case (seq 1) so legacy rows keep the run shape.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.services.config import (
    MODEL_NAME,
    MODEL_VERSION,
    PREDICTION_ID_PREFIX,
    prediction_window,
    severity_for_score,
)

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_LEGACY_EVIDENCE = {
    "top_factors": [],
    "driver": "Legacy prediction row backfilled by migration 0002; no feature-level evidence was recorded at run time.",
    "heuristic": True,
}


def upgrade() -> None:
    op.create_table(
        "prediction_runs",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column("prediction_id", sa.String(64), nullable=False),
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_id", sa.String(32), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("case_id", "seq", name="uq_prediction_runs_case_seq"),
    )
    op.create_unique_constraint(
        "uq_prediction_runs_prediction_id", "prediction_runs", ["prediction_id"]
    )
    op.create_index("ix_prediction_runs_case_id", "prediction_runs", ["case_id"])
    op.create_index(
        "ix_prediction_runs_superseded_at", "prediction_runs", ["superseded_at"]
    )

    op.add_column("predictions", sa.Column("run_id", sa.Integer(), nullable=True))
    op.add_column("predictions", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("predictions", sa.Column("risk_severity", sa.String(16), nullable=True))
    op.add_column(
        "predictions", sa.Column("evidence", postgresql.JSONB(), nullable=True)
    )

    _backfill()

    op.alter_column("predictions", "run_id", nullable=False)
    op.alter_column("predictions", "confidence", nullable=False)
    op.alter_column("predictions", "risk_severity", nullable=False)
    op.alter_column(
        "predictions",
        "evidence",
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )
    op.create_foreign_key(
        "fk_predictions_run_id",
        "predictions",
        "prediction_runs",
        ["run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_predictions_run_rank", "predictions", ["run_id", "rank"]
    )
    op.create_index("ix_predictions_run_id", "predictions", ["run_id"])
    # Explicit SQL: avoids the metadata naming convention doubling the name.
    op.execute(
        "ALTER TABLE predictions ADD CONSTRAINT ck_predictions_risk_severity "
        "CHECK (risk_severity IN ('low','medium','high','critical'))"
    )
    op.drop_constraint("uq_predictions_case_rank", "predictions", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_predictions_case_rank", "predictions", ["case_id", "rank"]
    )
    op.drop_index("ix_predictions_run_id", table_name="predictions")
    op.drop_constraint("uq_predictions_run_rank", "predictions", type_="unique")
    op.drop_constraint("fk_predictions_run_id", "predictions", type_="foreignkey")
    op.execute("ALTER TABLE predictions DROP CONSTRAINT ck_predictions_risk_severity")
    op.alter_column("predictions", "evidence", nullable=True)
    op.alter_column("predictions", "confidence", nullable=True)
    op.alter_column("predictions", "run_id", nullable=True)
    op.drop_column("predictions", "evidence")
    op.drop_column("predictions", "risk_severity")
    op.drop_column("predictions", "confidence")
    op.drop_column("predictions", "run_id")
    op.drop_index("ix_prediction_runs_superseded_at", table_name="prediction_runs")
    op.drop_index("ix_prediction_runs_case_id", table_name="prediction_runs")
    op.drop_table("prediction_runs")


def _backfill() -> None:
    """Group legacy predictions into one PredictionRun per case."""
    conn = op.get_bind()
    groups = conn.execute(
        sa.text(
            "SELECT case_id, transaction_id, MIN(created_at) AS ts "
            "FROM predictions GROUP BY case_id, transaction_id ORDER BY case_id"
        )
    ).mappings()
    for group in groups:
        case_id, transaction_id = group["case_id"], group["transaction_id"]
        triggered = group["ts"] or datetime.now(UTC)
        window_start, window_end = prediction_window(triggered)
        prediction_id = f"{PREDICTION_ID_PREFIX}-{case_id}-1"
        run_id = conn.execute(
            sa.text(
                "INSERT INTO prediction_runs "
                "(prediction_id, case_id, transaction_id, seq, model_name, "
                "model_version, window_start, window_end, confidence, triggered_at) "
                "VALUES (:pid, :cid, :tid, 1, :mn, :mv, :ws, :we, 0.0, :t) "
                "RETURNING id"
            ),
            {
                "pid": prediction_id,
                "cid": case_id,
                "tid": transaction_id,
                "mn": MODEL_NAME,
                "mv": MODEL_VERSION,
                "ws": window_start,
                "we": window_end,
                "t": triggered,
            },
        ).scalar_one()

        rows = conn.execute(
            sa.text(
                "SELECT id, rank, risk_score FROM predictions "
                "WHERE case_id = :cid ORDER BY rank"
            ),
            {"cid": case_id},
        ).mappings()
        ordered = list(rows)
        run_confidence = 0.0
        for index, row in enumerate(ordered):
            next_score = ordered[index + 1]["risk_score"] if index + 1 < len(ordered) else 0.0
            confidence = min(1.0, max(0.0, float(row["risk_score"] - next_score)))
            severity = severity_for_score(float(row["risk_score"]))
            if row["rank"] == 1:
                run_confidence = confidence
            conn.execute(
                sa.text(
                    "UPDATE predictions SET run_id = :rid, confidence = :conf, "
                    "risk_severity = :sev, evidence = :ev WHERE id = :id"
                ),
                {
                    "rid": run_id,
                    "conf": confidence,
                    "sev": severity,
                    "ev": json.dumps(_LEGACY_EVIDENCE),
                    "id": row["id"],
                },
            )
        conn.execute(
            sa.text("UPDATE prediction_runs SET confidence = :c WHERE id = :id"),
            {"c": run_confidence, "id": run_id},
        )