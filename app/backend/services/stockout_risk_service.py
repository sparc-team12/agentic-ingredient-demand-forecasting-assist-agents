"""Business logic for stockout risk (ACRI-38 US-003, ACRI-39 US-004,
ACRI-40 US-005, ACRI-41 US-006).

Responsibility: pure, deterministic maths only, built entirely on top of
`services/demand_projection_service.py::project_ingredient_demand_series`
(the projected daily consumption), `CurrentStock.quantity_on_hand` (the
current stock-on-hand), `Supplier.lead_time_days`, and
`services/ingredient_service.py::resolve_safety_margin` (reused verbatim,
per the implementation plan). No HTTP concerns here — those live in
`routes/risk.py`.

- US-003 (stockout flag): cumulative-sum the demand series' daily `total`
  day by day across the default forward horizon
  (`demand_projection_service.DEFAULT_FORWARD_HORIZON_DAYS`); the first day
  the running sum reaches or exceeds `quantity_on_hand` is the stockout date
  (AC: "first day cumulative demand >= stock = stockout date"). If the
  running sum never reaches `quantity_on_hand` within that horizon, the
  ingredient is not at risk — `evaluate_stockout_risk` returns `None`.
- US-004 (order-by date): `order_by_date = stockout_date - lead_time_days -
  safety_margin_days`. `safety_margin_days` comes from
  `resolve_safety_margin` (ingredient override, then supplier default, else
  a gap — reused verbatim); a gap is never silently reported as `0` —
  `safety_margin_gap` is always surfaced on the result — but the date
  subtraction itself needs a concrete number of days, so a gap contributes
  `0` days to that arithmetic (a documented, visibly-flagged assumption, not
  a silently-hidden one). The same treatment applies to a missing
  `lead_time_days` (no supplier mapped to the ingredient at all):
  `lead_time_gap` is surfaced, and it also contributes `0` days to the date
  arithmetic and to the order-quantity window below.
- US-005 (suggested order quantity): the sum of the demand series' daily
  `total` over the first `lead_time_days` days of the series — the
  consumption expected while a freshly placed order is in transit. `0.0`
  when `lead_time_days` is a gap (see above).
- US-006 (severity): `_severity_from_days_away`, banded off
  `(order_by_date - today).days` — see that function's docstring for the
  exact boundaries.

Evaluating at all requires a recorded `CurrentStock` snapshot: no snapshot
recorded is a data gap owned by ACRI-62 (distinguished there from a
genuine zero quantity), never fabricated here as a `0` stock-on-hand —
`evaluate_stockout_risk` returns `None` in that case too, same as "not at
risk".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import CurrentStock, Ingredient
from services import demand_projection_service
from services.ingredient_service import resolve_safety_margin


@dataclass(frozen=True)
class StockoutRiskResult:
    """A single ingredient's stockout risk, with every figure that AC5/AC-
    traceability requires and the explicit arithmetic `trace` that
    justifies it."""

    ingredient_id: int
    ingredient_name: str
    stockout_date: date
    order_by_date: date
    suggested_order_quantity: float
    severity: str
    safety_margin_gap: bool
    lead_time_gap: bool
    trace: dict[str, Any]


def _severity_from_days_away(days_away: int) -> str:
    """US-006 AC: `Critical` when `days_away <= 2` (an already-passed /
    negative order-by date is also `Critical` — there is no separate
    "overdue" state), `High` when `3 <= days_away <= 7`, `Low` when
    `days_away > 7`."""
    if days_away <= 2:
        return "Critical"
    if days_away <= 7:
        return "High"
    return "Low"


def _get_ingredient_or_404(db: Session, ingredient_id: int) -> Ingredient:
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return ingredient


def evaluate_stockout_risk(
    ingredient_id: int,
    db: Session,
    *,
    anchor: date | None = None,
    scenario_adjustments: list[demand_projection_service.ScenarioAdjustment] | None = None,
) -> StockoutRiskResult | None:
    """US-003/US-004/US-005/US-006. Returns `None` when the ingredient is
    not at stockout risk, or has no recorded `CurrentStock` snapshot to
    evaluate against (see module docstring). Raises `404` for an unknown
    `ingredient_id`. `anchor` defaults to `date.today()`; passing it
    explicitly keeps the maths itself free of a wall-clock read, mirroring
    `project_ingredient_demand_series`.

    `scenario_adjustments` (ACRI-49..52, optional): forwarded verbatim to
    `project_ingredient_demand_series` — `None` (the default) reproduces
    the exact pre-what-if behavior."""
    today = anchor if anchor is not None else date.today()
    ingredient = _get_ingredient_or_404(db, ingredient_id)

    stock = db.execute(
        select(CurrentStock).where(CurrentStock.ingredient_id == ingredient_id)
    ).scalar_one_or_none()
    if stock is None:
        return None

    supplier = ingredient.supplier
    lead_time_days = supplier.lead_time_days if supplier is not None else None
    lead_time_gap = lead_time_days is None

    safety_margin_days, safety_margin_source = resolve_safety_margin(ingredient, supplier)
    safety_margin_gap = safety_margin_days is None

    stockout_horizon_days = demand_projection_service.DEFAULT_FORWARD_HORIZON_DAYS
    series_horizon = max(stockout_horizon_days, lead_time_days or 0)
    series = demand_projection_service.project_ingredient_demand_series(
        ingredient_id,
        series_horizon,
        db,
        start_date=today,
        scenario_adjustments=scenario_adjustments,
    )

    cumulative = 0.0
    stockout_day = None
    daily_cumulative_trace: list[dict[str, Any]] = []
    for day in series.series[:stockout_horizon_days]:
        cumulative += day.total
        daily_cumulative_trace.append(
            {"date": day.date.isoformat(), "daily_total": day.total, "cumulative": cumulative}
        )
        if stockout_day is None and cumulative >= stock.quantity_on_hand:
            stockout_day = day

    if stockout_day is None:
        return None

    stockout_date = stockout_day.date
    lead_time_component = lead_time_days if lead_time_days is not None else 0
    safety_margin_component = safety_margin_days if safety_margin_days is not None else 0
    order_by_date = stockout_date - timedelta(days=lead_time_component + safety_margin_component)

    if lead_time_days is not None and lead_time_days > 0:
        lead_time_window = series.series[:lead_time_days]
        suggested_order_quantity = sum(day.total for day in lead_time_window)
    else:
        lead_time_window = []
        suggested_order_quantity = 0.0

    days_away = (order_by_date - today).days
    severity = _severity_from_days_away(days_away)

    trace: dict[str, Any] = {
        "stock_on_hand": stock.quantity_on_hand,
        "horizon_days_evaluated": stockout_horizon_days,
        "cumulative_demand_by_day": daily_cumulative_trace,
        "stockout_rule": "first day cumulative demand >= stock_on_hand",
        "stockout_date": stockout_date.isoformat(),
        "lead_time_days": lead_time_days,
        "lead_time_gap": lead_time_gap,
        "safety_margin_days": safety_margin_days,
        "safety_margin_source": safety_margin_source,
        "safety_margin_gap": safety_margin_gap,
        "order_by_date_formula": "stockout_date - lead_time_days - safety_margin_days"
        " (gaps contribute 0 days, never silently)",
        "order_by_date": order_by_date.isoformat(),
        "lead_time_window_daily_totals": [
            {"date": day.date.isoformat(), "total": day.total} for day in lead_time_window
        ],
        "suggested_order_quantity_formula": "sum(daily_total for first lead_time_days days)",
        "suggested_order_quantity": suggested_order_quantity,
        "days_away_from_order_by_date": days_away,
        "severity_thresholds": {"critical_max_days_away": 2, "high_max_days_away": 7},
        "anchor_date": today.isoformat(),
    }

    return StockoutRiskResult(
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        stockout_date=stockout_date,
        order_by_date=order_by_date,
        suggested_order_quantity=suggested_order_quantity,
        severity=severity,
        safety_margin_gap=safety_margin_gap,
        lead_time_gap=lead_time_gap,
        trace=trace,
    )
