"""Authentication sessions and the security audit trail.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-18

Phase 6: opaque bearer-token sessions (digest-only storage) and an
append-only audit log for login, case, prediction, alert and note actions.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(255)))

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("actor", sa.String(255)),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(64)),
        sa.Column(
            "details",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index(
        "ix_audit_logs_resource_type", "audit_logs", ["resource_type"]
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_column("users", "password_hash")