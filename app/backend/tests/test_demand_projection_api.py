"""`/demand-projection` HTTP route (ACRI-36 US-001 / ACRI-37 US-002): auth
reuse, the default >=14-day forward horizon (AC3), a custom `days` query
param, an unknown-ingredient 404, and an end-to-end per-dish/per-weekday
traceable projection built entirely through the public API surface.

The seeded sales history spans 14 consecutive real-clock days (2 full
weeks) with a constant `units_sold`, so every day-of-week group has
exactly 2 matching records with the same value — the weighted average is
that same value regardless of which weekday `date.today()` happens to
land on when the suite runs, keeping this test deterministic without
depending on a fixed calendar date.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import KITCHEN_MANAGER_EMAIL, KITCHEN_MANAGER_PASSWORD, seed_known_users

CONSTANT_UNITS_SOLD = 10


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


def _add_recipe_line(
    client: TestClient, dish_id: int, ingredient_name: str, quantity_per_serving: float
) -> dict[str, Any]:
    response = client.post(
        f"/dishes/{dish_id}/recipe-lines",
        json={
            "ingredient_name": ingredient_name,
            "quantity_per_serving": quantity_per_serving,
            "unit": "kg",
        },
    )
    assert response.status_code == 201
    return response.json()


def _seed_two_weeks_of_constant_sales(client: TestClient, dish_id: int) -> None:
    today = date.today()
    for offset in range(1, 15):
        sale_date = today - timedelta(days=offset)
        response = client.post(
            "/sales-history",
            json={
                "dish_id": dish_id,
                "sale_date": str(sale_date),
                "units_sold": CONSTANT_UNITS_SOLD,
            },
        )
        assert response.status_code == 201


def test_get_demand_projection_requires_authentication(client: TestClient) -> None:
    response = client.get("/demand-projection/1")
    assert response.status_code == 401


def test_unknown_ingredient_returns_404(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    response = client.get("/demand-projection/999999")

    assert response.status_code == 404


def test_default_horizon_is_at_least_14_days_ac3(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client)

    response = client.get(f"/demand-projection/{ingredient['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["horizon_days"] == 14
    assert len(body["series"]) == 14


def test_custom_days_query_param_controls_the_series_length(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client)

    response = client.get(f"/demand-projection/{ingredient['id']}", params={"days": 20})

    assert response.status_code == 200
    body = response.json()
    assert body["horizon_days"] == 20
    assert len(body["series"]) == 20


def test_end_to_end_projection_is_traceable_to_the_contributing_dish_ac1_ac3_ac5(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    ingredient = _create_ingredient(client)
    _add_recipe_line(client, dish["id"], ingredient["name"], quantity_per_serving=2.0)
    _seed_two_weeks_of_constant_sales(client, dish["id"])

    response = client.get(f"/demand-projection/{ingredient['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["ingredient_id"] == ingredient["id"]
    assert len(body["series"]) == 14

    for day_entry in body["series"]:
        assert day_entry["total"] == 20.0  # units_sold(10) * quantity_per_serving(2.0)
        assert len(day_entry["contributing_dishes"]) == 1
        contributing_dish = day_entry["contributing_dishes"][0]
        assert contributing_dish["dish_id"] == dish["id"]
        assert contributing_dish["projected_dish_demand"] == 10.0
        assert contributing_dish["contribution"] == 20.0
        trace = contributing_dish["trace"]
        assert trace["gap"] is False
        assert len(trace["data_points"]) == 2
        assert [point["units_sold"] for point in trace["data_points"]] == [10, 10]
        assert [point["weight"] for point in trace["data_points"]] == [1.0, 2.0]
        assert trace["weighted_average"] == 10.0
