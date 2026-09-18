"""Pure unit tests for `services/demand_projection_service.py` (ACRI-36
US-001 / ACRI-37 US-002): day-of-week grouping, recency weighting,
determinism, zero-history gaps, multi-dish aggregation, and per-dish/
per-weekday traceability.

DB rows are constructed directly via the ORM models (no HTTP layer, no
`client` fixture) since the service itself is a pure computation layer
over the DB — mirroring the `test_safety_margin_gap_logic.py` convention
of testing business logic in isolation.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Dish, Ingredient, RecipeLine, SalesHistoryRecord
from services.demand_projection_service import (
    _project_dish_demand_with_trace,
    project_dish_demand,
    project_ingredient_demand,
    project_ingredient_demand_series,
)

# 2026-01-03 is a Saturday; 2026-01-04 is the following Sunday.
TARGET_SATURDAY = date(2026, 1, 3)
TARGET_SUNDAY = date(2026, 1, 4)


def _make_dish(db: Session, name: str) -> Dish:
    dish = Dish(name=name)
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


def _add_sale(db: Session, dish_id: int, sale_date: date, units_sold: int) -> None:
    db.add(SalesHistoryRecord(dish_id=dish_id, sale_date=sale_date, units_sold=units_sold))
    db.commit()


def _make_ingredient(db: Session, name: str, unit: str = "kg") -> Ingredient:
    ingredient = Ingredient(name=name, unit=unit, unit_cost=1.0, perishable=False)
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


def _add_recipe_line(
    db: Session,
    dish_id: int,
    ingredient: Ingredient,
    quantity_per_serving: float,
    unit: str = "kg",
) -> RecipeLine:
    line = RecipeLine(
        dish_id=dish_id,
        ingredient_name=ingredient.name,
        ingredient_id=ingredient.id,
        quantity_per_serving=quantity_per_serving,
        unit=unit,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


def test_projection_for_a_saturday_uses_only_saturday_history_not_flat_average_ac1(
    db_session: Session,
) -> None:
    dish = _make_dish(db_session, "Weekend Special")
    # A Thursday and a Friday sale that would drag a flat average way down.
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(days=1), 1)
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(days=2), 1)
    # Two prior Saturdays.
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(weeks=1), 20)
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(weeks=2), 20)

    projected = project_dish_demand(dish.id, TARGET_SATURDAY, db_session)

    # A flat average across all 4 rows would be (1+1+20+20)/4 = 10.5.
    assert projected == pytest.approx(20.0)
    assert projected != pytest.approx(10.5)


def test_recency_weighting_differs_from_a_flat_weekday_average_ac2(db_session: Session) -> None:
    dish = _make_dish(db_session, "Trending Dish")
    older_saturday = TARGET_SATURDAY - timedelta(weeks=2)
    newer_saturday = TARGET_SATURDAY - timedelta(weeks=1)
    _add_sale(db_session, dish.id, older_saturday, 10)
    _add_sale(db_session, dish.id, newer_saturday, 20)

    projected = project_dish_demand(dish.id, TARGET_SATURDAY, db_session)

    flat_average = (10 + 20) / 2
    # Linear recency weights: 1 for the older Saturday, 2 for the newer one.
    expected_weighted = (1 * 10 + 2 * 20) / 3
    assert projected == pytest.approx(expected_weighted)
    assert projected != pytest.approx(flat_average)


def test_same_inputs_run_twice_produce_identical_output_ac4(db_session: Session) -> None:
    dish = _make_dish(db_session, "Deterministic Dish")
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(weeks=1), 7)
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(weeks=2), 13)

    first = project_dish_demand(dish.id, TARGET_SATURDAY, db_session)
    second = project_dish_demand(dish.id, TARGET_SATURDAY, db_session)

    assert first == second


def test_zero_history_for_target_weekday_returns_zero_not_an_error_ac1(
    db_session: Session,
) -> None:
    dish = _make_dish(db_session, "No Saturday History")
    # Only Sunday history exists — no Saturday row at all.
    _add_sale(db_session, dish.id, TARGET_SUNDAY - timedelta(weeks=1), 9)

    projected = project_dish_demand(dish.id, TARGET_SATURDAY, db_session)

    assert projected == 0.0


def test_trace_reconstructs_the_arithmetic_back_to_sales_history_ac5(
    db_session: Session,
) -> None:
    dish = _make_dish(db_session, "Traceable Dish")
    older_saturday = TARGET_SATURDAY - timedelta(weeks=2)
    newer_saturday = TARGET_SATURDAY - timedelta(weeks=1)
    _add_sale(db_session, dish.id, older_saturday, 10)
    _add_sale(db_session, dish.id, newer_saturday, 20)

    result = _project_dish_demand_with_trace(dish.id, TARGET_SATURDAY, db_session)

    assert result.trace.gap is False
    assert result.trace.weekday == TARGET_SATURDAY.weekday()
    assert [point.sale_date for point in result.trace.data_points] == [
        older_saturday,
        newer_saturday,
    ]
    assert [point.units_sold for point in result.trace.data_points] == [10, 20]
    assert [point.weight for point in result.trace.data_points] == [1.0, 2.0]
    assert result.trace.weighted_average == pytest.approx((1 * 10 + 2 * 20) / 3)
    assert result.value == result.trace.weighted_average


def test_zero_history_trace_flags_the_gap_instead_of_hiding_it(db_session: Session) -> None:
    dish = _make_dish(db_session, "Brand New Dish")

    result = _project_dish_demand_with_trace(dish.id, TARGET_SATURDAY, db_session)

    assert result.value == 0.0
    assert result.trace.gap is True
    assert result.trace.data_points == []


def test_forward_horizon_series_covers_at_least_14_days_ac3(db_session: Session) -> None:
    dish = _make_dish(db_session, "Horizon Dish")
    ingredient = _make_ingredient(db_session, "Horizon Ingredient")
    _add_recipe_line(db_session, dish.id, ingredient, quantity_per_serving=1.0)
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(weeks=1), 5)

    series = project_ingredient_demand_series(
        ingredient.id, 14, db_session, start_date=TARGET_SATURDAY
    )

    assert series.horizon_days == 14
    assert len(series.series) == 14
    assert series.series[0].date == TARGET_SATURDAY + timedelta(days=1)
    assert series.series[-1].date == TARGET_SATURDAY + timedelta(days=14)


def test_series_rejects_a_non_positive_horizon(db_session: Session) -> None:
    ingredient = _make_ingredient(db_session, "Zero Horizon Ingredient")

    with pytest.raises(HTTPException) as exc_info:
        project_ingredient_demand_series(ingredient.id, 0, db_session, start_date=TARGET_SATURDAY)

    assert exc_info.value.status_code == 422


def test_ingredient_demand_aggregates_across_three_contributing_dishes_ac1(
    db_session: Session,
) -> None:
    ingredient = _make_ingredient(db_session, "Shared Ingredient")

    dish_a = _make_dish(db_session, "Dish A")
    dish_b = _make_dish(db_session, "Dish B")
    dish_c = _make_dish(db_session, "Dish C")

    _add_recipe_line(db_session, dish_a.id, ingredient, quantity_per_serving=2.0)
    _add_recipe_line(db_session, dish_b.id, ingredient, quantity_per_serving=0.5)
    _add_recipe_line(db_session, dish_c.id, ingredient, quantity_per_serving=1.0)

    older_saturday = TARGET_SATURDAY - timedelta(weeks=2)
    newer_saturday = TARGET_SATURDAY - timedelta(weeks=1)
    for dish in (dish_a, dish_b, dish_c):
        _add_sale(db_session, dish.id, older_saturday, 10)
        _add_sale(db_session, dish.id, newer_saturday, 20)

    projection = project_ingredient_demand(ingredient.id, TARGET_SATURDAY, db_session)

    per_dish_demand = (1 * 10 + 2 * 20) / 3  # Same weighted projection for every dish.
    expected_total = per_dish_demand * 2.0 + per_dish_demand * 0.5 + per_dish_demand * 1.0
    assert projection.total == pytest.approx(expected_total)
    assert len(projection.contributing_dishes) == 3


def test_ingredient_demand_result_is_deterministic_ac2(db_session: Session) -> None:
    ingredient = _make_ingredient(db_session, "Deterministic Ingredient")
    dish = _make_dish(db_session, "Deterministic Contributor")
    _add_recipe_line(db_session, dish.id, ingredient, quantity_per_serving=3.0)
    _add_sale(db_session, dish.id, TARGET_SATURDAY - timedelta(weeks=1), 4)

    first = project_ingredient_demand(ingredient.id, TARGET_SATURDAY, db_session)
    second = project_ingredient_demand(ingredient.id, TARGET_SATURDAY, db_session)

    assert first.total == second.total
    assert [entry.contribution for entry in first.contributing_dishes] == [
        entry.contribution for entry in second.contributing_dishes
    ]


def test_ingredient_demand_is_traceable_to_each_contributing_dishes_amount_ac3(
    db_session: Session,
) -> None:
    ingredient = _make_ingredient(db_session, "Traceable Ingredient")
    dish_a = _make_dish(db_session, "Traceable Dish A")
    dish_b = _make_dish(db_session, "Traceable Dish B")
    _add_recipe_line(db_session, dish_a.id, ingredient, quantity_per_serving=2.0)
    _add_recipe_line(db_session, dish_b.id, ingredient, quantity_per_serving=5.0)
    _add_sale(db_session, dish_a.id, TARGET_SATURDAY - timedelta(weeks=1), 10)
    _add_sale(db_session, dish_b.id, TARGET_SATURDAY - timedelta(weeks=1), 6)

    projection = project_ingredient_demand(ingredient.id, TARGET_SATURDAY, db_session)

    breakdown = {entry.dish_id: entry for entry in projection.contributing_dishes}
    assert breakdown[dish_a.id].projected_dish_demand == pytest.approx(10.0)
    assert breakdown[dish_a.id].contribution == pytest.approx(20.0)
    assert breakdown[dish_b.id].projected_dish_demand == pytest.approx(6.0)
    assert breakdown[dish_b.id].contribution == pytest.approx(30.0)
    assert projection.total == pytest.approx(50.0)


def test_ingredient_demand_excludes_unresolved_recipe_lines(db_session: Session) -> None:
    ingredient = _make_ingredient(db_session, "Resolved Ingredient")
    resolved_dish = _make_dish(db_session, "Resolved Dish")
    unresolved_dish = _make_dish(db_session, "Unresolved Dish")
    _add_recipe_line(db_session, resolved_dish.id, ingredient, quantity_per_serving=1.0)
    # A recipe line whose typed ingredient_name never matched any Ingredient
    # row — stored with ingredient_id left NULL, per menu_recipe_service.
    db_session.add(
        RecipeLine(
            dish_id=unresolved_dish.id,
            ingredient_name="Some Unmatched Name",
            ingredient_id=None,
            quantity_per_serving=99.0,
            unit="kg",
        )
    )
    db_session.commit()
    _add_sale(db_session, resolved_dish.id, TARGET_SATURDAY - timedelta(weeks=1), 8)

    projection = project_ingredient_demand(ingredient.id, TARGET_SATURDAY, db_session)

    assert len(projection.contributing_dishes) == 1
    assert projection.contributing_dishes[0].dish_id == resolved_dish.id


def test_project_ingredient_demand_for_unknown_ingredient_raises_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        project_ingredient_demand(999999, TARGET_SATURDAY, db_session)

    assert exc_info.value.status_code == 404
