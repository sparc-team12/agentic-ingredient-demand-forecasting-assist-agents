"""Session-cookie authentication dependency (ACRI-66).

Responsibility: read the `session_token` cookie, validate it against
`user_sessions`, and either return the authenticated `User` or raise a
generic 401. This dependency is the single authentication gate reused by
`GET /auth/me` and all 4 protected `/screens/*` routes (AC1/AC5) — it makes
an authentication-only decision, with no persona-based branching.
"""

from __future__ import annotations

import os

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from services.auth_service import get_session_user

SESSION_COOKIE_NAME = "session_token"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: resolve the current authenticated user from the
    session cookie, or raise `401 Not authenticated`."""
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_session_user(db, session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
