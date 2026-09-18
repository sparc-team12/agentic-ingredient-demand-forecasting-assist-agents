"""Pydantic schemas for the Current Stock Setup HTTP contract (ACRI-62)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CurrentStockUpdate(BaseModel):
    """Request body for `PUT /current-stock/{ingredient_id}` — upserts the
    single snapshot row for that ingredient (full-replace: a `None`
    `use_by_date` clears any previously recorded date)."""

    quantity_on_hand: float = Field(ge=0)
    use_by_date: date | None = None


class CurrentStockOut(BaseModel):
    """Response body for `GET /current-stock` (AC1/AC2) — one entry per
    existing `Ingredient`, whether or not a snapshot has been recorded yet.

    ``has_stock_recorded`` distinguishes "not loaded yet" from a genuine
    zero quantity. ``use_by_date_gap`` is the AC2 flag: a perishable
    ingredient with no recorded use-by date, never silently hidden.
    """

    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    ingredient_name: str
    unit: str
    perishable: bool
    quantity_on_hand: float | None
    use_by_date: date | None
    has_stock_recorded: bool
    use_by_date_gap: bool
