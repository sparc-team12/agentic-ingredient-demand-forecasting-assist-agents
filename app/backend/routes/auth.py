"""Authentication HTTP routes (ACRI-66): login, logout, current-user lookup."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE, get_current_user
from schemas.auth import LoginRequest, UserOut
from services.auth_service import (
    create_session,
    delete_session,
    record_login_attempt,
    verify_credentials,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserOut:
    """Authenticate a user and start a new session (AC2/AC3/AC4).

    Returns a generic 401 for both an unknown email and a wrong password —
    no user/credential enumeration (Assumption A10). No cookie/session row
    is created on failure.
    """
    user = verify_credentials(db, payload.email, payload.password)
    if user is None:
        record_login_attempt(db, payload.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    record_login_attempt(db, payload.email, success=True)
    token = create_session(db, user)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
        path="/",
    )
    return UserOut(email=user.email, persona=user.persona)


@router.post("/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Invalidate the current session, if any. Always returns 200 — safe to
    call with no cookie or an already-invalid cookie (idempotent)."""
    if session_token is not None:
        delete_session(db, session_token)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    logger.info("logout")
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the authenticated user's identity, or 401 (session bootstrap)."""
    return UserOut(email=current_user.email, persona=current_user.persona)
