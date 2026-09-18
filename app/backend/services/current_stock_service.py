"""Business logic for the Current Stock Setup screen (ACRI-62).

Responsibility: build the one-row-per-ingredient snapshot view (AC1) and
upsert (never append-log) a single ingredient's quantity-on-hand/use-by-date
(AC2). No HTTP concerns here — those live in `routes/current_stock.py`.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import CurrentStock, Ingredient
from schemas.current_stock import CurrentStockOut, CurrentStockUpdate

logger = logging.getLogger(__name__)


def _to_current_stock_out(ingredient: Ingredient, stock: CurrentStock | None) -> CurrentStockOut:
    has_stock_recorded = stock is not None
    use_by_date = stock.use_by_date if stock is not None else None
    return CurrentStockOut(
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        unit=ingredient.unit,
        perishable=ingredient.perishable,
        quantity_on_hand=stock.quantity_on_hand if stock is not None else None,
        use_by_date=use_by_date,
        has_stock_recorded=has_stock_recorded,
        use_by_date_gap=ingredient.perishable and use_by_date is None,
    )


def list_current_stock(db: Session) -> list[CurrentStockOut]:
    """`GET /current-stock` — AC1/AC2, one row per `Ingredient` (ordered by
    name), joined with its snapshot (if any)."""
    ingredients = db.execute(select(Ingredient).order_by(Ingredient.name)).scalars().all()
    stocks_by_ingredient_id = {
        stock.ingredient_id: stock for stock in db.execute(select(CurrentStock)).scalars().all()
    }
    return [
        _to_current_stock_out(ingredient, stocks_by_ingredient_id.get(ingredient.id))
        for ingredient in ingredients
    ]


def upsert_current_stock(
    db: Session, ingredient_id: int, payload: CurrentStockUpdate
) -> CurrentStockOut:
    """`PUT /current-stock/{ingredient_id}` — AC2. Creates the snapshot row
    if none exists yet, otherwise updates the existing one in place (never
    a log entry). Raises `404` for a nonexistent ingredient."""
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")

    stock = db.execute(
        select(CurrentStock).where(CurrentStock.ingredient_id == ingredient_id)
    ).scalar_one_or_none()
    if stock is None:
        stock = CurrentStock(ingredient_id=ingredient_id, quantity_on_hand=0)
        db.add(stock)

    stock.quantity_on_hand = payload.quantity_on_hand
    stock.use_by_date = payload.use_by_date
    db.commit()
    db.refresh(stock)
    logger.info("current_stock_upserted", extra={"ingredient_id": ingredient_id})
    return _to_current_stock_out(ingredient, stock)


def count_recorded_stock(db: Session) -> int:
    """Used by `services/data_setup_service.py` for the ACRI-59 hub's
    loaded/not-loaded status (at least 1 snapshot row exists)."""
    return db.execute(select(func.count()).select_from(CurrentStock)).scalar_one()
