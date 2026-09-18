"""`/data-setup/status` HTTP route (ACRI-59 AC1/AC2): auth reuse, per-
category loaded/not-loaded (at least 1 row), and the all-4-loaded flag."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import KITCHEN_MANAGER_EMAIL, KITCHEN_MANAGER_PASSWORD, seed_known_users


def _login(client: TestClient, db_session: Session) -> None:
    seed_known_users(db_session)
    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )
    assert response.status_code == 200


def _create_dish(client: TestClient) -> dict[str, Any]:
    response = client.post("/dishes", json={"name": "Margherita Pizza"})
    assert response.status_code == 201
    return response.json()


def _create_ingredient(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/ingredients",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False},
    )
    assert response.status_code == 201
    return response.json()


def test_get_status_requires_authentication(client: TestClient) -> None:
    response = client.get("/data-setup/status")
    assert response.status_code == 401


def test_all_categories_not_loaded_on_a_fresh_database_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.get("/data-setup/status")

    assert response.status_code == 200
    body = response.json()
    assert len(body["categories"]) == 4
    assert all(category["loaded"] is False for category in body["categories"])
    assert body["all_loaded"] is False


def test_category_becomes_loaded_once_at_least_one_row_exists_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    _create_dish(client)

    response = client.get("/data-setup/status")

    categories = {category["id"]: category for category in response.json()["categories"]}
    assert categories["menu-recipe"]["loaded"] is True
    assert categories["ingredients-suppliers"]["loaded"] is False
    assert categories["current-stock"]["loaded"] is False
    assert categories["sales-history"]["loaded"] is False


def test_all_loaded_is_true_only_once_every_category_has_a_row_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    ingredient = _create_ingredient(client)
    client.put(
        f"/current-stock/{ingredient['id']}",
        json={"quantity_on_hand": 5, "use_by_date": None},
    )

    before = client.get("/data-setup/status").json()
    assert before["all_loaded"] is False

    client.post(
        "/sales-history",
        json={"dish_id": dish["id"], "sale_date": "2026-01-01", "units_sold": 5},
    )

    after = client.get("/data-setup/status").json()
    assert after["all_loaded"] is True
    assert all(category["loaded"] is True for category in after["categories"])


def test_category_entries_carry_label_and_path(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    response = client.get("/data-setup/status")

    categories = {category["id"]: category for category in response.json()["categories"]}
    assert categories["ingredients-suppliers"]["path"] == "/data-setup/ingredients-suppliers"
    assert categories["menu-recipe"]["label"] == "Menu & Recipe Setup"
