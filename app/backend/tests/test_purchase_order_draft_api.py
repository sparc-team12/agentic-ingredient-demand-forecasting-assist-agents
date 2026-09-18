"""`/ingredients/{id}/purchase-order-draft` HTTP route (ACRI-53 US-018): auth
reuse, unknown-ingredient 404, an end-to-end draft built through the public
API surface, and the "not stockout-flagged" 404 case.

The seeded sales history spans 14 consecutive real-clock days with a
constant `units_sold`, mirroring `test_risk_api.py`, so the projected daily
demand is deterministic regardless of which weekday `date.today()` happens
to land on when the suite runs.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import KITCHEN_MANAGER_EMAIL, KITCHEN_MANAGER_PASSWORD, seed_known_users

CONSTANT_UNITS_SOLD = 10
QUANTITY_PER_SERVING = 2.0
DAILY_TOTAL = CONSTANT_UNITS_SOLD * QUANTITY_PER_SERVING  # 20.0


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
        "lead_time_days": 5,
        "safety_margin_days": 2,
    }
    payload.update(overrides)
    response = client.post("/suppliers", json=payload)
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


def _create_dish(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": "Margherita Pizza"}
    payload.update(overrides)
    response = client.post("/dishes", json=payload)
    assert response.status_code == 201
    return response.json()


def _add_recipe_line(client: TestClient, dish_id: int, ingredient_name: str) -> None:
    response = client.post(
        f"/dishes/{dish_id}/recipe-lines",
        json={
            "ingredient_name": ingredient_name,
            "quantity_per_serving": QUANTITY_PER_SERVING,
            "unit": "kg",
        },
    )
    assert response.status_code == 201


def _seed_two_weeks_of_constant_sales(client: TestClient, dish_id: int) -> None:
    today = date.today()
    for offset in range(1, 15):
        response = client.post(
            "/sales-history",
            json={
                "dish_id": dish_id,
                "sale_date": str(today - timedelta(days=offset)),
                "units_sold": CONSTANT_UNITS_SOLD,
            },
        )
        assert response.status_code == 201


def _put_current_stock(
    client: TestClient, ingredient_id: int, quantity_on_hand: float, use_by_date: str | None
) -> dict[str, Any]:
    response = client.put(
        f"/current-stock/{ingredient_id}",
        json={"quantity_on_hand": quantity_on_hand, "use_by_date": use_by_date},
    )
    assert response.status_code == 200
    return response.json()


def _seed_ingredient_with_constant_demand(
    client: TestClient, name: str, **ingredient_overrides: Any
) -> dict[str, Any]:
    ingredient = _create_ingredient(client, name=name, **ingredient_overrides)
    dish = _create_dish(client, name=f"{name} Dish")
    _add_recipe_line(client, dish["id"], ingredient["name"])
    _seed_two_weeks_of_constant_sales(client, dish["id"])
    return ingredient


def test_get_purchase_order_draft_requires_authentication(client: TestClient) -> None:
    response = client.get("/ingredients/1/purchase-order-draft")
    assert response.status_code == 401


def test_get_purchase_order_draft_for_unknown_ingredient_returns_404(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.get("/ingredients/999999/purchase-order-draft")

    assert response.status_code == 404


def test_draft_correct_for_a_stockout_flagged_ingredient_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    supplier = _create_supplier(client, lead_time_days=5, safety_margin_days=2)
    ingredient = _seed_ingredient_with_constant_demand(
        client, "Stockout Risk Ingredient", supplier_id=supplier["id"]
    )
    # Cumulative demand: day1=20, day2=40, day3=60 -> stockout on day3.
    _put_current_stock(client, ingredient["id"], quantity_on_hand=45.0, use_by_date=None)

    response = client.get(f"/ingredients/{ingredient['id']}/purchase-order-draft")

    assert response.status_code == 200
    body = response.json()
    today = date.today()
    assert body["ingredient_id"] == ingredient["id"]
    assert body["item_name"] == "Stockout Risk Ingredient"
    assert body["unit"] == "kg"
    assert body["supplier_name"] == "Acme Produce Co"
    assert body["supplier_gap"] is False
    assert body["required_delivery_date"] == str(
        today + timedelta(days=3) - timedelta(days=5 + 2)
    )
    assert body["suggested_quantity"] == pytest.approx(5 * DAILY_TOTAL)


def test_no_draft_available_response_for_a_non_stockout_flagged_ingredient(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _seed_ingredient_with_constant_demand(client, "Never At Risk")
    # Plenty of stock -> never stockout-flagged within the horizon.
    _put_current_stock(client, ingredient["id"], quantity_on_hand=10_000, use_by_date=None)

    response = client.get(f"/ingredients/{ingredient['id']}/purchase-order-draft")

    assert response.status_code == 404
    assert "not currently flagged for stockout risk" in response.json()["detail"]


def test_no_draft_available_when_no_current_stock_recorded_at_all(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _seed_ingredient_with_constant_demand(client, "No Stock Snapshot")

    response = client.get(f"/ingredients/{ingredient['id']}/purchase-order-draft")

    assert response.status_code == 404


def test_missing_supplier_flags_supplier_gap_over_http(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _seed_ingredient_with_constant_demand(client, "No Supplier Ingredient")
    _put_current_stock(client, ingredient["id"], quantity_on_hand=45.0, use_by_date=None)

    response = client.get(f"/ingredients/{ingredient['id']}/purchase-order-draft")

    assert response.status_code == 200
    body = response.json()
    assert body["supplier_name"] is None
    assert body["supplier_gap"] is True
