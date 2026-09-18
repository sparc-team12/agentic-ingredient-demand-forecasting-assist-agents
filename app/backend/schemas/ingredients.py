"""Pydantic schemas for the Ingredients & Suppliers Setup HTTP contract
(ACRI-61).

``SupplierUpdate``/``IngredientUpdate`` intentionally share the exact same
required-field shape as their ``*Create`` counterparts — **full-replace**
PUT semantics (tech-lead review MINOR finding), not partial/merge. Edit
forms in the frontend are always pre-filled from the already-fetched list
and resubmit the complete current object, so a field omitted from a `PUT`
payload is a client bug (rejected as `422` by Pydantic), never silently
interpreted as "leave the existing value unchanged".
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SupplierBase(BaseModel):
    """Shared shape for `SupplierCreate` and `SupplierUpdate` (full-replace)."""

    name: str
    lead_time_days: int = Field(ge=0)
    safety_margin_days: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def name_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value


class SupplierCreate(SupplierBase):
    """Request body for `POST /suppliers`."""


class SupplierUpdate(SupplierBase):
    """Request body for `PUT /suppliers/{id}` — full-replace semantics, see
    module docstring."""


class SupplierSummary(BaseModel):
    """Nested supplier summary embedded in `IngredientOut` (AC2/AC3)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    lead_time_days: int


class SupplierOut(SupplierBase):
    """Response body for supplier list/create/update endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class IngredientBase(BaseModel):
    """Shared shape for `IngredientCreate` and `IngredientUpdate`
    (full-replace)."""

    name: str
    unit: str
    unit_cost: float = Field(ge=0)
    perishable: bool = False
    shelf_life_days: int | None = Field(default=None, gt=0)
    supplier_id: int | None = None
    safety_margin_days_override: int | None = Field(default=None, ge=0)

    @field_validator("name", "unit")
    @classmethod
    def field_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def perishable_requires_shelf_life(self) -> IngredientBase:
        """AC1 cross-field rule: a perishable ingredient must carry a shelf
        life; surfaced as a standard FastAPI `422`."""
        if self.perishable and self.shelf_life_days is None:
            raise ValueError("shelf_life_days is required when perishable is true")
        return self


class IngredientCreate(IngredientBase):
    """Request body for `POST /ingredients`."""


class IngredientUpdate(IngredientBase):
    """Request body for `PUT /ingredients/{id}` — full-replace semantics,
    see module docstring."""


class IngredientOut(BaseModel):
    """Response body for ingredient list/create/update endpoints.

    Carries the raw stored fields plus the server-computed, never-persisted
    fields that drive the AC3/AC4/AC5 UI: ``has_supplier``,
    ``effective_safety_margin_days``, ``safety_margin_source``, and
    ``safety_margin_gap``.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit: str
    unit_cost: float
    perishable: bool
    shelf_life_days: int | None
    supplier_id: int | None
    safety_margin_days_override: int | None
    supplier: SupplierSummary | None
    has_supplier: bool
    effective_safety_margin_days: int | None
    safety_margin_source: str | None
    safety_margin_gap: bool
