"""Pure unit tests for `services/spoilage_risk_service.py` (ACRI-42 US-007,
ACRI-43 US-008, ACRI-44 US-009, ACRI-64 US-029).

Same conventions as `test_stockout_risk_service.py`: direct ORM setup, an
explicit `anchor` on every call, and 14 consecutive days of constant sales
history so the projected daily demand is a known constant regardless of
weekday.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import CurrentStock, Dish, Ingredient, RecipeLine, SalesHistoryRecord
from schemas.risk import RiskConfigUpdate
from services.risk_config_service import update_risk_config
from services.spoilage_risk_service import _severity_from_waste_cost, evaluate_spoilage_risk

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
    db: Session, name: str, *, perishable: bool = True, unit_cost: float = 1.0
) -> Ingredient:
    ingredient = Ingredient(
        name=name,
        unit="kg",
        unit_cost=unit_cost,
        perishable=perishable,
        shelf_life_days=5 if perishable else None,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


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


def _add_current_stock(
    db: Session, ingredient_id: int, quantity_on_hand: float, use_by_date: date | None
) -> CurrentStock:
    stock = CurrentStock(
        ingredient_id=ingredient_id, quantity_on_hand=quantity_on_hand, use_by_date=use_by_date
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def _seed_ingredient_with_constant_demand(
    db: Session, name: str, *, perishable: bool = True, unit_cost: float = 1.0
) -> Ingredient:
    ingredient = _make_ingredient(db, name, perishable=perishable, unit_cost=unit_cost)
    dish = _make_dish(db, f"{name} Dish")
    _add_recipe_line(db, dish.id, ingredient)
    _seed_two_weeks_of_constant_history(db, dish.id, ANCHOR, DAILY_TOTAL)
    return ingredient


def test_non_perishable_ingredient_is_never_flagged_ac_acri_42(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Non Perishable", perishable=False
    )
    # Stock that would otherwise clearly leave a large unconsumed remainder.
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=1.0, use_by_date=ANCHOR)

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is None


def test_no_current_stock_snapshot_is_not_fabricated(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "No Snapshot")

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is None


def test_no_use_by_date_recorded_cannot_be_evaluated(db_session: Session) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "No Use By Date")
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=100.0, use_by_date=None)

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is None


def test_not_flagged_when_cumulative_demand_exactly_meets_stock_boundary_ac_acri_42(
    db_session: Session,
) -> None:
    # 3 days until use-by => cumulative demand = 3 * 10 = 30. Stock exactly 30.
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Exact Boundary")
    _add_current_stock(
        db_session, ingredient.id, quantity_on_hand=30.0, use_by_date=ANCHOR + timedelta(days=3)
    )

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is None


def test_flagged_when_cumulative_demand_is_strictly_below_stock_ac_acri_42(
    db_session: Session,
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Flagged Spoilage", unit_cost=20.0
    )
    _add_current_stock(
        db_session, ingredient.id, quantity_on_hand=35.0, use_by_date=ANCHOR + timedelta(days=3)
    )

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.use_by_date == ANCHOR + timedelta(days=3)
    # unconsumed = 35 - 30 = 5; waste_cost = 5 * 20 = 100 (ACRI-43).
    assert result.waste_cost_inr == pytest.approx(100.0)
    assert result.trace["cumulative_demand_up_to_use_by_date"] == pytest.approx(30.0)
    assert result.trace["unconsumed_quantity"] == pytest.approx(5.0)


def test_waste_cost_floors_unconsumed_quantity_at_zero_never_negative(db_session: Session) -> None:
    # Sanity: the boundary test above already proves stock <= cumulative
    # returns None (never a negative waste cost); this asserts the exact
    # floor formula directly via the trace on a small positive remainder.
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Floor Check", unit_cost=1.0)
    _add_current_stock(
        db_session, ingredient.id, quantity_on_hand=30.5, use_by_date=ANCHOR + timedelta(days=3)
    )

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.trace["unconsumed_quantity"] == pytest.approx(0.5)
    assert result.trace["unconsumed_quantity"] >= 0.0


@pytest.mark.parametrize("days_before_anchor", [0, 2])
def test_use_by_date_today_or_in_the_past_treats_cumulative_demand_as_zero(
    db_session: Session, days_before_anchor: int
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, f"Past Use By {days_before_anchor}", unit_cost=2.0
    )
    use_by_date = ANCHOR - timedelta(days=days_before_anchor)
    _add_current_stock(db_session, ingredient.id, quantity_on_hand=5.0, use_by_date=use_by_date)

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.trace["cumulative_demand_up_to_use_by_date"] == 0.0
    assert result.waste_cost_inr == pytest.approx(5.0 * 2.0)


@pytest.mark.parametrize(
    ("waste_cost_inr", "expected_severity"),
    [
        (2000.0, "Critical"),
        (1999.99, "High"),
        (500.0, "High"),
        (499.99, "Low"),
        (0.0, "Low"),
    ],
)
def test_severity_band_boundaries_ac_acri_64(waste_cost_inr: float, expected_severity: str) -> None:
    assert _severity_from_waste_cost(waste_cost_inr) == expected_severity


def test_materiality_threshold_suppresses_below_but_not_at_the_boundary_ac_acri_44(
    db_session: Session,
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(
        db_session, "Materiality Boundary", unit_cost=10.0
    )
    # unconsumed = 35 - 30 = 5; waste_cost = 50.
    _add_current_stock(
        db_session, ingredient.id, quantity_on_hand=35.0, use_by_date=ANCHOR + timedelta(days=3)
    )
    update_risk_config(db_session, RiskConfigUpdate(materiality_threshold_inr=50.0))

    result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert result is not None
    assert result.waste_cost_inr == pytest.approx(50.0)
    # Exactly at the threshold is not "below" it -> not suppressed.
    assert result.suppressed is False


def test_materiality_threshold_change_applies_immediately_and_never_alters_raw_cost(
    db_session: Session,
) -> None:
    ingredient = _seed_ingredient_with_constant_demand(db_session, "Live Threshold", unit_cost=10.0)
    _add_current_stock(
        db_session, ingredient.id, quantity_on_hand=35.0, use_by_date=ANCHOR + timedelta(days=3)
    )

    default_result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)
    assert default_result is not None
    assert default_result.suppressed is True  # 50 < default 500
    assert default_result.waste_cost_inr == pytest.approx(50.0)

    update_risk_config(db_session, RiskConfigUpdate(materiality_threshold_inr=10.0))
    updated_result = evaluate_spoilage_risk(ingredient.id, db_session, anchor=ANCHOR)

    assert updated_result is not None
    assert updated_result.suppressed is False  # 50 >= 10 now
    assert updated_result.waste_cost_inr == pytest.approx(50.0)  # raw cost unaffected


def test_unknown_ingredient_raises_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        evaluate_spoilage_risk(999999, db_session, anchor=ANCHOR)

    assert exc_info.value.status_code == 404
