"""Business logic for spoilage risk (ACRI-42 US-007, ACRI-43 US-008,
ACRI-44 US-009, ACRI-64 US-029).

Responsibility: pure, deterministic maths only, built on
`services/demand_projection_service.py::project_ingredient_demand_series`,
`CurrentStock.use_by_date`, `Ingredient.unit_cost`, and the live
materiality threshold from `services/risk_config_service.py`. No HTTP
concerns here — those live in `routes/risk.py`.

- US-007 (spoilage flag): a non-`perishable` ingredient is *never* flagged
  — `evaluate_spoilage_risk` returns `None` immediately, before even
  looking at stock. A `perishable` ingredient with no recorded
  `CurrentStock` snapshot, or no recorded `use_by_date`, cannot be
  evaluated either (a data gap owned by ACRI-62, not fabricated here) and
  also returns `None`. Otherwise: sum the demand series' daily `total` for
  every day on or before `use_by_date`; if that cumulative demand is
  strictly less than `quantity_on_hand`, some stock will still be on hand,
  unconsumed, at the use-by date — spoilage risk (AC: "cumulative demand up
  to use_by_date < stock_on_hand"). If `use_by_date` is today or already in
  the past, there are zero forward days left to sum, so cumulative demand
  is `0.0` (the entire current stock is unconsumed).
- US-008 (waste cost): `waste_cost_inr = unconsumed_quantity * unit_cost`,
  where `unconsumed_quantity = max(quantity_on_hand - cumulative_demand,
  0.0)` (floored at `0`, never negative).
- US-009 (materiality threshold): `suppressed = waste_cost_inr <
  materiality_threshold_inr` (read live from `risk_config_service`, so a
  `PUT /risk-config` change applies to the very next evaluation).
  `suppressed` is returned alongside the *raw*, un-suppressed
  `waste_cost_inr` — a caller building a visible list can filter on
  `suppressed`; a caller summing an aggregate total never has to, and so is
  never silently short-changed by the threshold.
- US-029 (severity): `_severity_from_waste_cost`, banded off
  `waste_cost_inr` — see that function's docstring for the exact
  boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import CurrentStock, Ingredient
from services import demand_projection_service, risk_config_service


@dataclass(frozen=True)
class SpoilageRiskResult:
    """A single ingredient's spoilage risk, with every figure that AC5/AC-
    traceability requires and the explicit arithmetic `trace` that
    justifies it."""

    ingredient_id: int
    ingredient_name: str
    use_by_date: date
    waste_cost_inr: float
    severity: str
    suppressed: bool
    trace: dict[str, Any]


def _severity_from_waste_cost(waste_cost_inr: float) -> str:
    """US-029 AC: `Critical` when `waste_cost_inr >= 2000`, `High` when
    `500 <= waste_cost_inr < 2000`, `Low` when `waste_cost_inr < 500`."""
    if waste_cost_inr >= 2000:
        return "Critical"
    if waste_cost_inr >= 500:
        return "High"
    return "Low"


def _get_ingredient_or_404(db: Session, ingredient_id: int) -> Ingredient:
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return ingredient


def evaluate_spoilage_risk(
    ingredient_id: int,
    db: Session,
    *,
    anchor: date | None = None,
    scenario_adjustments: list[demand_projection_service.ScenarioAdjustment] | None = None,
) -> SpoilageRiskResult | None:
    """US-007/US-008/US-009/US-029. Returns `None` when the ingredient is
    non-perishable, has no recorded stock/use-by date, or is not at
    spoilage risk. Raises `404` for an unknown `ingredient_id`. `anchor`
    defaults to `date.today()` — see
    `stockout_risk_service.evaluate_stockout_risk` for the same pattern.

    `scenario_adjustments` (ACRI-49..52, optional): forwarded verbatim to
    `project_ingredient_demand_series` — `None` (the default) reproduces
    the exact pre-what-if behavior."""
    today = anchor if anchor is not None else date.today()
    ingredient = _get_ingredient_or_404(db, ingredient_id)

    if not ingredient.perishable:
        return None

    stock = db.execute(
        select(CurrentStock).where(CurrentStock.ingredient_id == ingredient_id)
    ).scalar_one_or_none()
    if stock is None or stock.use_by_date is None:
        return None

    use_by_date = stock.use_by_date
    days_until_use_by = (use_by_date - today).days

    daily_totals_trace: list[dict[str, Any]] = []
    if days_until_use_by <= 0:
        cumulative_demand = 0.0
    else:
        series = demand_projection_service.project_ingredient_demand_series(
            ingredient_id,
            days_until_use_by,
            db,
            start_date=today,
            scenario_adjustments=scenario_adjustments,
        )
        relevant_days = [day for day in series.series if day.date <= use_by_date]
        cumulative_demand = sum(day.total for day in relevant_days)
        daily_totals_trace = [
            {"date": day.date.isoformat(), "total": day.total} for day in relevant_days
        ]

    stock_on_hand = stock.quantity_on_hand
    if cumulative_demand >= stock_on_hand:
        return None

    unconsumed_quantity = max(stock_on_hand - cumulative_demand, 0.0)
    waste_cost_inr = unconsumed_quantity * ingredient.unit_cost
    materiality_threshold_inr = risk_config_service.get_materiality_threshold(db)
    suppressed = waste_cost_inr < materiality_threshold_inr
    severity = _severity_from_waste_cost(waste_cost_inr)

    trace: dict[str, Any] = {
        "perishable": ingredient.perishable,
        "use_by_date": use_by_date.isoformat(),
        "stock_on_hand": stock_on_hand,
        "days_until_use_by": days_until_use_by,
        "spoilage_rule": "cumulative demand up to use_by_date < stock_on_hand",
        "cumulative_demand_up_to_use_by_date": cumulative_demand,
        "demand_by_day": daily_totals_trace,
        "unconsumed_quantity_formula": "max(stock_on_hand - cumulative_demand, 0.0)",
        "unconsumed_quantity": unconsumed_quantity,
        "unit_cost": ingredient.unit_cost,
        "waste_cost_formula": "unconsumed_quantity * unit_cost",
        "waste_cost_inr": waste_cost_inr,
        "materiality_threshold_inr": materiality_threshold_inr,
        "suppressed": suppressed,
        "severity_thresholds": {"critical_min_inr": 2000, "high_min_inr": 500},
        "anchor_date": today.isoformat(),
    }

    return SpoilageRiskResult(
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        use_by_date=use_by_date,
        waste_cost_inr=waste_cost_inr,
        severity=severity,
        suppressed=suppressed,
        trace=trace,
    )
