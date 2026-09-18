"""`GET /auth/me` behavior (session bootstrap, used by the frontend
`AuthProvider` on mount): 401 with no cookie, 401 with a tampered/forged
cookie, 200 with the authenticated user's identity for either persona, and
401 again after logout.

This endpoint had no dedicated test coverage prior to this file even though
it is load-bearing for AC1 (session bootstrap) and is explicitly listed in
the implementation plan's backend contract table (`implementation-plan.md`
§6)."""

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


def test_me_returns_401_with_no_session_cookie(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_returns_401_with_a_tampered_or_forged_session_cookie(client: TestClient) -> None:
    """A cookie value that was never issued by `create_session` (e.g.
    forged, guessed, or corrupted in transit) must be rejected identically
    to having no cookie at all — no partial trust, no information leak."""
    client.cookies.set("session_token", "tampered-or-forged-token-value")
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_returns_the_kitchen_managers_identity_after_login(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)
    client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": KITCHEN_MANAGER_EMAIL, "persona": "kitchen_manager"}


def test_me_returns_the_fb_managers_identity_after_login(
    client: TestClient, db_session: Session
) -> None:
    seed_known_users(db_session)
    client.post(
        "/auth/login",
        json={"email": FB_MANAGER_EMAIL, "password": FB_MANAGER_PASSWORD},
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": FB_MANAGER_EMAIL, "persona": "fb_manager"}


def test_me_returns_401_again_after_logout(client: TestClient, db_session: Session) -> None:
    seed_known_users(db_session)
    client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )
    client.post("/auth/logout")

    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
