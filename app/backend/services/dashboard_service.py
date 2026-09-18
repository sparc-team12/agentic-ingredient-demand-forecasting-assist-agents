"""Business logic for the Risk Dashboard aggregation endpoint (ACRI-54
US-019, ACRI-55 US-020, ACRI-56 US-021, ACRI-57 US-022, ACRI-58 US-023).

Responsibility: iterate every `Ingredient` row (a fixed ~30-40 row demo
dataset per the implementation plan — no async/background jobs needed,
just a synchronous loop) and evaluate both
`services/stockout_risk_service.py::evaluate_stockout_risk` and
`services/spoilage_risk_service.py::evaluate_spoilage_risk` for each,
combining the results into the single severity-ordered list the Risk
Dashboard renders, plus the always-unfiltered aggregate waste-exposure
total. No HTTP concerns here — those live in `routes/dashboard.py`.

Ranking rule (ACRI-54 US-019 AC3 — tie-break chosen by Development, per the
story's explicit invitation to use judgment and document the exact rule):

1. Severity band first, across both risk types: Critical > High > Low. A
   Critical spoilage row always ranks above a High stockout row (and any
   Low row of either type), because severity band is compared *before*
   anything else.
2. Within the same severity band: risk type, stockout rows before spoilage
   rows. Interleaving a date-based key (stockout) and a cost-based key
   (spoilage) on one shared axis would need an arbitrary, undocumented
   conversion (e.g. INR-per-day-of-urgency) to be meaningful; keeping each
   type's own natural ordering intact and grouping stockout-then-spoilage
   within the tied band is the more honest, explainable rule.
3. Within the same severity band and risk type: stockout rows by
   `order_by_date` ascending (soonest first, ACRI-56 US-021 AC); spoilage
   rows by `waste_cost_inr` descending (highest cost first, ACRI-57 US-022
   AC).

Suppression (ACRI-58 US-023 / ACRI-44 US-009): `total_waste_exposure_inr`
sums *every* spoilage-risk ingredient's `waste_cost_inr`, including ones
below the current materiality threshold (`suppressed=True`) — this sum
never filters. Every at-risk row (both types) is still included in `rows`,
tagged with its own `suppressed` flag; the caller (the Risk Dashboard's
table) is responsible for filtering `suppressed` rows out of what it
renders, so the underlying data stays fully traceable rather than silently
dropped server-side.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Ingredient
from schemas.dashboard import DashboardRiskRow, DashboardRiskSummaryOut
from services import risk_config_service, spoilage_risk_service, stockout_risk_service

_SEVERITY_RANK = {"Critical": 0, "High": 1, "Low": 2}
_TYPE_RANK = {"stockout": 0, "spoilage": 1}


def _sort_key(row: DashboardRiskRow) -> tuple[int, int, date | float]:
    """The exact tie-break rule documented in the module docstring above.
    Safe against cross-type comparison at the tertiary position: rows with
    a different `risk_type` already differ at the (lower-priority) 2nd
    tuple element, so Python's element-by-element tuple comparison never
    reaches the 3rd element (a `date` for stockout, a negated `float` for
    spoilage) across two rows of different types."""
    severity_rank = _SEVERITY_RANK[row.severity]
    type_rank = _TYPE_RANK[row.risk_type]
    if row.risk_type == "stockout":
        assert row.order_by_date is not None
        tertiary: date | float = row.order_by_date
    else:
        tertiary = -(row.waste_cost_inr or 0.0)
    return (severity_rank, type_rank, tertiary)


def get_risk_summary(db: Session, *, anchor: date | None = None) -> DashboardRiskSummaryOut:
    """`GET /dashboard/risk-summary` (ACRI-54..58). `anchor` defaults to
    `date.today()`; passing it explicitly keeps pure unit tests free of a
    wall-clock read, mirroring `evaluate_stockout_risk`/
    `evaluate_spoilage_risk`."""
    ingredients = db.execute(select(Ingredient)).scalars().all()
    materiality_threshold_inr = risk_config_service.get_materiality_threshold(db)

    total_waste_exposure_inr = 0.0
    rows: list[DashboardRiskRow] = []

    for ingredient in ingredients:
        stockout = stockout_risk_service.evaluate_stockout_risk(ingredient.id, db, anchor=anchor)
        if stockout is not None:
            rows.append(
                DashboardRiskRow(
                    ingredient_id=stockout.ingredient_id,
                    ingredient_name=stockout.ingredient_name,
                    risk_type="stockout",
                    severity=stockout.severity,
                    order_by_date=stockout.order_by_date,
                    waste_cost_inr=None,
                    suppressed=False,
                )
            )

        spoilage = spoilage_risk_service.evaluate_spoilage_risk(ingredient.id, db, anchor=anchor)
        if spoilage is not None:
            total_waste_exposure_inr += spoilage.waste_cost_inr
            rows.append(
                DashboardRiskRow(
                    ingredient_id=spoilage.ingredient_id,
                    ingredient_name=spoilage.ingredient_name,
                    risk_type="spoilage",
                    severity=spoilage.severity,
                    order_by_date=None,
                    waste_cost_inr=spoilage.waste_cost_inr,
                    suppressed=spoilage.suppressed,
                )
            )

    ordered_rows = sorted(rows, key=_sort_key)

    return DashboardRiskSummaryOut(
        total_waste_exposure_inr=total_waste_exposure_inr,
        rows=ordered_rows,
        materiality_threshold_inr=materiality_threshold_inr,
    )
