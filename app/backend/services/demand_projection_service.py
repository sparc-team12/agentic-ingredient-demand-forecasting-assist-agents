"""Business logic for ingredient demand projection (ACRI-36 US-001 /
ACRI-37 US-002).

Responsibility: pure, deterministic maths only.

- ``project_dish_demand`` (US-001): a recency-weighted, day-of-week-grouped
  projection of one dish's demand on one future date, derived solely from
  that dish's own `SalesHistoryRecord` rows (AC1/AC2/AC4), with an explicit
  arithmetic trace back to the underlying data points (AC5).
- ``project_ingredient_demand`` (US-002): aggregates every dish's projected
  demand for an ingredient, weighted by that dish's recipe
  ``quantity_per_serving`` (AC1), with a per-dish breakdown for
  traceability (AC3).
- ``project_ingredient_demand_series``: the same aggregation repeated across
  a forward horizon (US-001 AC3; also the shape the Stockout/Spoilage track
  will consume next — one entry per day, each carrying the same per-dish
  breakdown).

Recency weighting (US-001 AC2): within one dish's historical records that
fall on the target date's weekday (sorted oldest-to-newest), the i-th data
point (1-indexed, i=1 is the oldest match) is given a **linear** weight of
``i`` — the most recent occurrence of that weekday carries the largest
weight, the oldest carries the smallest (weight 1). The projection is the
weight-normalized average: ``sum(weight_i * units_sold_i) / sum(weight_i)``.
This weighting is a pure function of the historical rows' relative order,
never of wall-clock time, so repeated calls with the same inputs always
produce the same output (AC4).

No HTTP concerns here — those live in `routes/demand_projection.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Dish, Ingredient, RecipeLine, SalesHistoryRecord

DEFAULT_FORWARD_HORIZON_DAYS = 14
"""US-001 AC3: forward horizon of at least 14 days."""

_WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


@dataclass(frozen=True)
class WeekdayDataPoint:
    """One historical sales record contributing to a dish's weekday
    average, and the recency weight applied to it (US-001 AC5)."""

    sale_date: date
    units_sold: int
    weight: float


@dataclass(frozen=True)
class DishProjectionTrace:
    """The explicit arithmetic trace for one dish's projected demand on one
    target date (US-001 AC5): which weekday was matched, every historical
    data point considered, the weight applied to each, and the resulting
    weighted average. ``gap`` is `True` when the dish has zero history for
    that weekday — the projection is `0.0`, not an error, but the gap is
    never silently hidden."""

    weekday: int
    weekday_name: str
    data_points: list[WeekdayDataPoint]
    weighted_average: float
    gap: bool


@dataclass(frozen=True)
class DishProjectionResult:
    value: float
    trace: DishProjectionTrace


def _weekday_history(db: Session, dish_id: int, weekday: int) -> list[SalesHistoryRecord]:
    """All of one dish's `SalesHistoryRecord` rows falling on `weekday`
    (Python convention: Monday=0 .. Sunday=6), oldest first."""
    records = (
        db.execute(
            select(SalesHistoryRecord)
            .where(SalesHistoryRecord.dish_id == dish_id)
            .order_by(SalesHistoryRecord.sale_date)
        )
        .scalars()
        .all()
    )
    return [record for record in records if record.sale_date.weekday() == weekday]


def _project_dish_demand_with_trace(
    dish_id: int, target_date: date, db: Session
) -> DishProjectionResult:
    """Shared implementation behind `project_dish_demand`: computes both the
    projected value and the trace that justifies it, per the module-level
    recency-weighting formula."""
    weekday = target_date.weekday()
    history = _weekday_history(db, dish_id, weekday)

    if not history:
        trace = DishProjectionTrace(
            weekday=weekday,
            weekday_name=_WEEKDAY_NAMES[weekday],
            data_points=[],
            weighted_average=0.0,
            gap=True,
        )
        return DishProjectionResult(value=0.0, trace=trace)

    data_points = [
        WeekdayDataPoint(
            sale_date=record.sale_date, units_sold=record.units_sold, weight=float(rank)
        )
        for rank, record in enumerate(history, start=1)
    ]
    total_weight = sum(point.weight for point in data_points)
    weighted_sum = sum(point.weight * point.units_sold for point in data_points)
    weighted_average = weighted_sum / total_weight

    trace = DishProjectionTrace(
        weekday=weekday,
        weekday_name=_WEEKDAY_NAMES[weekday],
        data_points=data_points,
        weighted_average=weighted_average,
        gap=False,
    )
    return DishProjectionResult(value=weighted_average, trace=trace)


def project_dish_demand(dish_id: int, target_date: date, db: Session) -> float:
    """US-001: recency-weighted, day-of-week-grouped projection for one dish
    on one future date (AC1/AC2/AC4). Returns `0.0` — never raises — when
    the dish has zero history for that weekday (a gap, not an error); use
    `_project_dish_demand_with_trace` when the trace is also needed."""
    return _project_dish_demand_with_trace(dish_id, target_date, db).value


@dataclass(frozen=True)
class ContributingDish:
    """One dish's contribution to an ingredient's aggregated projected
    demand (US-002 AC1/AC3)."""

    dish_id: int
    dish_name: str
    projected_dish_demand: float
    quantity_per_serving: float
    unit: str
    contribution: float
    trace: DishProjectionTrace


@dataclass(frozen=True)
class IngredientDemandProjection:
    ingredient_id: int
    ingredient_name: str
    target_date: date
    total: float
    contributing_dishes: list[ContributingDish]


def _get_ingredient_or_404(db: Session, ingredient_id: int) -> Ingredient:
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return ingredient


def project_ingredient_demand(
    ingredient_id: int, target_date: date, db: Session
) -> IngredientDemandProjection:
    """US-002: aggregates projected demand for `ingredient_id` on
    `target_date` across every `RecipeLine` that resolves to it (AC1) —
    only rows with a non-`NULL`, resolved `ingredient_id` ever match this
    query, per US-002's "resolved ingredient_id lines" scope. Each dish's
    contribution is ``project_dish_demand(dish, target_date) *
    quantity_per_serving`` (AC1), and every contribution is returned
    individually for traceability (AC3), never just the total.

    Raises `404` when `ingredient_id` does not reference an existing
    `Ingredient`.
    """
    ingredient = _get_ingredient_or_404(db, ingredient_id)

    recipe_lines = (
        db.execute(select(RecipeLine).where(RecipeLine.ingredient_id == ingredient_id))
        .scalars()
        .all()
    )

    contributing_dishes: list[ContributingDish] = []
    total = 0.0
    for line in recipe_lines:
        dish = db.get(Dish, line.dish_id)
        if dish is None:
            continue
        result = _project_dish_demand_with_trace(dish.id, target_date, db)
        contribution = result.value * line.quantity_per_serving
        contributing_dishes.append(
            ContributingDish(
                dish_id=dish.id,
                dish_name=dish.name,
                projected_dish_demand=result.value,
                quantity_per_serving=line.quantity_per_serving,
                unit=line.unit,
                contribution=contribution,
                trace=result.trace,
            )
        )
        total += contribution

    return IngredientDemandProjection(
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        target_date=target_date,
        total=total,
        contributing_dishes=contributing_dishes,
    )


@dataclass(frozen=True)
class IngredientDemandSeriesDay:
    date: date
    total: float
    contributing_dishes: list[ContributingDish]


@dataclass(frozen=True)
class IngredientDemandSeries:
    ingredient_id: int
    ingredient_name: str
    horizon_days: int
    series: list[IngredientDemandSeriesDay]


@dataclass(frozen=True)
class ScenarioAdjustment:
    """One what-if adjustment (ACRI-49..52): `extra_servings` additional
    servings of `dish_id` on `date`, purely in-memory — never written to
    the database. Applied by `project_ingredient_demand_series` as
    ``extra_servings * recipe_quantity_per_serving`` extra demand on that
    date, for every ingredient present in that dish's recipe (a no-op for
    an ingredient/date combination the adjustment doesn't touch)."""

    dish_id: int
    date: date
    extra_servings: int


def _scenario_extra_for_ingredient(
    ingredient_id: int,
    day: date,
    scenario_adjustments: list[ScenarioAdjustment] | None,
    db: Session,
) -> tuple[float, list[ContributingDish]]:
    """The extra demand (and its own `ContributingDish` breakdown entries,
    for traceability) that `scenario_adjustments` contribute to
    `ingredient_id` on `day`. Returns `(0.0, [])` when no adjustment
    targets this ingredient/day — the default, unscenario'd path is
    untouched. Purely in-memory: reads `RecipeLine`/`Dish` rows already in
    the session, writes nothing."""
    if not scenario_adjustments:
        return 0.0, []

    extra_total = 0.0
    extra_dishes: list[ContributingDish] = []
    for adjustment in scenario_adjustments:
        if adjustment.date != day:
            continue
        line = (
            db.execute(
                select(RecipeLine).where(
                    RecipeLine.dish_id == adjustment.dish_id,
                    RecipeLine.ingredient_id == ingredient_id,
                )
            )
            .scalars()
            .first()
        )
        if line is None:
            # This dish's recipe doesn't use this ingredient at all —
            # not a gap, just nothing to add.
            continue
        dish = db.get(Dish, adjustment.dish_id)
        dish_name = dish.name if dish is not None else f"dish#{adjustment.dish_id}"
        contribution = adjustment.extra_servings * line.quantity_per_serving
        extra_total += contribution
        extra_dishes.append(
            ContributingDish(
                dish_id=adjustment.dish_id,
                dish_name=f"{dish_name} (what-if: +{adjustment.extra_servings} servings)",
                projected_dish_demand=float(adjustment.extra_servings),
                quantity_per_serving=line.quantity_per_serving,
                unit=line.unit,
                contribution=contribution,
                trace=DishProjectionTrace(
                    weekday=day.weekday(),
                    weekday_name=_WEEKDAY_NAMES[day.weekday()],
                    data_points=[],
                    weighted_average=0.0,
                    gap=False,
                ),
            )
        )
    return extra_total, extra_dishes


def project_ingredient_demand_series(
    ingredient_id: int,
    horizon_days: int,
    db: Session,
    *,
    start_date: date | None = None,
    scenario_adjustments: list[ScenarioAdjustment] | None = None,
) -> IngredientDemandSeries:
    """The full forward-horizon projection series for one ingredient: one
    entry per day from `start_date + 1` to `start_date + horizon_days`
    (inclusive), each carrying the same per-dish breakdown as
    `project_ingredient_demand` (US-001 AC3, and the shape the
    Stockout/Spoilage track needs next — "does projected consumption
    exceed stock within the forward horizon").

    `start_date` defaults to `date.today()` when omitted. Passing it
    explicitly keeps the projection maths itself free of any wall-clock
    read — the only wall-clock-dependent step is choosing the anchor date,
    which happens once, at the boundary, not inside the per-day
    calculation (US-001 AC4).

    `scenario_adjustments` (ACRI-49..52, optional, defaults to `None`):
    zero or more in-memory `ScenarioAdjustment`s layered on top of the
    normal projection — see `_scenario_extra_for_ingredient`. `None`
    (the default) reproduces the exact pre-what-if behavior; every existing
    caller that never passes this argument is unaffected.
    """
    if horizon_days < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="horizon_days must be at least 1",
        )
    ingredient = _get_ingredient_or_404(db, ingredient_id)
    anchor = start_date if start_date is not None else date.today()

    series: list[IngredientDemandSeriesDay] = []
    for offset in range(1, horizon_days + 1):
        day = anchor + timedelta(days=offset)
        projection = project_ingredient_demand(ingredient_id, day, db)
        extra_total, extra_dishes = _scenario_extra_for_ingredient(
            ingredient_id, day, scenario_adjustments, db
        )
        series.append(
            IngredientDemandSeriesDay(
                date=day,
                total=projection.total + extra_total,
                contributing_dishes=[*projection.contributing_dishes, *extra_dishes],
            )
        )

    return IngredientDemandSeries(
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        horizon_days=horizon_days,
        series=series,
    )
