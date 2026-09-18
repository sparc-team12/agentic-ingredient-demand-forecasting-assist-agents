"""Pydantic schemas for the Sales History Import HTTP contract (ACRI-63)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

TARGET_DAYS_OF_HISTORY = 84
"""12 weeks x 7 days (AC2's "flag if <84")."""


class SalesHistoryRecordCreate(BaseModel):
    """Request body for `POST /sales-history` (manual add-record form)."""

    dish_id: int
    sale_date: date
    units_sold: int = Field(ge=0)


class SalesHistoryRecordOut(BaseModel):
    """A single day's units-sold record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    sale_date: date
    units_sold: int


class DishSalesHistoryOut(BaseModel):
    """Response body for `GET /sales-history` (AC1/AC2) — one entry per
    `Dish`, its full (never summarized) daily records, the computed
    ``distinct_days_of_history`` count, and the AC2
    ``has_full_history`` flag (``distinct_days_of_history >= 84``)."""

    model_config = ConfigDict(from_attributes=True)

    dish_id: int
    dish_name: str
    distinct_days_of_history: int
    has_full_history: bool
    records: list[SalesHistoryRecordOut]
