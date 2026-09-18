"""Investigator notes attached to cases: the case_notes table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-18

Append-only free-form case notes (blueprint FR 8 "Record investigator
notes/actions"). Actor is the caller's identity when an authenticated
session provides one, else null.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "case_notes",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor", sa.String(100)),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_case_notes_case_id", table_name="case_notes")
    op.drop_table("case_notes")