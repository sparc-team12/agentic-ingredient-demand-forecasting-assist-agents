"""`/ingredients/{id}/risk` and `/risk-config` HTTP routes (ACRI-38..44,
ACRI-64): auth reuse, unknown-ingredient 404, an end-to-end stockout+
spoilage evaluation built entirely through the public API surface, the
neither-flagged case, and the live-adjustable materiality threshold.

The seeded sales history spans 14 consecutive real-clock days with a
constant `units_sold`, mirroring `test_demand_projection_api.py`, so the
projected daily demand is deterministic regardless of which weekday
`date.today()` happens to land on when the suite runs.
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


def test_get_ingredient_risk_requires_authentication(client: TestClient) -> None:
    response = client.get("/ingredients/1/risk")
    assert response.status_code == 401


def test_get_ingredient_risk_for_unknown_ingredient_returns_404(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.get("/ingredients/999999/risk")

    assert response.status_code == 404


def test_neither_flagged_when_no_stock_recorded_at_all(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _seed_ingredient_with_constant_demand(client, "Never At Risk")

    response = client.get(f"/ingredients/{ingredient['id']}/risk")

    assert response.status_code == 200
    body = response.json()
    assert body["stockout"] is None
    assert body["spoilage"] is None


def test_end_to_end_stockout_risk_traces_to_lead_time_and_safety_margin(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    supplier = _create_supplier(client, lead_time_days=5, safety_margin_days=2)
    ingredient = _seed_ingredient_with_constant_demand(
        client, "Stockout Risk Ingredient", supplier_id=supplier["id"]
    )
    # Cumulative demand: day1=20, day2=40, day3=60 -> stockout on day3.
    _put_current_stock(client, ingredient["id"], quantity_on_hand=45.0, use_by_date=None)

    response = client.get(f"/ingredients/{ingredient['id']}/risk")

    assert response.status_code == 200
    body = response.json()
    stockout = body["stockout"]
    assert stockout is not None
    today = date.today()
    assert stockout["stockout_date"] == str(today + timedelta(days=3))
    assert stockout["order_by_date"] == str(today + timedelta(days=3) - timedelta(days=5 + 2))
    assert stockout["suggested_order_quantity"] == pytest.approx(5 * DAILY_TOTAL)
    assert stockout["safety_margin_gap"] is False
    assert stockout["lead_time_gap"] is False
    assert stockout["severity"] in {"Critical", "High", "Low"}
    assert body["spoilage"] is None


def test_end_to_end_spoilage_risk_is_suppressed_below_the_default_threshold(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _seed_ingredient_with_constant_demand(
        client, "Spoilage Risk Ingredient", perishable=True, shelf_life_days=5, unit_cost=1.0
    )
    today = date.today()
    use_by_date = today + timedelta(days=3)
    # Cumulative demand by day3 = 60; stock 65 -> unconsumed 5 -> waste_cost 5.
    _put_current_stock(
        client, ingredient["id"], quantity_on_hand=65.0, use_by_date=str(use_by_date)
    )

    response = client.get(f"/ingredients/{ingredient['id']}/risk")

    assert response.status_code == 200
    body = response.json()
    spoilage = body["spoilage"]
    assert spoilage is not None
    assert spoilage["use_by_date"] == str(use_by_date)
    assert spoilage["waste_cost_inr"] == pytest.approx(5.0)
    assert spoilage["severity"] == "Low"
    assert spoilage["suppressed"] is True  # 5 < default 500 threshold
    assert body["stockout"] is None or body["stockout"]["severity"] in {"Critical", "High", "Low"}


def test_get_risk_config_requires_authentication(client: TestClient) -> None:
    response = client.get("/risk-config")
    assert response.status_code == 401


def test_get_risk_config_returns_default_500(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    response = client.get("/risk-config")

    assert response.status_code == 200
    assert response.json() == {"materiality_threshold_inr": 500.0}


def test_put_risk_config_updates_and_applies_immediately(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    put_response = client.put("/risk-config", json={"materiality_threshold_inr": 250.0})
    assert put_response.status_code == 200
    assert put_response.json() == {"materiality_threshold_inr": 250.0}

    get_response = client.get("/risk-config")
    assert get_response.json() == {"materiality_threshold_inr": 250.0}


def test_put_risk_config_rejects_a_negative_threshold(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.put("/risk-config", json={"materiality_threshold_inr": -1})

    assert response.status_code == 422
