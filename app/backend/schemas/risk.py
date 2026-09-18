"""Pydantic schemas for the Stockout/Spoilage Risk HTTP contract (ACRI-38
US-003, ACRI-39 US-004, ACRI-40 US-005, ACRI-41 US-006, ACRI-42 US-007,
ACRI-43 US-008, ACRI-44 US-009, ACRI-64 US-029).

Mirrors `services/stockout_risk_service.py::StockoutRiskResult`,
`services/spoilage_risk_service.py::SpoilageRiskResult`, and
`services/risk_config_service.py`'s `RiskConfig` row one-to-one (via
`from_attributes=True`), same pattern as `schemas/demand_projection.py`.
`trace` is intentionally a free-form `dict` so every input value cited by
each service's docstring is visible over HTTP, not just the computed
figures.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskConfigOut(BaseModel):
    """Response body for `GET /risk-config` and `PUT /risk-config` (ACRI-44
    US-009)."""

    model_config = ConfigDict(from_attributes=True)

    materiality_threshold_inr: float


class RiskConfigUpdate(BaseModel):
    """Request body for `PUT /risk-config` (ACRI-44 US-009)."""

    materiality_threshold_inr: float = Field(ge=0)


class StockoutRiskOut(BaseModel):
    """One ingredient's stockout risk (ACRI-38/39/40/41), when at risk."""

    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    ingredient_name: str
    stockout_date: date
    order_by_date: date
    suggested_order_quantity: float
    severity: str
    safety_margin_gap: bool
    lead_time_gap: bool
    trace: dict[str, Any]


class SpoilageRiskOut(BaseModel):
    """One ingredient's spoilage risk (ACRI-42/43/44/64), when at risk."""

    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    ingredient_name: str
    use_by_date: date
    waste_cost_inr: float
    severity: str
    suppressed: bool
    trace: dict[str, Any]


class IngredientRiskOut(BaseModel):
    """Response body for `GET /ingredients/{id}/risk` — either/both/neither
    of `stockout`/`spoilage` may be `null` (dual-flag stacking rule owned by
    the caller/frontend, not this schema)."""

    model_config = ConfigDict(from_attributes=True)

    stockout: StockoutRiskOut | None
    spoilage: SpoilageRiskOut | None
