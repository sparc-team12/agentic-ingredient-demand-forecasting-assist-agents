"""Business logic for the Ingredients & Suppliers Setup screen (ACRI-61).

Responsibility: CRUD for `Supplier`/`Ingredient`, the server-side
supplier-existence validation for `Ingredient.supplier_id` (a DB lookup, so
it cannot live in a pure Pydantic validator), and the safety-margin
precedence/gap resolver used to build every `IngredientOut` (AC4/AC5). No
HTTP concerns here — those live in `routes/ingredients.py`, mirroring the
`services/auth_service.py` / `routes/auth.py` split already established by
ACRI-66.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Ingredient, Supplier
from schemas.ingredients import (
    IngredientCreate,
    IngredientOut,
    IngredientUpdate,
    SupplierCreate,
    SupplierOut,
    SupplierSummary,
    SupplierUpdate,
)

logger = logging.getLogger(__name__)


def resolve_safety_margin(
    ingredient: Ingredient, supplier: Supplier | None
) -> tuple[int | None, str | None]:
    """Pure precedence function (AC4/AC5), unit-tested in isolation.

    - the ingredient's own ``safety_margin_days_override`` wins when set;
    - else the mapped supplier's ``safety_margin_days`` when set;
    - else ``(None, None)`` — the value is **never** coerced to ``0``.
    """
    if ingredient.safety_margin_days_override is not None:
        return ingredient.safety_margin_days_override, "ingredient"
    if supplier is not None and supplier.safety_margin_days is not None:
        return supplier.safety_margin_days, "supplier"
    return None, None


def _to_ingredient_out(ingredient: Ingredient) -> IngredientOut:
    supplier = ingredient.supplier
    effective_value, source = resolve_safety_margin(ingredient, supplier)
    return IngredientOut(
        id=ingredient.id,
        name=ingredient.name,
        unit=ingredient.unit,
        unit_cost=ingredient.unit_cost,
        perishable=ingredient.perishable,
        shelf_life_days=ingredient.shelf_life_days,
        supplier_id=ingredient.supplier_id,
        safety_margin_days_override=ingredient.safety_margin_days_override,
        supplier=(
            SupplierSummary(
                id=supplier.id, name=supplier.name, lead_time_days=supplier.lead_time_days
            )
            if supplier is not None
            else None
        ),
        has_supplier=supplier is not None,
        effective_safety_margin_days=effective_value,
        safety_margin_source=source,
        safety_margin_gap=effective_value is None,
    )


def list_suppliers(db: Session) -> list[SupplierOut]:
    """`GET /suppliers` — AC2, ordered by name."""
    suppliers = db.execute(select(Supplier).order_by(Supplier.name)).scalars().all()
    return [SupplierOut.model_validate(supplier) for supplier in suppliers]


def create_supplier(db: Session, payload: SupplierCreate) -> SupplierOut:
    """`POST /suppliers` — AC2/AC4. Raises `409` on a duplicate name."""
    supplier = Supplier(
        name=payload.name,
        lead_time_days=payload.lead_time_days,
        safety_margin_days=payload.safety_margin_days,
    )
    db.add(supplier)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier with this name already exists",
        ) from exc
    db.refresh(supplier)
    logger.info("supplier_created", extra={"supplier_id": supplier.id})
    return SupplierOut.model_validate(supplier)


def update_supplier(db: Session, supplier_id: int, payload: SupplierUpdate) -> SupplierOut:
    """`PUT /suppliers/{id}` — full-replace semantics (tech-lead review
    MINOR finding): every field on `payload` is always applied, including
    a `None` `safety_margin_days`, since edit forms resubmit the complete,
    pre-filled object rather than a partial patch."""
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    supplier.name = payload.name
    supplier.lead_time_days = payload.lead_time_days
    supplier.safety_margin_days = payload.safety_margin_days
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier with this name already exists",
        ) from exc
    db.refresh(supplier)
    logger.info("supplier_updated", extra={"supplier_id": supplier.id})
    return SupplierOut.model_validate(supplier)


def _check_supplier_exists(db: Session, supplier_id: int | None) -> None:
    """Service-layer existence check for `Ingredient.supplier_id` (cannot be
    a pure Pydantic validator — requires a DB lookup). Raises `422`, not
    `404`, since this is request-body validation, not a resource lookup."""
    if supplier_id is None:
        return
    if db.get(Supplier, supplier_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="supplier_id does not reference an existing supplier",
        )


def list_ingredients(db: Session) -> list[IngredientOut]:
    """`GET /ingredients` — AC1/AC2/AC3/AC4/AC5, ordered by name."""
    ingredients = db.execute(select(Ingredient).order_by(Ingredient.name)).scalars().all()
    return [_to_ingredient_out(ingredient) for ingredient in ingredients]


def create_ingredient(db: Session, payload: IngredientCreate) -> IngredientOut:
    """`POST /ingredients`. Raises `422` for a nonexistent `supplier_id`,
    `409` on a duplicate name."""
    _check_supplier_exists(db, payload.supplier_id)
    ingredient = Ingredient(
        name=payload.name,
        unit=payload.unit,
        unit_cost=payload.unit_cost,
        perishable=payload.perishable,
        shelf_life_days=payload.shelf_life_days,
        supplier_id=payload.supplier_id,
        safety_margin_days_override=payload.safety_margin_days_override,
    )
    db.add(ingredient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ingredient with this name already exists",
        ) from exc
    db.refresh(ingredient)
    logger.info("ingredient_created", extra={"ingredient_id": ingredient.id})
    return _to_ingredient_out(ingredient)


def update_ingredient(db: Session, ingredient_id: int, payload: IngredientUpdate) -> IngredientOut:
    """`PUT /ingredients/{id}` — full-replace semantics (tech-lead review
    MINOR finding): every field on `payload` is always applied, including a
    `None` `supplier_id`/`safety_margin_days_override`. An edit that omits
    the supplier picker's selection un-maps the ingredient rather than
    silently preserving the prior mapping, since the form always resubmits
    the complete current object."""
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    _check_supplier_exists(db, payload.supplier_id)
    ingredient.name = payload.name
    ingredient.unit = payload.unit
    ingredient.unit_cost = payload.unit_cost
    ingredient.perishable = payload.perishable
    ingredient.shelf_life_days = payload.shelf_life_days
    ingredient.supplier_id = payload.supplier_id
    ingredient.safety_margin_days_override = payload.safety_margin_days_override
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ingredient with this name already exists",
        ) from exc
    db.refresh(ingredient)
    logger.info("ingredient_updated", extra={"ingredient_id": ingredient.id})
    return _to_ingredient_out(ingredient)
