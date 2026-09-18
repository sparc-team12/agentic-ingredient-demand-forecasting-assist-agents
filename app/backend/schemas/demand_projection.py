"""Pydantic schemas for the ingredient demand projection debug/introspection
HTTP contract (ACRI-36 US-001 / ACRI-37 US-002).

Mirrors the dataclasses returned by `services/demand_projection_service.py`
one-to-one (via `from_attributes=True`) so the full arithmetic trace
(US-001 AC5) and per-dish breakdown (US-002 AC3) are visible over HTTP,
not just the aggregated totals.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class WeekdayDataPointOut(BaseModel):
    """One historical sales record and the recency weight applied to it."""

    model_config = ConfigDict(from_attributes=True)

    sale_date: date
    units_sold: int
    weight: float


class DishProjectionTraceOut(BaseModel):
    """The explicit arithmetic trace for one dish's projected demand on one
    target date (US-001 AC5)."""

    model_config = ConfigDict(from_attributes=True)

    weekday: int
    weekday_name: str
    data_points: list[WeekdayDataPointOut]
    weighted_average: float
    gap: bool


class ContributingDishOut(BaseModel):
    """One dish's contribution to an ingredient's aggregated projected
    demand (US-002 AC1/AC3)."""

    model_config = ConfigDict(from_attributes=True)

    dish_id: int
    dish_name: str
    projected_dish_demand: float
    quantity_per_serving: float
    unit: str
    contribution: float
    trace: DishProjectionTraceOut


class IngredientDemandSeriesDayOut(BaseModel):
    """One day's aggregated ingredient demand projection, with its full
    per-dish breakdown."""

    model_config = ConfigDict(from_attributes=True)

    date: date
    total: float
    contributing_dishes: list[ContributingDishOut]


class IngredientDemandSeriesOut(BaseModel):
    """Response body for `GET /demand-projection/{ingredient_id}` — the
    full forward-horizon projection series for one ingredient."""

    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    ingredient_name: str
    horizon_days: int
    series: list[IngredientDemandSeriesDayOut]
