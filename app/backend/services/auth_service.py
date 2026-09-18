"""Authentication business logic (ACRI-66).

Responsibility: password hashing/verification, session lifecycle, and
failed-login attempt recording + rolling-window alerting. No HTTP concerns
here — those live in `routes/auth.py` / `middleware/auth.py`.
"""

from __future__ import annotations

import logging
import os
import secrets
from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import LoginAttempt, User, UserSession

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

FAILED_LOGIN_ALERT_THRESHOLD = int(os.environ.get("FAILED_LOGIN_ALERT_THRESHOLD", "5"))
FAILED_LOGIN_ALERT_WINDOW_MINUTES = int(os.environ.get("FAILED_LOGIN_ALERT_WINDOW_MINUTES", "15"))


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (passlib)."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(password, password_hash)


def verify_credentials(db: Session, email: str, password: str) -> User | None:
    """Look up the user by (lowercased) email and verify the password.

    Returns the `User` on success, `None` on any failure (unknown email or
    wrong password) — callers must return an identical, generic 401 for both
    cases to avoid user/credential enumeration (Assumption A10).
    """
    normalized_email = email.strip().lower()
    user = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User) -> str:
    """Create a new opaque session token for the given user and persist it."""
    token = secrets.token_urlsafe(32)
    session_row = UserSession(token=token, user_id=user.id)
    db.add(session_row)
    db.commit()
    return token


def get_session_user(db: Session, token: str) -> User | None:
    """Resolve a session token to its `User`, or `None` if invalid/unknown."""
    session_row = db.execute(
        select(UserSession).where(UserSession.token == token)
    ).scalar_one_or_none()
    if session_row is None:
        return None
    return db.get(User, session_row.user_id)


def delete_session(db: Session, token: str) -> None:
    """Delete a session row if it exists. Idempotent — safe to call for a
    missing/unknown token (logout is always a 200)."""
    session_row = db.execute(
        select(UserSession).where(UserSession.token == token)
    ).scalar_one_or_none()
    if session_row is not None:
        db.delete(session_row)
        db.commit()


def record_login_attempt(db: Session, email: str, success: bool) -> None:
    """Persist and log a single login attempt (ARCH-020 audit requirement)."""
    normalized_email = email.strip().lower()
    db.add(LoginAttempt(email=normalized_email, success=success))
    db.commit()
    if success:
        logger.info("login_attempt", extra={"email": normalized_email, "success": True})
    else:
        logger.info("login_attempt", extra={"email": normalized_email, "success": False})
        check_failed_login_alert(db, normalized_email)


def check_failed_login_alert(db: Session, email: str) -> None:
    """Log a single structured WARNING if the trailing window's failed-login
    count for this email has reached the configured threshold.

    No lockout/blocked response is enforced — this is alerting only, per the
    task's authorized resolution (mirrors the prior
    `failed_login_alerting_assumption` precedent).
    """
    normalized_email = email.strip().lower()
    window_start = datetime.now(UTC) - timedelta(minutes=FAILED_LOGIN_ALERT_WINDOW_MINUTES)
    attempt_count = db.execute(
        select(func.count())
        .select_from(LoginAttempt)
        .where(
            LoginAttempt.email == normalized_email,
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= window_start,
        )
    ).scalar_one()
    if attempt_count >= FAILED_LOGIN_ALERT_THRESHOLD:
        logger.warning(
            "failed_login_alert",
            extra={
                "email": normalized_email,
                "attempt_count": attempt_count,
                "window_minutes": FAILED_LOGIN_ALERT_WINDOW_MINUTES,
            },
        )
