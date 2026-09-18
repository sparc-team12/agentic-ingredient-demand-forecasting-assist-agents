"""AC1/AC5: all 4 protected `/screens/*` routes require a valid session and
grant both personas an identical response shape."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import (
    FB_MANAGER_EMAIL,
    FB_MANAGER_PASSWORD,
    KITCHEN_MANAGER_EMAIL,
    KITCHEN_MANAGER_PASSWORD,
    seed_known_users,
)

SCREEN_PATHS = [
    "/screens/risk-dashboard",
    "/screens/ingredient-detail",
    "/screens/chat-agent",
    "/screens/purchase-order-draft",
]


@pytest.mark.parametrize("path", SCREEN_PATHS)
def test_each_screen_returns_401_with_no_session_cookie(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("path", SCREEN_PATHS)
def test_each_screen_returns_401_with_a_garbage_cookie(client: TestClient, path: str) -> None:
    client.cookies.set("session_token", "not-a-real-session-token")
    response = client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", SCREEN_PATHS)
def test_each_screen_returns_200_for_an_authenticated_kitchen_manager(
    client: TestClient, db_session: Session, path: str
) -> None:
    seed_known_users(db_session)
    client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )

    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize("path", SCREEN_PATHS)
def test_each_screen_returns_200_for_an_authenticated_fb_manager(
    client: TestClient, db_session: Session, path: str
) -> None:
    seed_known_users(db_session)
    client.post(
        "/auth/login",
        json={"email": FB_MANAGER_EMAIL, "password": FB_MANAGER_PASSWORD},
    )

    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize("path", SCREEN_PATHS)
def test_both_personas_get_a_byte_identical_response_shape(
    client: TestClient, db_session: Session, path: str
) -> None:
    """AC5: no field is present for one persona and missing for the other."""
    seed_known_users(db_session)

    client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )
    km_response = client.get(path)
    client.post("/auth/logout")

    client.post(
        "/auth/login",
        json={"email": FB_MANAGER_EMAIL, "password": FB_MANAGER_PASSWORD},
    )
    fb_response = client.get(path)

    assert km_response.status_code == fb_response.status_code == 200
    assert set(km_response.json().keys()) == set(fb_response.json().keys())
    assert set(km_response.json()["user"].keys()) == set(fb_response.json()["user"].keys())
    assert km_response.json()["screen"] == fb_response.json()["screen"] == path.rsplit("/", 1)[-1]
    assert km_response.json()["message"] == fb_response.json()["message"]
