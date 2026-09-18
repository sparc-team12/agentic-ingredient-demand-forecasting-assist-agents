"""`POST /auth/login` behavior: AC2 (valid credentials), AC3 (invalid
credentials), AC4 (each persona has its own distinct credential set)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import (
    FB_MANAGER_EMAIL,
    FB_MANAGER_PASSWORD,
    KITCHEN_MANAGER_EMAIL,
    KITCHEN_MANAGER_PASSWORD,
    seed_known_users,
)


def test_login_with_valid_kitchen_manager_credentials_succeeds(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json() == {"email": KITCHEN_MANAGER_EMAIL, "persona": "kitchen_manager"}
    assert "session_token" in response.cookies


def test_login_with_valid_fb_manager_credentials_succeeds(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": FB_MANAGER_EMAIL, "password": FB_MANAGER_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json() == {"email": FB_MANAGER_EMAIL, "persona": "fb_manager"}
    assert "session_token" in response.cookies


def test_a_valid_session_cookie_grants_access_to_a_stub_screen(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    login_response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )
    assert login_response.status_code == 200

    screen_response = client.get("/screens/risk-dashboard")
    assert screen_response.status_code == 200
    assert screen_response.json()["screen"] == "risk-dashboard"


def test_login_with_wrong_password_returns_generic_401(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": "definitely-the-wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
    assert "session_token" not in response.cookies


def test_login_with_unknown_email_returns_the_same_generic_401(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": "nobody-registered@example.com", "password": "irrelevant-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
    assert "session_token" not in response.cookies


def test_kitchen_managers_password_does_not_authenticate_as_fb_manager(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": FB_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )

    assert response.status_code == 401
    assert "session_token" not in response.cookies


def test_fb_managers_password_does_not_authenticate_as_kitchen_manager(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": FB_MANAGER_PASSWORD},
    )

    assert response.status_code == 401
    assert "session_token" not in response.cookies


def test_login_with_missing_password_returns_422(client: TestClient, db_session: Session) -> None:
    seed_known_users(db_session)

    response = client.post("/auth/login", json={"email": KITCHEN_MANAGER_EMAIL})

    assert response.status_code == 422


def test_login_email_lookup_is_case_insensitive(client: TestClient, db_session: Session) -> None:
    """The stored email is lowercased at seed time; login must match
    regardless of the case the user types it in."""
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL.upper(), "password": KITCHEN_MANAGER_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json() == {"email": KITCHEN_MANAGER_EMAIL, "persona": "kitchen_manager"}
    assert "session_token" in response.cookies


def test_login_email_lookup_tolerates_leading_and_trailing_whitespace(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": f"  {KITCHEN_MANAGER_EMAIL}  ", "password": KITCHEN_MANAGER_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json() == {"email": KITCHEN_MANAGER_EMAIL, "persona": "kitchen_manager"}


def test_login_email_with_mixed_case_and_whitespace_still_rejects_the_wrong_password(
    client: TestClient, db_session: Session
) -> None:
    """Normalization must not accidentally widen matching beyond the email —
    a wrong password with a differently-cased/whitespace-padded email must
    still be rejected."""
    seed_known_users(db_session)

    response = client.post(
        "/auth/login",
        json={"email": f"  {KITCHEN_MANAGER_EMAIL.upper()}  ", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
    assert "session_token" not in response.cookies
