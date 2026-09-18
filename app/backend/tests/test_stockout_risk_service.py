"""Pure unit tests for `services/stockout_risk_service.py` (ACRI-38 US-003,
ACRI-39 US-004, ACRI-40 US-005, ACRI-41 US-006).

DB rows are constructed directly via the ORM models (no HTTP layer), same
convention as `test_demand_projection_service.py`. Every scenario passes an
explicit `anchor` so the maths under test never depends on the real
wall-clock date; a dish is seeded with 14 consecutive days of constant
sales history (mirrors `test_demand_projection_api.py`) so every future
day's projected demand is the same known constant, regardless of which
weekday `anchor` happens to be.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import CurrentStock, Dish, Ingredient, RecipeLine, Supplier
from services.stockout_risk_service import _severity_from_days_away, evaluate_stockout_risk

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
    from db.models import SalesHistoryRecord

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
    supplier_id: int | None = None,
    safety_margin_days_override: int | None = None,
) -> Ingredient:
    ingredient = Ingredient(
        name=name,
        unit="kg",
        unit_cost=1.0,
        perishable=False,
        supplier_id=supplier_id,
        safety_margin_days_override=safety_margin_days_override,
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


def test_no_current_stock_snapshot_is_not_fabricated_as_zero(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Unrecorded Ingredient")

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is None


def test_not_flagged_when_consumption_never_exceeds_stock_in_horizon_ac_acri_38(
    db_session: Session,
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Plenty Of Stock")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=10_000)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is None


def test_stockout_boundary_is_first_day_cumulative_demand_meets_or_exceeds_stock(
    db_session: Session,
) -> None:
    # Daily total is 10.0: cumulative after day1/2/3 = 10/20/30.
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Exact Boundary")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.stockout_date == ANCHOR + timedelta(days=3)


def test_stockout_one_unit_above_boundary_pushes_to_the_next_day(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Just Above Boundary")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.01)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.stockout_date == ANCHOR + timedelta(days=4)


def test_flagged_result_traces_to_stock_on_hand_and_demand_series_ac5(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Traceable Stockout")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=25.0)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.trace["stock_on_hand"] == 25.0
    cumulative_trace = result.trace["cumulative_demand_by_day"]
    assert cumulative_trace[0]["cumulative"] == 10.0
    assert cumulative_trace[1]["cumulative"] == 20.0
    assert cumulative_trace[2]["cumulative"] == 30.0
    assert result.trace["stockout_date"] == result.stockout_date.isoformat()


def test_order_by_date_prefers_ingredient_override_over_supplier_default_ac_acri_39(
    db_session: Session,
) -> None:
    supplier = _make_supplier(db_session, "Acme", lead_time_days=5, safety_margin_days=2)
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Override Wins", supplier_id=supplier.id, safety_margin_days_override=4
    )
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)  # stockout day3

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    stockout_date = ANCHOR + timedelta(days=3)
    assert result.stockout_date == stockout_date
    assert result.order_by_date == stockout_date - timedelta(days=5 + 4)
    assert result.safety_margin_gap is False
    assert result.lead_time_gap is False
    assert result.trace["safety_margin_source"] == "ingredient"


def test_order_by_date_falls_back_to_supplier_default_safety_margin(db_session: Session) -> None:
    supplier = _make_supplier(db_session, "Acme", lead_time_days=5, safety_margin_days=2)
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Supplier Default", supplier_id=supplier.id
    )
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    stockout_date = ANCHOR + timedelta(days=3)
    assert result.order_by_date == stockout_date - timedelta(days=5 + 2)
    assert result.trace["safety_margin_source"] == "supplier"


def test_safety_margin_gap_is_visibly_flagged_and_never_silently_treated_as_present(
    db_session: Session,
) -> None:
    supplier = _make_supplier(db_session, "No Margin Supplier", lead_time_days=5)
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Safety Margin Gap", supplier_id=supplier.id
    )
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.safety_margin_gap is True
    stockout_date = ANCHOR + timedelta(days=3)
    # Gap contributes 0 days to the date arithmetic, but is still flagged above.
    assert result.order_by_date == stockout_date - timedelta(days=5)
    assert result.trace["safety_margin_days"] is None


def test_missing_supplier_flags_lead_time_gap_and_contributes_zero_days(
    db_session: Session,
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "No Supplier Mapped")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.lead_time_gap is True
    assert result.safety_margin_gap is True
    stockout_date = ANCHOR + timedelta(days=3)
    assert result.order_by_date == stockout_date
    assert result.suggested_order_quantity == 0.0


def test_suggested_order_quantity_sums_the_lead_time_day_window_ac_acri_40(
    db_session: Session,
) -> None:
    supplier = _make_supplier(db_session, "Lead Time Supplier", lead_time_days=5)
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Order Quantity", supplier_id=supplier.id
    )
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=30.0)

    result = evaluate_stockout_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.suggested_order_quantity == pytest.approx(5 * DAILY_TOTAL)


@pytest.mark.parametrize(
    ("days_away", "expected_severity"),
    [
        (-5, "Critical"),
        (0, "Critical"),
        (2, "Critical"),
        (3, "High"),
        (7, "High"),
        (8, "Low"),
        (100, "Low"),
    ],
)
def test_severity_band_boundaries_ac_acri_41(days_away: int, expected_severity: str) -> None:
    assert _severity_from_days_away(days_away) == expected_severity


def test_unknown_ingredient_raises_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        evaluate_stockout_risk(999999, db_session, anchor=ANCHOR)

    assert exc_info.value.status_code == 404
