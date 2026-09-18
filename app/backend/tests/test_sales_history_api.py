"""`/sales-history` HTTP routes (ACRI-63 AC1/AC2): auth reuse, manual
add-record, per-dish distinct-days-of-history computation, and the
<84-days flag."""

from __future__ import annotations

from datetime import date, timedelta
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


def test_get_sales_history_requires_authentication(client: TestClient) -> None:
    response = client.get("/sales-history")
    assert response.status_code == 401


def test_lists_one_entry_per_dish_with_zero_records_when_none_added_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.get("/sales-history")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["dish_id"] == dish["id"]
    assert entries[0]["distinct_days_of_history"] == 0
    assert entries[0]["has_full_history"] is False
    assert entries[0]["records"] == []


def test_create_sales_history_record_for_unknown_dish_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/sales-history",
        json={"dish_id": 999999, "sale_date": "2026-01-01", "units_sold": 10},
    )

    assert response.status_code == 422


def test_create_and_list_sales_history_record_round_trips_ac1(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.post(
        "/sales-history",
        json={"dish_id": dish["id"], "sale_date": "2026-01-01", "units_sold": 42},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["dish_id"] == dish["id"]
    assert body["units_sold"] == 42

    list_response = client.get("/sales-history")
    entry = list_response.json()[0]
    assert entry["distinct_days_of_history"] == 1
    assert entry["records"][0]["units_sold"] == 42


def test_duplicate_record_for_same_dish_and_date_returns_409(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    payload = {"dish_id": dish["id"], "sale_date": "2026-01-01", "units_sold": 10}
    client.post("/sales-history", json=payload)

    response = client.post("/sales-history", json=payload)

    assert response.status_code == 409


def test_negative_units_sold_returns_422(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)
    dish = _create_dish(client)

    response = client.post(
        "/sales-history",
        json={"dish_id": dish["id"], "sale_date": "2026-01-01", "units_sold": -1},
    )

    assert response.status_code == 422


def test_dish_with_84_distinct_days_has_full_history_flag_true_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    start = date(2026, 1, 1)
    for offset in range(84):
        response = client.post(
            "/sales-history",
            json={
                "dish_id": dish["id"],
                "sale_date": str(start + timedelta(days=offset)),
                "units_sold": 5,
            },
        )
        assert response.status_code == 201

    entry = client.get("/sales-history").json()[0]

    assert entry["distinct_days_of_history"] == 84
    assert entry["has_full_history"] is True


def test_dish_with_fewer_than_84_distinct_days_is_flagged_ac2(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    dish = _create_dish(client)
    client.post(
        "/sales-history",
        json={"dish_id": dish["id"], "sale_date": "2026-01-01", "units_sold": 5},
    )

    entry = client.get("/sales-history").json()[0]

    assert entry["distinct_days_of_history"] == 1
    assert entry["has_full_history"] is False
