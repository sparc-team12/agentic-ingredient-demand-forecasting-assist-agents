"""Dish and recipe-line HTTP routes (ACRI-60).

One `APIRouter` (`dishes_router`), depending on
`middleware.auth.get_current_user` — reused verbatim, the identical gating
pattern already used by `routes/ingredients.py`. No persona-based branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.menu_recipe import (
    DishCreate,
    DishOut,
    DishUpdate,
    DishWithRecipeOut,
    RecipeLineCreate,
    RecipeLineOut,
    RecipeLineUpdate,
)
from services import menu_recipe_service

dishes_router = APIRouter(prefix="/dishes", tags=["dishes"])


@dishes_router.get("", response_model=list[DishWithRecipeOut])
def get_dishes(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[DishWithRecipeOut]:
    return menu_recipe_service.list_dishes(db)


@dishes_router.post("", response_model=DishOut, status_code=201)
def post_dish(
    payload: DishCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DishOut:
    return menu_recipe_service.create_dish(db, payload)


@dishes_router.put("/{dish_id}", response_model=DishOut)
def put_dish(
    dish_id: int,
    payload: DishUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DishOut:
    return menu_recipe_service.update_dish(db, dish_id, payload)


@dishes_router.post("/{dish_id}/recipe-lines", response_model=RecipeLineOut, status_code=201)
def post_recipe_line(
    dish_id: int,
    payload: RecipeLineCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RecipeLineOut:
    return menu_recipe_service.create_recipe_line(db, dish_id, payload)


@dishes_router.put("/{dish_id}/recipe-lines/{line_id}", response_model=RecipeLineOut)
def put_recipe_line(
    dish_id: int,
    line_id: int,
    payload: RecipeLineUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RecipeLineOut:
    return menu_recipe_service.update_recipe_line(db, dish_id, line_id, payload)
