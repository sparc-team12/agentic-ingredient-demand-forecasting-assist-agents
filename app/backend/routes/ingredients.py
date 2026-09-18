"""Supplier and Ingredient HTTP routes (ACRI-61).

Two `APIRouter`s (`suppliers_router`, `ingredients_router`), both depending
on `middleware.auth.get_current_user` — reused verbatim (unmodified), the
identical gating pattern already used by `routes/screens.py`. No
persona-based branching: both personas get identical access.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.ingredients import (
    IngredientCreate,
    IngredientOut,
    IngredientUpdate,
    SupplierCreate,
    SupplierOut,
    SupplierUpdate,
)
from services import ingredient_service

suppliers_router = APIRouter(prefix="/suppliers", tags=["suppliers"])
ingredients_router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@suppliers_router.get("", response_model=list[SupplierOut])
def get_suppliers(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[SupplierOut]:
    return ingredient_service.list_suppliers(db)


@suppliers_router.post("", response_model=SupplierOut, status_code=201)
def post_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SupplierOut:
    return ingredient_service.create_supplier(db, payload)


@suppliers_router.put("/{supplier_id}", response_model=SupplierOut)
def put_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SupplierOut:
    return ingredient_service.update_supplier(db, supplier_id, payload)


@ingredients_router.get("", response_model=list[IngredientOut])
def get_ingredients(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[IngredientOut]:
    return ingredient_service.list_ingredients(db)


@ingredients_router.post("", response_model=IngredientOut, status_code=201)
def post_ingredient(
    payload: IngredientCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> IngredientOut:
    return ingredient_service.create_ingredient(db, payload)


@ingredients_router.put("/{ingredient_id}", response_model=IngredientOut)
def put_ingredient(
    ingredient_id: int,
    payload: IngredientUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> IngredientOut:
    return ingredient_service.update_ingredient(db, ingredient_id, payload)
