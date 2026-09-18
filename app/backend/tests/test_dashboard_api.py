"""`/dashboard/risk-summary` HTTP route (ACRI-54..58): auth reuse, an
empty-dashboard shape, and an end-to-end stockout+spoilage aggregation
built entirely through the public API surface (mirrors
`test_risk_api.py`'s end-to-end conventions, real wall-clock dates via
`date.today()` since these are API-level tests, not pure unit tests).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import KITCHEN_MANAGER_EMAIL, KITCHEN_MANAGER_PASSWORD, seed_known_users

CONSTANT_UNITS_SOLD = 10
QUANTITY_PER_SERVING = 1.0
DAILY_TOTAL = CONSTANT_UNITS_SOLD * QUANTITY_PER_SERVING  # 10.0


def _login(client: TestClient, db_session: Session) -> None:
    seed_known_users(db_session)
    response = client.post(
        "/auth/login",
        json={"email": KITCHEN_MANAGER_EMAIL, "password": KITCHEN_MANAGER_PASSWORD},
    )
    assert response.status_code == 200


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


def test_get_risk_summary_requires_authentication(client: TestClient) -> None:
    response = client.get("/dashboard/risk-summary")
    assert response.status_code == 401


def test_get_risk_summary_is_empty_when_no_ingredients_exist(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.get("/dashboard/risk-summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_waste_exposure_inr"] == 0.0
    assert body["rows"] == []
    assert body["materiality_threshold_inr"] == 500.0


def test_get_risk_summary_includes_both_risk_types_end_to_end(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    stockout_ingredient = _seed_ingredient_with_constant_demand(client, "Dashboard Stockout")
    # Cumulative demand: day1=10, day2=20, day3=30 -> stockout day3.
    _put_current_stock(client, stockout_ingredient["id"], quantity_on_hand=25.0, use_by_date=None)

    spoilage_ingredient = _seed_ingredient_with_constant_demand(
        client, "Dashboard Spoilage", perishable=True, shelf_life_days=30, unit_cost=100.0
    )
    today = date.today()
    use_by_date = today + timedelta(days=3)
    # Cumulative demand up to use_by_date = 30.0; unconsumed = 530 - 30 = 500
    # -> waste_cost = 500 * 100 = 50000 (well above the default threshold,
    # so both `rows` and the total sum reflect it unsuppressed).
    _put_current_stock(
        client, spoilage_ingredient["id"], quantity_on_hand=530.0, use_by_date=str(use_by_date)
    )

    response = client.get("/dashboard/risk-summary")

    assert response.status_code == 200
    body = response.json()

    row_by_name = {row["ingredient_name"]: row for row in body["rows"]}
    assert row_by_name["Dashboard Stockout"]["risk_type"] == "stockout"
    assert row_by_name["Dashboard Stockout"]["order_by_date"] is not None
    assert row_by_name["Dashboard Stockout"]["waste_cost_inr"] is None
    assert row_by_name["Dashboard Stockout"]["suppressed"] is False

    assert row_by_name["Dashboard Spoilage"]["risk_type"] == "spoilage"
    assert row_by_name["Dashboard Spoilage"]["waste_cost_inr"] == 50000.0
    assert row_by_name["Dashboard Spoilage"]["order_by_date"] is None
    assert row_by_name["Dashboard Spoilage"]["suppressed"] is False

    assert body["total_waste_exposure_inr"] == 50000.0


def test_get_risk_summary_total_includes_suppressed_rows(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    ingredient = _seed_ingredient_with_constant_demand(
        client, "Below Threshold Spoilage", perishable=True, shelf_life_days=30, unit_cost=0.1
    )
    today = date.today()
    use_by_date = today + timedelta(days=1)
    # Cumulative demand up to use_by_date = 10.0; unconsumed = 510 - 10 =
    # 500 -> waste_cost = 500 * 0.1 = 50 (< default 500 threshold ->
    # suppressed).
    _put_current_stock(
        client, ingredient["id"], quantity_on_hand=510.0, use_by_date=str(use_by_date)
    )

    response = client.get("/dashboard/risk-summary")

    assert response.status_code == 200
    body = response.json()
    row = next(r for r in body["rows"] if r["ingredient_name"] == "Below Threshold Spoilage")
    assert row["suppressed"] is True
    assert row["waste_cost_inr"] == 50.0
    assert body["total_waste_exposure_inr"] == 50.0
