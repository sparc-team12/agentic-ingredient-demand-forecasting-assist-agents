"""Failed-login alerting: 5 failed attempts for the same email inside the
rolling window emit exactly one WARNING log record; 4 attempts emit none.

No lockout/blocked response is asserted — this is alerting-only, per the
task's authorized resolution (implementation-plan.md §6/§12 A5)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from db.models import LoginAttempt
from tests.conftest import KITCHEN_MANAGER_EMAIL, KITCHEN_MANAGER_PASSWORD, seed_known_users


def _fail_login(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_four_failed_attempts_emit_no_warning(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    seed_known_users(db_session)

    with caplog.at_level(logging.WARNING, logger="services.auth_service"):
        for _ in range(4):
            _fail_login(client)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


def test_fifth_failed_attempt_in_window_emits_exactly_one_warning(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    seed_known_users(db_session)

    with caplog.at_level(logging.WARNING, logger="services.auth_service"):
        for _ in range(5):
            _fail_login(client)

    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and r.getMessage() == "failed_login_alert"
    ]
    assert len(warnings) == 1


def test_login_is_never_blocked_even_after_the_alert_threshold(
    client: TestClient, db_session: Session
) -> None:
    """No lockout: a correct login still succeeds after 5+ prior failures."""
    seed_known_users(db_session)
    for _ in range(6):
        _fail_login(client)

    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )
    assert response.status_code == 200


def test_sixth_consecutive_failed_attempt_also_emits_a_warning(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    """Boundary above the threshold: alerting is not a one-time latch that
    arms once and then goes silent. Per `check_failed_login_alert`, every
    attempt whose trailing-window count is >= the threshold logs its own
    WARNING (5th and 6th each qualify) — this documents the actual,
    tech-lead-approved per-attempt semantics rather than a
    fire-once-per-breach semantic, and would catch an accidental change to
    "alert only once" or "stop counting after the threshold"."""
    seed_known_users(db_session)

    with caplog.at_level(logging.WARNING, logger="services.auth_service"):
        for _ in range(6):
            _fail_login(client)

    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and r.getMessage() == "failed_login_alert"
    ]
    assert len(warnings) == 2


def test_failed_attempts_outside_the_rolling_window_do_not_count_towards_the_alert(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    """Window-expiry boundary: 4 failed attempts older than the 15-minute
    rolling window (`FAILED_LOGIN_ALERT_WINDOW_MINUTES`) must not be summed
    with a new failure to reach the threshold — only in-window attempts
    count."""
    seed_known_users(db_session)

    stale_time = datetime.now(UTC) - timedelta(minutes=20)
    for _ in range(4):
        db_session.add(
            LoginAttempt(email=KITCHEN_MANAGER_EMAIL, success=False, created_at=stale_time)
        )
    db_session.commit()

    with caplog.at_level(logging.WARNING, logger="services.auth_service"):
        _fail_login(client)  # only the 1st in-window failure

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


def test_a_stale_attempt_plus_five_fresh_ones_still_alerts_on_the_fresh_fifth(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    """Complements the window-expiry boundary above: a stale (out-of-window)
    failure must not suppress alerting either — 5 fresh, in-window failures
    must still cross the threshold and alert exactly once, regardless of
    older, expired history for the same email."""
    seed_known_users(db_session)

    stale_time = datetime.now(UTC) - timedelta(minutes=20)
    db_session.add(LoginAttempt(email=KITCHEN_MANAGER_EMAIL, success=False, created_at=stale_time))
    db_session.commit()

    with caplog.at_level(logging.WARNING, logger="services.auth_service"):
        for _ in range(5):
            _fail_login(client)

    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and r.getMessage() == "failed_login_alert"
    ]
    assert len(warnings) == 1
