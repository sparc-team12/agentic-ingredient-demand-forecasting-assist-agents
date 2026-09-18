"""Pydantic schemas for the Menu & Recipe Setup HTTP contract (ACRI-60).

``RecipeLineUpdate`` mirrors ``RecipeLineCreate`` exactly (full-replace
`PUT` semantics), same convention as ``schemas/ingredients.py``.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DishBase(BaseModel):
    """Shared shape for `DishCreate` and `DishUpdate` (full-replace)."""

    name: str

    @field_validator("name")
    @classmethod
    def name_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value


class DishCreate(DishBase):
    """Request body for `POST /dishes`."""


class DishUpdate(DishBase):
    """Request body for `PUT /dishes/{id}` — full-replace, see module
    docstring."""


class RecipeLineBase(BaseModel):
    """Shared shape for `RecipeLineCreate` and `RecipeLineUpdate`
    (full-replace).

    ``ingredient_name`` is free text, not constrained to an existing
    `Ingredient` — a name with no match in the `Ingredient` table is
    accepted and flagged (AC2), never rejected.
    """

    ingredient_name: str
    quantity_per_serving: float = Field(gt=0)
    unit: str

    @field_validator("ingredient_name", "unit")
    @classmethod
    def field_must_be_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class RecipeLineCreate(RecipeLineBase):
    """Request body for `POST /dishes/{dish_id}/recipe-lines`."""


class RecipeLineUpdate(RecipeLineBase):
    """Request body for `PUT /dishes/{dish_id}/recipe-lines/{line_id}` —
    full-replace, see module docstring."""


class RecipeLineOut(BaseModel):
    """Response body for a recipe line, carrying the server-resolved,
    never-persisted-as-a-choice ``ingredient_flagged`` field (AC2) driven by
    whether ``ingredient_id`` resolved to an existing `Ingredient`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    ingredient_name: str
    ingredient_id: int | None
    quantity_per_serving: float
    unit: str
    ingredient_flagged: bool


class DishOut(BaseModel):
    """Response body for `POST /dishes` / `PUT /dishes/{id}` — dish only,
    no nested recipe (see `DishWithRecipeOut` for the full-recipe list
    view)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class DishWithRecipeOut(DishOut):
    """Response body for `GET /dishes` (AC1) — each dish's full recipe,
    viewable in full, never summarized/truncated."""

    recipe_lines: list[RecipeLineOut]
