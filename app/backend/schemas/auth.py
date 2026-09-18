"""Pydantic schemas for the authentication HTTP contract (ACRI-66)."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    """Request body for ``POST /auth/login``.

    Email is validated only as a required, non-empty string containing an
    "@" (not full RFC 5322/``EmailStr``) — see Assumption A_email in the
    implementation plan: this avoids introducing the `email-validator`
    dependency for a POC-scale, seed-only user set.
    """

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_must_look_like_an_email(cls, value: str) -> str:
        value = value.strip()
        if not value or "@" not in value:
            raise ValueError("email must be a non-empty string containing '@'")
        return value

    @field_validator("password")
    @classmethod
    def password_must_be_non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("password must not be empty")
        return value


class UserOut(BaseModel):
    """Public-safe representation of an authenticated user.

    Carries `persona` for display/traceability only — never for an access
    decision (AC5: both personas get identical access).
    """

    email: str
    persona: str


class ScreenPlaceholderResponse(BaseModel):
    """Response shape for each of the 4 protected stub screen routes.

    Identical shape for every persona (AC5) — no persona-conditional fields.
    """

    screen: str
    message: str
    user: UserOut
