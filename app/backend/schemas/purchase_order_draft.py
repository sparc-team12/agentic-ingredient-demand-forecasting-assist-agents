"""Pydantic schema for the Purchase Order Draft HTTP contract (ACRI-53
US-018).

Mirrors `services/purchase_order_draft_service.py::PurchaseOrderDraftResult`
one-to-one (via `from_attributes=True`), same pattern as
`schemas/demand_projection.py` and `schemas/risk.py`. `supplier_name` is
nullable and `supplier_gap` is always surfaced alongside it (never silently
defaulted) when the ingredient has no supplier mapped — same convention as
`StockoutRiskOut.lead_time_gap`.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class PurchaseOrderDraftOut(BaseModel):
    """Response body for `GET /ingredients/{id}/purchase-order-draft`
    (ACRI-53 US-018 AC1) — only returned for a stockout-flagged ingredient
    with a recorded `CurrentStock` snapshot; a `404` is raised otherwise
    (see `routes/purchase_order_draft.py`)."""

    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    item_name: str
    unit: str
    supplier_name: str | None
    supplier_gap: bool
    suggested_quantity: float
    required_delivery_date: date
