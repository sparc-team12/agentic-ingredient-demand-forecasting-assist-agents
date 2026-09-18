"""`POST /auth/logout` behavior: invalidates the session; idempotent."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import KITCHEN_MANAGER_EMAIL, KITCHEN_MANAGER_PASSWORD, seed_known_users


def test_logout_invalidates_the_session_cookie(client: TestClient, db_session: Session) -> None:
    seed_known_users(db_session)
    client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "ok"}

    screen_response = client.get("/screens/risk-dashboard")
    assert screen_response.status_code == 401


def test_logout_without_any_cookie_is_a_safe_no_op(client: TestClient) -> None:
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_logout_with_an_already_invalid_cookie_still_returns_200(client: TestClient) -> None:
    client.cookies.set("session_token", "not-a-real-session-token")
    response = client.post("/auth/logout")
    assert response.status_code == 200
