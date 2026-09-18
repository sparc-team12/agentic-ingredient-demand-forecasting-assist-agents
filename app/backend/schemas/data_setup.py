"""Pydantic schemas for the Data Setup Hub HTTP contract (ACRI-59)."""

from __future__ import annotations

from pydantic import BaseModel


class DataSetupCategoryStatus(BaseModel):
    """Loaded/not-loaded status for one of the 4 Data Setup categories.

    ``loaded`` is true when at least 1 row exists in that category's table
    (AC1) — never a proxy for "fully loaded"/complete, just "has any data".
    """

    id: str
    label: str
    path: str
    loaded: bool


class DataSetupStatusOut(BaseModel):
    """Response body for `GET /data-setup/status` — all 4 categories plus
    the AC2 all-loaded flag (true only when every category is loaded)."""

    categories: list[DataSetupCategoryStatus]
    all_loaded: bool
