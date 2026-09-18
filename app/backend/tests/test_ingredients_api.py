"""`/ingredients` HTTP routes (ACRI-61 AC1/AC2/AC3/AC4/AC5): auth reuse,
create/list, perishable/shelf-life cross-field validation, supplier-id
existence check, nested supplier summary, safety-margin precedence/gap, and
full-replace `PUT` semantics (tech-lead review MINOR finding)."""

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


def _create_supplier(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Acme Produce Co",
        "lead_time_days": 3,
        "safety_margin_days": 2,
    }
    payload.update(overrides)
    response = client.post("/suppliers", json=payload)
    assert response.status_code == 201
    return response.json()


def test_get_ingredients_requires_authentication(client: TestClient) -> None:
    response = client.get("/ingredients")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_and_list_ingredient_round_trips_ac1_fields(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": True,
            "shelf_life_days": 7,
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["unit"] == "kg"
    assert created["unit_cost"] == 2.5
    assert created["perishable"] is True
    assert created["shelf_life_days"] == 7

    list_response = client.get("/ingredients")
    assert list_response.status_code == 200
    ingredients = list_response.json()
    assert len(ingredients) == 1
    assert ingredients[0]["name"] == "Roma Tomatoes"


def test_perishable_ingredient_with_null_shelf_life_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": True,
            "shelf_life_days": None,
        },
    )

    assert response.status_code == 422


def test_non_perishable_ingredient_may_omit_shelf_life(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/ingredients",
        json={"name": "Basmati Rice", "unit": "kg", "unit_cost": 1.8, "perishable": False},
    )

    assert response.status_code == 201
    assert response.json()["shelf_life_days"] is None


def test_ingredient_created_with_valid_supplier_id_shows_nested_supplier_summary_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    supplier = _create_supplier(client)

    response = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": True,
            "shelf_life_days": 7,
            "supplier_id": supplier["id"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["supplier"] == {
        "id": supplier["id"],
        "name": supplier["name"],
        "lead_time_days": supplier["lead_time_days"],
    }
    assert body["has_supplier"] is True


def test_ingredient_created_with_no_supplier_is_flagged_ac3(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/ingredients",
        json={
            "name": "Fresh Basil",
            "unit": "bunch",
            "unit_cost": 0.9,
            "perishable": True,
            "shelf_life_days": 3,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["has_supplier"] is False
    assert body["supplier"] is None


def test_create_ingredient_with_nonexistent_supplier_id_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": False,
            "supplier_id": 999999,
        },
    )

    assert response.status_code == 422


def test_create_ingredient_with_duplicate_name_returns_409(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    payload = {"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False}
    client.post("/ingredients", json=payload)

    response = client.post("/ingredients", json=payload)

    assert response.status_code == 409


def test_ingredient_override_takes_precedence_over_supplier_default_ac4(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    supplier = _create_supplier(client, safety_margin_days=9)

    response = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": False,
            "supplier_id": supplier["id"],
            "safety_margin_days_override": 3,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["effective_safety_margin_days"] == 3
    assert body["safety_margin_source"] == "ingredient"
    assert body["safety_margin_gap"] is False


def test_ingredient_falls_back_to_supplier_default_when_no_override_ac4(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    supplier = _create_supplier(client, safety_margin_days=6)

    response = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": False,
            "supplier_id": supplier["id"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["effective_safety_margin_days"] == 6
    assert body["safety_margin_source"] == "supplier"
    assert body["safety_margin_gap"] is False


def test_ingredient_with_no_override_and_no_mapped_supplier_value_is_gap_never_zero_ac5(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    supplier = _create_supplier(client, safety_margin_days=None)

    response = client.post(
        "/ingredients",
        json={
            "name": "Basmati Rice",
            "unit": "kg",
            "unit_cost": 1.8,
            "perishable": False,
            "supplier_id": supplier["id"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["effective_safety_margin_days"] is None
    assert body["safety_margin_source"] is None
    assert body["safety_margin_gap"] is True


def test_ingredient_with_no_supplier_and_no_override_is_gap_never_zero_ac5(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/ingredients",
        json={"name": "Fresh Basil", "unit": "bunch", "unit_cost": 0.9, "perishable": False},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["effective_safety_margin_days"] is None
    assert body["safety_margin_gap"] is True


def test_update_ingredient_replaces_all_fields(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)
    created: dict[str, Any] = client.post(
        "/ingredients",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False},
    ).json()

    response = client.put(
        f"/ingredients/{created['id']}",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 3.0,
            "perishable": True,
            "shelf_life_days": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["unit_cost"] == 3.0
    assert body["perishable"] is True
    assert body["shelf_life_days"] == 5


def test_update_ingredient_full_replace_unmaps_supplier_when_omitted(
    client: TestClient, db_session: Session
) -> None:
    """Tech-lead review MINOR finding: `PUT` is full-replace. An edit
    payload that omits `supplier_id` (defaults to `None` on the schema)
    un-maps the ingredient — it does not silently keep the previous
    mapping — matching the pre-filled-edit-form client contract."""
    _login(client, db_session)
    supplier = _create_supplier(client)
    created: dict[str, Any] = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": False,
            "supplier_id": supplier["id"],
        },
    ).json()
    assert created["has_supplier"] is True

    response = client.put(
        f"/ingredients/{created['id']}",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_supplier"] is False
    assert body["supplier_id"] is None


def test_update_ingredient_full_replace_also_clears_safety_margin_override_when_omitted(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    created: dict[str, Any] = client.post(
        "/ingredients",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": False,
            "safety_margin_days_override": 4,
        },
    ).json()
    assert created["safety_margin_days_override"] == 4

    response = client.put(
        f"/ingredients/{created['id']}",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False},
    )

    assert response.status_code == 200
    assert response.json()["safety_margin_days_override"] is None


def test_update_ingredient_with_nonexistent_supplier_id_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    created: dict[str, Any] = client.post(
        "/ingredients",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False},
    ).json()

    response = client.put(
        f"/ingredients/{created['id']}",
        json={
            "name": "Roma Tomatoes",
            "unit": "kg",
            "unit_cost": 2.5,
            "perishable": False,
            "supplier_id": 999999,
        },
    )

    assert response.status_code == 422


def test_update_unknown_ingredient_returns_404(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    response = client.put(
        "/ingredients/999999",
        json={"name": "Ghost", "unit": "kg", "unit_cost": 1.0, "perishable": False},
    )

    assert response.status_code == 404


def test_update_ingredient_to_a_duplicate_name_returns_409(
    client: TestClient, db_session: Session
) -> None:
    """Mirrors `test_update_supplier_to_a_duplicate_name_returns_409`: the
    same `IntegrityError`-to-409 backstop in `update_ingredient` (service
    layer) is exercised for ingredients too, not just suppliers."""
    _login(client, db_session)
    client.post(
        "/ingredients",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 2.5, "perishable": False},
    )
    second: dict[str, Any] = client.post(
        "/ingredients",
        json={"name": "Basmati Rice", "unit": "kg", "unit_cost": 1.8, "perishable": False},
    ).json()

    response = client.put(
        f"/ingredients/{second['id']}",
        json={"name": "Roma Tomatoes", "unit": "kg", "unit_cost": 1.8, "perishable": False},
    )

    assert response.status_code == 409
