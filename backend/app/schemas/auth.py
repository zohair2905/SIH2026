from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=200)


class UserResponse(BaseModel):
    id: int
    badge: str | None = None
    name: str | None = None
    email: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse