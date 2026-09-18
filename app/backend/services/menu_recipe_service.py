"""Business logic for the Menu & Recipe Setup screen (ACRI-60).

Responsibility: CRUD for `Dish`/`RecipeLine` and the ingredient-name
resolution/flag logic used to build every `RecipeLineOut` (AC2). No HTTP
concerns here — those live in `routes/menu_recipe.py`, mirroring the
`services/ingredient_service.py` / `routes/ingredients.py` split.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Dish, Ingredient, RecipeLine
from schemas.menu_recipe import (
    DishCreate,
    DishOut,
    DishUpdate,
    DishWithRecipeOut,
    RecipeLineCreate,
    RecipeLineOut,
    RecipeLineUpdate,
)

logger = logging.getLogger(__name__)


def resolve_ingredient_id(db: Session, ingredient_name: str) -> int | None:
    """Pure-ish lookup (AC2): case-insensitive exact match of
    ``ingredient_name`` against `Ingredient.name`. Returns `None` — never
    raises — when there is no match, so the recipe line is stored and
    flagged rather than rejected."""
    ingredient = db.execute(
        select(Ingredient).where(func.lower(Ingredient.name) == ingredient_name.strip().lower())
    ).scalar_one_or_none()
    return ingredient.id if ingredient is not None else None


def _to_recipe_line_out(line: RecipeLine) -> RecipeLineOut:
    return RecipeLineOut(
        id=line.id,
        dish_id=line.dish_id,
        ingredient_name=line.ingredient_name,
        ingredient_id=line.ingredient_id,
        quantity_per_serving=line.quantity_per_serving,
        unit=line.unit,
        ingredient_flagged=line.ingredient_id is None,
    )


def _to_dish_with_recipe_out(dish: Dish) -> DishWithRecipeOut:
    return DishWithRecipeOut(
        id=dish.id,
        name=dish.name,
        created_at=dish.created_at,
        recipe_lines=[_to_recipe_line_out(line) for line in dish.recipe_lines],
    )


def list_dishes(db: Session) -> list[DishWithRecipeOut]:
    """`GET /dishes` — AC1, ordered by name, each with its full (never
    summarized) recipe."""
    dishes = db.execute(select(Dish).order_by(Dish.name)).scalars().all()
    return [_to_dish_with_recipe_out(dish) for dish in dishes]


def create_dish(db: Session, payload: DishCreate) -> DishOut:
    """`POST /dishes`. Raises `409` on a duplicate name."""
    dish = Dish(name=payload.name)
    db.add(dish)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Dish with this name already exists"
        ) from exc
    db.refresh(dish)
    logger.info("dish_created", extra={"dish_id": dish.id})
    return DishOut.model_validate(dish)


def update_dish(db: Session, dish_id: int, payload: DishUpdate) -> DishOut:
    """`PUT /dishes/{id}` — full-replace (name only)."""
    dish = db.get(Dish, dish_id)
    if dish is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
    dish.name = payload.name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Dish with this name already exists"
        ) from exc
    db.refresh(dish)
    logger.info("dish_updated", extra={"dish_id": dish.id})
    return DishOut.model_validate(dish)


def _get_dish_or_404(db: Session, dish_id: int) -> Dish:
    dish = db.get(Dish, dish_id)
    if dish is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
    return dish


def create_recipe_line(db: Session, dish_id: int, payload: RecipeLineCreate) -> RecipeLineOut:
    """`POST /dishes/{dish_id}/recipe-lines` — AC1/AC2. Never rejects an
    unmatched ``ingredient_name``; it is stored and flagged instead."""
    _get_dish_or_404(db, dish_id)
    ingredient_id = resolve_ingredient_id(db, payload.ingredient_name)
    line = RecipeLine(
        dish_id=dish_id,
        ingredient_name=payload.ingredient_name,
        ingredient_id=ingredient_id,
        quantity_per_serving=payload.quantity_per_serving,
        unit=payload.unit,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    logger.info("recipe_line_created", extra={"dish_id": dish_id, "recipe_line_id": line.id})
    return _to_recipe_line_out(line)


def update_recipe_line(
    db: Session, dish_id: int, line_id: int, payload: RecipeLineUpdate
) -> RecipeLineOut:
    """`PUT /dishes/{dish_id}/recipe-lines/{line_id}` — full-replace. The
    ingredient match is re-resolved from the (possibly edited)
    ``ingredient_name`` every time."""
    _get_dish_or_404(db, dish_id)
    line = db.get(RecipeLine, line_id)
    if line is None or line.dish_id != dish_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe line not found")
    line.ingredient_name = payload.ingredient_name
    line.ingredient_id = resolve_ingredient_id(db, payload.ingredient_name)
    line.quantity_per_serving = payload.quantity_per_serving
    line.unit = payload.unit
    db.commit()
    db.refresh(line)
    logger.info("recipe_line_updated", extra={"dish_id": dish_id, "recipe_line_id": line.id})
    return _to_recipe_line_out(line)


def count_dishes(db: Session) -> int:
    """Used by `services/data_setup_service.py` for the ACRI-59 hub's
    loaded/not-loaded status (at least 1 row exists)."""
    return db.execute(select(func.count()).select_from(Dish)).scalar_one()
