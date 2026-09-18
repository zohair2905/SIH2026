from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.logging import get_logger, request_id_var
from app.db.models import User
from app.db.repositories import AuthRepository
from app.db.session import SessionLocal

log = get_logger("middleware")

_PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/api/auth/login", "/api/auth/logout"}

_OPERATOR_ROLES = {"investigator", "admin"}
_ADMIN_ROLES = {"admin"}


def _role_required(path: str, method: str) -> str | None:
    """Normalized-path RBAC. Compat (non-/api) paths normalize to /cases etc."""
    normalized = path.removeprefix("/api")
    if method.lower() == "get" and normalized.startswith("/audit-logs"):
        return "admin"
    if method.lower() in {"post", "patch", "put", "delete"}:
        if normalized.startswith(("/cases", "/alerts")):
            return "operator"
        if normalized.startswith("/predictions/predict"):
            return "operator"
    return None


def _envelope(status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": detail},
            "detail": detail,
            "request_id": request_id_var.get() or "-",
        },
    )


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        response: Response | None = None
        try:
            response = await call_next(request)
        finally:
            log.info(
                "request method=%s path=%s status=%s",
                request.method,
                request.url.path,
                getattr(response, "status_code", "?"),
            )
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


def _read_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip() or None
    return request.cookies.get(settings.session_cookie_name)


class AuthMiddleware(BaseHTTPMiddleware):
    """Single auth choke point: every request except /health, /docs and the
    auth endpoints requires a valid session -> 401, and privileged paths are
    role-checked -> 403. The resolved user is exposed on request.state.user.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        role_required: str | None = None
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)
        role_required = _role_required(request.url.path, request.method)

        token = _read_token(request)
        if not token:
            return _envelope(401, "authentication_required", "Authentication required")

        with SessionLocal() as session:
            user: User | None = AuthRepository(session).user_for_token(token)
            if user is None:
                return _envelope(401, "invalid_token", "Invalid or expired session")

            if role_required == "operator" and user.role not in _OPERATOR_ROLES:
                return _envelope(403, "forbidden", "Insufficient permissions")
            if role_required == "admin" and user.role not in _ADMIN_ROLES:
                return _envelope(403, "forbidden", "Insufficient permissions")

            request.state.user = user
            return await call_next(request)


def current_user(request: Request) -> User:
    """FastAPI dependency: the authenticated user, or a 401."""
    user: Any = getattr(request.state, "user", None)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Authentication required")
    return user