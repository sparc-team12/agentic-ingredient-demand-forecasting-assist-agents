"""Pure unit tests for `services/dashboard_service.py` (ACRI-54 US-019,
ACRI-55 US-020, ACRI-56 US-021, ACRI-57 US-022, ACRI-58 US-023).

Same conventions as `test_stockout_risk_service.py`/
`test_spoilage_risk_service.py`: direct ORM setup, an explicit `anchor` on
every call, and 14 consecutive days of constant sales history (daily total
10.0, via `quantity_per_serving=1.0` and `units_sold=10`) so every
ingredient's projected demand is a known constant, letting stockout dates
and waste costs be picked deterministically.

Layout of the combined scenario (`_seed_combined_dashboard_scenario`),
covering every AC this module is responsible for:

- `stockout_critical_soonest` / `stockout_critical_later` — both Critical
  stockout rows, `order_by_date` = anchor+1 and anchor+2 respectively
  (days-away 1 and 2) — exercises the "stockout rows ordered by
  `order_by_date` ascending within a tied band" tie-break.
- `spoilage_critical_highest` / `spoilage_critical_lower` — both Critical
  spoilage rows, waste cost 5000 and 2500 respectively — exercises the
  "spoilage rows ordered by `waste_cost_inr` descending within a tied
  band" tie-break, and the "stockout rows before spoilage rows within the
  same tied band" rule.
- `stockout_high` — a High-severity stockout row — exercises AC3's
  explicit example: it must rank *below* every Critical row above,
  including the Critical *spoilage* rows, even though those are a
  different risk type.
- `spoilage_suppressed_low` — a Low-severity spoilage row whose waste cost
  (50) is below the default 500 materiality threshold — exercises
  ACRI-58's "aggregate sum includes suppressed rows; the row itself is
  still returned, tagged `suppressed=True`" rule.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from db.models import CurrentStock, Dish, Ingredient, RecipeLine, SalesHistoryRecord, Supplier
from services.dashboard_service import get_risk_summary

ANCHOR = date(2026, 1, 1)
DAILY_TOTAL = 10.0


def _make_dish(db: Session, name: str) -> Dish:
    dish = Dish(name=name)
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


def _seed_two_weeks_of_constant_history(db: Session, dish_id: int) -> None:
    for offset in range(1, 15):
        db.add(
            SalesHistoryRecord(
                dish_id=dish_id, sale_date=ANCHOR - timedelta(days=offset), units_sold=DAILY_TOTAL
            )
        )
    db.commit()


def _make_supplier(db: Session, name: str) -> Supplier:
    supplier = Supplier(name=name, lead_time_days=0, safety_margin_days=0)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _seed_stockout_ingredient(
    db: Session, name: str, *, quantity_on_hand: float, supplier: Supplier
) -> Ingredient:
    """A non-perishable ingredient at stockout risk only. `lead_time_days`
    and `safety_margin_days` are both 0 on `supplier`, so
    `order_by_date == stockout_date` and `days_away == (stockout_date -
    ANCHOR).days` exactly, keeping the arithmetic simple to reason about."""
    ingredient = Ingredient(
        name=name, unit="kg", unit_cost=1.0, perishable=False, supplier_id=supplier.id
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    dish = _make_dish(db, f"{name} Dish")
    db.add(
        RecipeLine(
            dish_id=dish.id,
            ingredient_name=name,
            ingredient_id=ingredient.id,
            quantity_per_serving=1.0,
            unit="kg",
        )
    )
    db.commit()
    _seed_two_weeks_of_constant_history(db, dish.id)

    db.add(CurrentStock(ingredient_id=ingredient.id, quantity_on_hand=quantity_on_hand))
    db.commit()
    return ingredient


def _seed_spoilage_ingredient(
    db: Session,
    name: str,
    *,
    quantity_on_hand: float,
    unit_cost: float,
    use_by_offset_days: int,
) -> Ingredient:
    """A perishable ingredient at spoilage risk only (no supplier, so it is
    never at stockout risk either — `evaluate_stockout_risk` returns `None`
    with no `CurrentStock`-independent reason to flag it; it still has a
    `CurrentStock` row, but no supplier is irrelevant to spoilage)."""
    ingredient = Ingredient(
        name=name,
        unit="kg",
        unit_cost=unit_cost,
        perishable=True,
        shelf_life_days=30,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    dish = _make_dish(db, f"{name} Dish")
    db.add(
        RecipeLine(
            dish_id=dish.id,
            ingredient_name=name,
            ingredient_id=ingredient.id,
            quantity_per_serving=1.0,
            unit="kg",
        )
    )
    db.commit()
    _seed_two_weeks_of_constant_history(db, dish.id)

    db.add(
        CurrentStock(
            ingredient_id=ingredient.id,
            quantity_on_hand=quantity_on_hand,
            use_by_date=ANCHOR + timedelta(days=use_by_offset_days),
        )
    )
    db.commit()
    return ingredient


def _seed_combined_dashboard_scenario(db: Session) -> None:
    supplier = _make_supplier(db, "Dashboard Test Supplier")

    # Critical stockout rows (days-away 1 and 2, both <= 2 -> Critical).
    # Cumulative demand: day1=10, day2=20, ... quantity_on_hand=5 -> stockout
    # on day1 (10 >= 5) -> order_by_date = ANCHOR+1 -> days_away=1.
    _seed_stockout_ingredient(
        db, "Stockout Critical Soonest", quantity_on_hand=5.0, supplier=supplier
    )
    # quantity_on_hand=15 -> stockout on day2 (20 >= 15) -> order_by_date =
    # ANCHOR+2 -> days_away=2.
    _seed_stockout_ingredient(
        db, "Stockout Critical Later", quantity_on_hand=15.0, supplier=supplier
    )
    # High stockout row (days-away 5, in [3, 7] -> High). quantity_on_hand=45
    # -> stockout on day5 (50 >= 45).
    _seed_stockout_ingredient(db, "Stockout High", quantity_on_hand=45.0, supplier=supplier)

    # Critical spoilage rows. `quantity_on_hand` is kept > 140 (the 14-day
    # stockout horizon's max cumulative demand at daily_total=10.0) on all 3
    # spoilage-only ingredients below so `evaluate_stockout_risk` never also
    # flags them within this suite's forward horizon — each ingredient below
    # is spoilage-risk-only, by construction.
    # use_by_date = ANCHOR+3 -> cumulative demand up to use_by_date = 30.0.
    # unconsumed = 530 - 30 = 500 -> waste = 500 * 10 = 5000 (Critical).
    _seed_spoilage_ingredient(
        db,
        "Spoilage Critical Highest",
        quantity_on_hand=530.0,
        unit_cost=10.0,
        use_by_offset_days=3,
    )
    # unconsumed = 280 - 30 = 250 -> waste = 250 * 10 = 2500 (Critical).
    _seed_spoilage_ingredient(
        db,
        "Spoilage Critical Lower",
        quantity_on_hand=280.0,
        unit_cost=10.0,
        use_by_offset_days=3,
    )

    # Low spoilage row, suppressed by the default 500 INR threshold.
    # use_by_date = ANCHOR+1 -> cumulative demand up to use_by_date = 10.0.
    # unconsumed = 510 - 10 = 500 -> waste = 500 * 0.1 = 50 (Low, < 500).
    _seed_spoilage_ingredient(
        db,
        "Spoilage Suppressed Low",
        quantity_on_hand=510.0,
        unit_cost=0.1,
        use_by_offset_days=1,
    )


def test_empty_dashboard_has_zero_total_and_no_rows(db_session: Session) -> None:
    summary = get_risk_summary(db_session, anchor=ANCHOR)

    assert summary.total_waste_exposure_inr == 0.0
    assert summary.rows == []
    assert summary.materiality_threshold_inr == 500.0


def test_combined_ranking_rule_orders_by_severity_band_then_documented_tie_break(
    db_session: Session,
) -> None:
    _seed_combined_dashboard_scenario(db_session)

    summary = get_risk_summary(db_session, anchor=ANCHOR)

    ordered = [(row.ingredient_name, row.risk_type, row.severity) for row in summary.rows]
    assert ordered == [
        ("Stockout Critical Soonest", "stockout", "Critical"),
        ("Stockout Critical Later", "stockout", "Critical"),
        ("Spoilage Critical Highest", "spoilage", "Critical"),
        ("Spoilage Critical Lower", "spoilage", "Critical"),
        ("Stockout High", "stockout", "High"),
        ("Spoilage Suppressed Low", "spoilage", "Low"),
    ]


def test_critical_spoilage_ranks_above_high_stockout_ac3(db_session: Session) -> None:
    """AC3's explicit example: a Critical spoilage item ranks above a High
    stockout item, cross-type."""
    _seed_combined_dashboard_scenario(db_session)

    summary = get_risk_summary(db_session, anchor=ANCHOR)

    names_in_order = [row.ingredient_name for row in summary.rows]
    critical_spoilage_index = names_in_order.index("Spoilage Critical Lower")
    high_stockout_index = names_in_order.index("Stockout High")
    assert critical_spoilage_index < high_stockout_index


def test_stockout_rows_ordered_by_order_by_date_ascending_within_tied_band(
    db_session: Session,
) -> None:
    _seed_combined_dashboard_scenario(db_session)

    summary = get_risk_summary(db_session, anchor=ANCHOR)

    stockout_rows = [row for row in summary.rows if row.risk_type == "stockout"]
    dates = [row.order_by_date for row in stockout_rows]
    assert all(d is not None for d in dates)
    non_null_dates = [d for d in dates if d is not None]
    assert non_null_dates == sorted(non_null_dates)
    assert non_null_dates[0] == ANCHOR + timedelta(days=1)


def test_spoilage_rows_ordered_by_waste_cost_descending_within_tied_band(
    db_session: Session,
) -> None:
    _seed_combined_dashboard_scenario(db_session)

    summary = get_risk_summary(db_session, anchor=ANCHOR)

    spoilage_rows = [row for row in summary.rows if row.risk_type == "spoilage"]
    costs = [row.waste_cost_inr for row in spoilage_rows]
    assert all(c is not None for c in costs)
    non_null_costs = [c for c in costs if c is not None]
    assert non_null_costs == sorted(non_null_costs, reverse=True)


def test_aggregate_total_includes_suppressed_spoilage_rows(db_session: Session) -> None:
    _seed_combined_dashboard_scenario(db_session)

    summary = get_risk_summary(db_session, anchor=ANCHOR)

    suppressed_rows = [row for row in summary.rows if row.suppressed]
    assert len(suppressed_rows) == 1
    assert suppressed_rows[0].ingredient_name == "Spoilage Suppressed Low"
    assert suppressed_rows[0].waste_cost_inr == pytest.approx(50.0)

    # 5000 + 2500 + 50 = 7550, including the suppressed row's waste cost.
    assert summary.total_waste_exposure_inr == pytest.approx(7550.0)


def test_stockout_rows_never_marked_suppressed(db_session: Session) -> None:
    _seed_combined_dashboard_scenario(db_session)

    summary = get_risk_summary(db_session, anchor=ANCHOR)

    stockout_rows = [row for row in summary.rows if row.risk_type == "stockout"]
    assert all(row.suppressed is False for row in stockout_rows)
    assert all(row.waste_cost_inr is None for row in stockout_rows)
    assert all(row.order_by_date is None for row in summary.rows if row.risk_type == "spoilage")
