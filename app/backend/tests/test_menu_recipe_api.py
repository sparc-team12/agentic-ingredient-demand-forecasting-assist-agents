"""`/dishes` HTTP routes (ACRI-60 AC1/AC2): auth reuse, dish create/list/
update, recipe-line create/update viewable in full, and the ingredient-name
flag for a recipe line with no matching `Ingredient`."""

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


def _create_dish(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": "Margherita Pizza"}
    payload.update(overrides)
    response = client.post("/dishes", json=payload)
    assert response.status_code == 201
    return response.json()


def _create_ingredient(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Mozzarella",
        "unit": "kg",
        "unit_cost": 5.0,
        "perishable": False,
    }
    payload.update(overrides)
    response = client.post("/ingredients", json=payload)
    assert response.status_code == 201
    return response.json()


def test_get_dishes_requires_authentication(client: TestClient) -> None:
    response = client.get("/dishes")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_and_list_dish_round_trips_ac1(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    created = _create_dish(client)
    assert created["name"] == "Margherita Pizza"

    list_response = client.get("/dishes")
    assert list_response.status_code == 200
    dishes = list_response.json()
    assert len(dishes) == 1
    assert dishes[0]["name"] == "Margherita Pizza"
    assert dishes[0]["recipe_lines"] == []


def test_create_dish_with_duplicate_name_returns_409(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    _create_dish(client)

    response = client.post("/dishes", json={"name": "Margherita Pizza"})

    assert response.status_code == 409


def test_update_dish_replaces_name(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.put(f"/dishes/{dish['id']}", json={"name": "Margherita Pizza (updated)"})

    assert response.status_code == 200
    assert response.json()["name"] == "Margherita Pizza (updated)"


def test_update_unknown_dish_returns_404(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    response = client.put("/dishes/999999", json={"name": "Ghost Dish"})

    assert response.status_code == 404


def test_create_recipe_line_for_unknown_dish_returns_404(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/dishes/999999/recipe-lines",
        json={"ingredient_name": "Mozzarella", "quantity_per_serving": 0.2, "unit": "kg"},
    )

    assert response.status_code == 404


def test_create_recipe_line_with_matching_ingredient_resolves_id_and_no_flag_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    ingredient = _create_ingredient(client)

    response = client.post(
        f"/dishes/{dish['id']}/recipe-lines",
        json={"ingredient_name": "Mozzarella", "quantity_per_serving": 0.2, "unit": "kg"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ingredient_id"] == ingredient["id"]
    assert body["ingredient_flagged"] is False


def test_create_recipe_line_with_unmatched_ingredient_is_flagged_not_rejected_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.post(
        f"/dishes/{dish['id']}/recipe-lines",
        json={"ingredient_name": "Unicorn Meat", "quantity_per_serving": 0.5, "unit": "kg"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ingredient_id"] is None
    assert body["ingredient_flagged"] is True
    assert body["ingredient_name"] == "Unicorn Meat"


def test_recipe_line_ingredient_name_match_is_case_insensitive_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    _create_ingredient(client, name="Mozzarella")

    response = client.post(
        f"/dishes/{dish['id']}/recipe-lines",
        json={"ingredient_name": "mozzarella", "quantity_per_serving": 0.2, "unit": "kg"},
    )

    assert response.status_code == 201
    assert response.json()["ingredient_flagged"] is False


def test_dish_recipe_is_viewable_in_full_not_summarized_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    for name, qty in [("Mozzarella", 0.2), ("Tomato Sauce", 0.15), ("Basil", 0.02)]:
        response = client.post(
            f"/dishes/{dish['id']}/recipe-lines",
            json={"ingredient_name": name, "quantity_per_serving": qty, "unit": "kg"},
        )
        assert response.status_code == 201

    list_response = client.get("/dishes")
    recipe_lines = list_response.json()[0]["recipe_lines"]
    assert len(recipe_lines) == 3
    assert {line["ingredient_name"] for line in recipe_lines} == {
        "Mozzarella",
        "Tomato Sauce",
        "Basil",
    }


def test_update_recipe_line_full_replace_and_re_resolves_flag(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    line: dict[str, Any] = client.post(
        f"/dishes/{dish['id']}/recipe-lines",
        json={"ingredient_name": "Unicorn Meat", "quantity_per_serving": 0.5, "unit": "kg"},
    ).json()
    assert line["ingredient_flagged"] is True
    _create_ingredient(client, name="Unicorn Meat")

    response = client.put(
        f"/dishes/{dish['id']}/recipe-lines/{line['id']}",
        json={"ingredient_name": "Unicorn Meat", "quantity_per_serving": 0.6, "unit": "kg"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ingredient_flagged"] is False
    assert body["quantity_per_serving"] == 0.6


def test_update_recipe_line_for_unknown_line_returns_404(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.put(
        f"/dishes/{dish['id']}/recipe-lines/999999",
        json={"ingredient_name": "Mozzarella", "quantity_per_serving": 0.2, "unit": "kg"},
    )

    assert response.status_code == 404


def test_create_recipe_line_with_non_positive_quantity_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.post(
        f"/dishes/{dish['id']}/recipe-lines",
        json={"ingredient_name": "Mozzarella", "quantity_per_serving": 0, "unit": "kg"},
    )

    assert response.status_code == 422
