from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.serializers import to_user_response
from app.core.config import settings
from app.core.middleware import current_user
from app.core.security import verify_password
from app.db.models import User
from app.db.repositories import AuditRepository, AuthRepository, UserRepository
from app.db.session import get_session
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _read_token(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return request.cookies.get(settings.session_cookie_name)


def _set_session_cookie(response: JSONResponse, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        max_age=settings.token_ttl_hours * 3600,
        samesite="lax",
        secure=settings.secure_cookies,
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, http: Request, session: SessionDep):
    ip = _client_ip(http)
    user = UserRepository(session).by_email(request.email)
    if user is None or request.password == "" or not verify_password(
        request.password, user.password_hash
    ):
        AuditRepository(session).record(
            actor=request.email,
            action="auth.login_failed",
            resource_type="user",
            metadata={"reason": "invalid_credentials"},
            ip_address=ip,
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = AuthRepository(session, ttl_hours=settings.token_ttl_hours).create_session(
        user.id, ip_address=ip
    )
    AuditRepository(session).record(
        user_id=user.id,
        actor=user.email,
        action="auth.login_succeeded",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip,
    )

    response = JSONResponse(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": to_user_response(user),
        }
    )
    _set_session_cookie(response, token)
    return response


@router.post("/logout")
def logout(http: Request, session: SessionDep):
    token = _read_token(http)
    auth = AuthRepository(session, ttl_hours=settings.token_ttl_hours)
    user = auth.user_for_token(token) if token else None
    if token:
        auth.revoke(token)
    AuditRepository(session).record(
        user_id=user.id if user is not None else None,
        actor=user.email if user is not None else None,
        action="auth.logout",
        resource_type="user",
        resource_id=str(user.id) if user is not None else None,
        ip_address=_client_ip(http),
    )
    response = JSONResponse({"ok": True})
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(current_user)]):
    return to_user_response(user)