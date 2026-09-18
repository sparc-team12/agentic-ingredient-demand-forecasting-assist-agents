"""Pydantic schemas for the Risk Dashboard aggregation HTTP contract
(ACRI-54 US-019, ACRI-55 US-020, ACRI-56 US-021, ACRI-57 US-022, ACRI-58
US-023).

Mirrors `services/dashboard_service.py`'s output one-to-one, same
`from_attributes=True` pattern used by `schemas/risk.py`.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DashboardRiskRow(BaseModel):
    """One at-risk ingredient row (ACRI-55 US-020/ACRI-56 US-021/ACRI-57
    US-022): exactly one risk type per row — an ingredient flagged for both
    stockout and spoilage appears as 2 separate rows, one per type, each
    independently ranked (see `services/dashboard_service.py`'s ranking
    rule). `order_by_date` is populated only for `risk_type: "stockout"`
    rows; `waste_cost_inr` only for `risk_type: "spoilage"` rows.
    `suppressed` is always `False` for stockout rows (suppression is a
    spoilage-only, materiality-threshold concept)."""

    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    ingredient_name: str
    risk_type: Literal["stockout", "spoilage"]
    severity: str
    order_by_date: date | None
    waste_cost_inr: float | None
    suppressed: bool


class DashboardRiskSummaryOut(BaseModel):
    """Response body for `GET /dashboard/risk-summary` (ACRI-54..58).

    `total_waste_exposure_inr` (ACRI-58 US-023) always sums every
    spoilage-risk ingredient's waste cost, *including* ones suppressed by
    the materiality threshold — never filtered. `rows` is the full
    severity-ordered list (both risk types, including suppressed spoilage
    rows, each tagged); the Risk Dashboard's visible table filters
    `suppressed` rows out before rendering (ACRI-44 US-009's "hidden from
    the list below" rule) — a frontend display concern, not a backend
    omission, so the raw data stays fully traceable end to end.
    `materiality_threshold_inr` is the live-adjustable value from
    `GET/PUT /risk-config`, echoed here so the dashboard doesn't need a
    second round-trip just to render its threshold control."""

    model_config = ConfigDict(from_attributes=True)

    total_waste_exposure_inr: float
    rows: list[DashboardRiskRow]
    materiality_threshold_inr: float
