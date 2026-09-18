"""Current stock HTTP routes (ACRI-62).

One `APIRouter` (`current_stock_router`), depending on
`middleware.auth.get_current_user` — reused verbatim. No persona-based
branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.current_stock import CurrentStockOut, CurrentStockUpdate
from services import current_stock_service

current_stock_router = APIRouter(prefix="/current-stock", tags=["current-stock"])


@current_stock_router.get("", response_model=list[CurrentStockOut])
def get_current_stock(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[CurrentStockOut]:
    return current_stock_service.list_current_stock(db)


@current_stock_router.put("/{ingredient_id}", response_model=CurrentStockOut)
def put_current_stock(
    ingredient_id: int,
    payload: CurrentStockUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CurrentStockOut:
    return current_stock_service.upsert_current_stock(db, ingredient_id, payload)
