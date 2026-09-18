"""`/current-stock` HTTP routes (ACRI-62 AC1/AC2): auth reuse, one row per
existing ingredient, upsert-on-edit (never a log), and the perishable/
no-use-by-date gap flag."""

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


def _create_ingredient(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Roma Tomatoes",
        "unit": "kg",
        "unit_cost": 2.5,
        "perishable": False,
    }
    payload.update(overrides)
    response = client.post("/ingredients", json=payload)
    assert response.status_code == 201
    return response.json()


def test_get_current_stock_requires_authentication(client: TestClient) -> None:
    response = client.get("/current-stock")
    assert response.status_code == 401


def test_lists_one_row_per_existing_ingredient_even_with_no_snapshot_yet_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client)

    response = client.get("/current-stock")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["ingredient_id"] == ingredient["id"]
    assert rows[0]["has_stock_recorded"] is False
    assert rows[0]["quantity_on_hand"] is None


def test_upsert_current_stock_creates_snapshot_ac2(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client)

    response = client.put(
        f"/current-stock/{ingredient['id']}",
        json={"quantity_on_hand": 12.5, "use_by_date": "2026-01-01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quantity_on_hand"] == 12.5
    assert body["use_by_date"] == "2026-01-01"
    assert body["has_stock_recorded"] is True


def test_upsert_current_stock_updates_existing_row_not_a_log(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client)
    client.put(
        f"/current-stock/{ingredient['id']}", json={"quantity_on_hand": 10, "use_by_date": None}
    )

    response = client.put(
        f"/current-stock/{ingredient['id']}", json={"quantity_on_hand": 20, "use_by_date": None}
    )

    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == 20
    all_rows = client.get("/current-stock").json()
    assert len(all_rows) == 1


def test_perishable_ingredient_with_no_use_by_date_is_flagged_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client, perishable=True, shelf_life_days=5)
    client.put(
        f"/current-stock/{ingredient['id']}", json={"quantity_on_hand": 3, "use_by_date": None}
    )

    response = client.get("/current-stock")

    assert response.status_code == 200
    row = response.json()[0]
    assert row["use_by_date_gap"] is True


def test_perishable_ingredient_with_use_by_date_is_not_flagged_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client, perishable=True, shelf_life_days=5)
    client.put(
        f"/current-stock/{ingredient['id']}",
        json={"quantity_on_hand": 3, "use_by_date": "2026-02-01"},
    )

    response = client.get("/current-stock")

    assert response.json()[0]["use_by_date_gap"] is False


def test_non_perishable_ingredient_with_no_use_by_date_is_never_flagged(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client, perishable=False)
    client.put(
        f"/current-stock/{ingredient['id']}", json={"quantity_on_hand": 3, "use_by_date": None}
    )

    response = client.get("/current-stock")

    assert response.json()[0]["use_by_date_gap"] is False


def test_upsert_current_stock_for_unknown_ingredient_returns_404(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.put(
        "/current-stock/999999", json={"quantity_on_hand": 1, "use_by_date": None}
    )

    assert response.status_code == 404


def test_upsert_current_stock_with_negative_quantity_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    ingredient = _create_ingredient(client)

    response = client.put(
        f"/current-stock/{ingredient['id']}", json={"quantity_on_hand": -1, "use_by_date": None}
    )

    assert response.status_code == 422
