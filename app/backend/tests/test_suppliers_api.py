"""`/suppliers` HTTP routes (ACRI-61 AC2/AC4): auth reuse, create/list,
validation, duplicate-name conflict, and full-replace `PUT` semantics
(tech-lead review MINOR finding)."""

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


def test_get_suppliers_requires_authentication(client: TestClient) -> None:
    response = client.get("/suppliers")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_and_list_suppliers_round_trips_name_and_lead_time(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    create_response = client.post(
        "/suppliers",
        json={"name": "Acme Produce Co", "lead_time_days": 3, "safety_margin_days": 2},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Acme Produce Co"
    assert created["lead_time_days"] == 3
    assert created["safety_margin_days"] == 2

    list_response = client.get("/suppliers")
    assert list_response.status_code == 200
    suppliers = list_response.json()
    assert len(suppliers) == 1
    assert suppliers[0]["name"] == "Acme Produce Co"


def test_create_supplier_with_empty_name_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post("/suppliers", json={"name": "   ", "lead_time_days": 3})

    assert response.status_code == 422


def test_create_supplier_with_negative_lead_time_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post("/suppliers", json={"name": "Acme Produce Co", "lead_time_days": -1})

    assert response.status_code == 422


def test_create_supplier_with_negative_safety_margin_returns_422(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/suppliers",
        json={"name": "Acme Produce Co", "lead_time_days": 3, "safety_margin_days": -1},
    )

    assert response.status_code == 422


def test_create_supplier_with_no_safety_margin_leaves_it_null(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)

    response = client.post(
        "/suppliers", json={"name": "Metro Wholesale Foods", "lead_time_days": 5}
    )

    assert response.status_code == 201
    assert response.json()["safety_margin_days"] is None


def test_create_supplier_with_duplicate_name_returns_409(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    client.post("/suppliers", json={"name": "Acme Produce Co", "lead_time_days": 3})

    response = client.post("/suppliers", json={"name": "Acme Produce Co", "lead_time_days": 4})

    assert response.status_code == 409


def test_update_supplier_replaces_all_fields(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)
    created: dict[str, Any] = client.post(
        "/suppliers",
        json={"name": "Acme Produce Co", "lead_time_days": 3, "safety_margin_days": 2},
    ).json()

    response = client.put(
        f"/suppliers/{created['id']}",
        json={"name": "Acme Produce Co", "lead_time_days": 4, "safety_margin_days": 5},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["lead_time_days"] == 4
    assert updated["safety_margin_days"] == 5


def test_update_supplier_full_replace_clears_an_omitted_optional_field(
    client: TestClient, db_session: Session
) -> None:
    """Tech-lead review MINOR finding: `PUT` is full-replace, not a partial
    merge. An edit payload that omits `safety_margin_days` (defaults to
    `None` on the schema) clears the previously-set value — it does not
    silently preserve it — matching the pre-filled-edit-form client
    contract described in the plan."""
    _login(client, db_session)
    created: dict[str, Any] = client.post(
        "/suppliers",
        json={"name": "Acme Produce Co", "lead_time_days": 3, "safety_margin_days": 2},
    ).json()
    assert created["safety_margin_days"] == 2

    response = client.put(
        f"/suppliers/{created['id']}",
        json={"name": "Acme Produce Co", "lead_time_days": 3},
    )

    assert response.status_code == 200
    assert response.json()["safety_margin_days"] is None


def test_update_unknown_supplier_returns_404(client: TestClient, db_session: Session) -> None:
    _login(client, db_session)

    response = client.put("/suppliers/999999", json={"name": "Ghost", "lead_time_days": 1})

    assert response.status_code == 404


def test_update_supplier_to_a_duplicate_name_returns_409(
    client: TestClient, db_session: Session
) -> None:
    _login(client, db_session)
    client.post("/suppliers", json={"name": "Acme Produce Co", "lead_time_days": 3})
    second: dict[str, Any] = client.post(
        "/suppliers", json={"name": "Metro Wholesale Foods", "lead_time_days": 5}
    ).json()

    response = client.put(
        f"/suppliers/{second['id']}", json={"name": "Acme Produce Co", "lead_time_days": 5}
    )

    assert response.status_code == 409
