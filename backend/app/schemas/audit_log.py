from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: int
    user_id: int | None = None
    actor: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] = {}
    ip_address: str | None = None
    created_at: str