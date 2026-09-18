"""Pure unit tests for `services/purchase_order_draft_service.py` (ACRI-53
US-018).

Follows the exact seeding conventions of `test_stockout_risk_service.py`
(constant 14-day sales history so projected demand is deterministic
regardless of weekday, an explicit `anchor` so the maths under test never
depends on the real wall-clock date).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import CurrentStock, Dish, Ingredient, RecipeLine, SalesHistoryRecord, Supplier
from services.purchase_order_draft_service import generate_purchase_order_draft

ANCHOR = date(2026, 1, 1)
DAILY_TOTAL = 10.0


def _make_dish(db: Session, name: str) -> Dish:
    dish = Dish(name=name)
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


def _seed_two_weeks_of_constant_history(
    db: Session, dish_id: int, anchor: date, units_sold: float
) -> None:
    for offset in range(1, 15):
        db.add(
            SalesHistoryRecord(
                dish_id=dish_id, sale_date=anchor - timedelta(days=offset), units_sold=units_sold
            )
        )
    db.commit()


def _make_ingredient(
    db: Session,
    name: str,
    *,
    unit: str = "kg",
    supplier_id: int | None = None,
) -> Ingredient:
    ingredient = Ingredient(
        name=name,
        unit=unit,
        unit_cost=1.0,
        perishable=False,
        supplier_id=supplier_id,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


def _make_supplier(
    db: Session, name: str, *, lead_time_days: int, safety_margin_days: int | None = None
) -> Supplier:
    supplier = Supplier(
        name=name, lead_time_days=lead_time_days, safety_margin_days=safety_margin_days
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _add_recipe_line(db: Session, dish_id: int, ingredient: Ingredient) -> None:
    db.add(
        RecipeLine(
            dish_id=dish_id,
            ingredient_name=ingredient.name,
            ingredient_id=ingredient.id,
            quantity_per_serving=1.0,
            unit="kg",
        )
    )
    db.commit()


def _add_current_stock(db: Session, ingredient_id: int, quantity_on_hand: float) -> CurrentStock:
    stock = CurrentStock(ingredient_id=ingredient_id, quantity_on_hand=quantity_on_hand)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def _seed_ingredient_with_constant_demand(
    db: Session, name: str, **ingredient_overrides: object
) -> Ingredient:
    ingredient = _make_ingredient(db, name, **ingredient_overrides)  # type: ignore[arg-type]
    dish = _make_dish(db, f"{name} Dish")
    _add_recipe_line(db, dish.id, ingredient)
    _seed_two_weeks_of_constant_history(db, dish.id, ANCHOR, DAILY_TOTAL)
    return ingredient


def test_draft_available_for_a_stockout_flagged_ingredient_ac1(db_session: Session) -> None:
    supplier = _make_supplier(db_session, "Acme Produce Co", lead_time_days=5, safety_margin_days=2)
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Roma Tomatoes", unit="kg", supplier_id=supplier.id
    )
    # Cumulative demand: day1=10, day2=20, day3=30 -> stockout on day3.
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    draft = generate_purchase_order_draft(ingredient.id, db_session, anchor=ANCHOR)

    assert draft is not None
    assert draft.ingredient_id == ingredient.id
    assert draft.item_name == "Roma Tomatoes"
    assert draft.unit == "kg"
    assert draft.supplier_name == "Acme Produce Co"
    assert draft.supplier_gap is False
    stockout_date = ANCHOR + timedelta(days=3)
    assert draft.required_delivery_date == stockout_date - timedelta(days=5 + 2)
    assert draft.suggested_quantity == pytest.approx(5 * DAILY_TOTAL)


def test_no_draft_available_when_ingredient_is_not_stockout_flagged(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Plenty Of Stock")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=10_000)

    draft = generate_purchase_order_draft(ingredient.id, db_session, anchor=ANCHOR)

    assert draft is None


def test_no_draft_available_when_no_current_stock_snapshot_recorded(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Unrecorded Ingredient")

    draft = generate_purchase_order_draft(ingredient.id, db_session, anchor=ANCHOR)

    assert draft is None


def test_missing_supplier_flags_supplier_gap_and_leaves_supplier_name_none(
    db_session: Session,
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "No Supplier Mapped")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    draft = generate_purchase_order_draft(ingredient.id, db_session, anchor=ANCHOR)

    assert draft is not None
    assert draft.supplier_name is None
    assert draft.supplier_gap is True


def test_unknown_ingredient_raises_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        generate_purchase_order_draft(999999, db_session, anchor=ANCHOR)

    assert exc_info.value.status_code == 404
