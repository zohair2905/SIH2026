from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.repositories import AuditRepository
from app.db.session import get_session
from app.api.serializers import to_audit_response
from app.schemas.audit_log import AuditLogEntry

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

SessionDep = Annotated[Session, Depends(get_session)]


def audit_action(
    request: Request,
    session: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record an audit event using the resolved authenticated actor."""
    user = getattr(request.state, "user", None)
    AuditRepository(session).record(
        user_id=user.id if user is not None else None,
        actor=(user.email if user is not None else None),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata,
        ip_address=(
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else None)
        ),
    )


@router.get("", response_model=list[AuditLogEntry])
def list_audit_logs(session: SessionDep, limit: int = 200):
    """Admin-only; the AuthMiddleware enforces the role gate."""
    return [to_audit_response(entry) for entry in AuditRepository(session).list(limit)]