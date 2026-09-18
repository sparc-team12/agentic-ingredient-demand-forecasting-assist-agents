"""Sales history HTTP routes (ACRI-63).

One `APIRouter` (`sales_history_router`), depending on
`middleware.auth.get_current_user` — reused verbatim. No persona-based
branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.sales_history import (
    DishSalesHistoryOut,
    SalesHistoryRecordCreate,
    SalesHistoryRecordOut,
)
from services import sales_history_service

sales_history_router = APIRouter(prefix="/sales-history", tags=["sales-history"])


@sales_history_router.get("", response_model=list[DishSalesHistoryOut])
def get_sales_history(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[DishSalesHistoryOut]:
    return sales_history_service.list_sales_history(db)


@sales_history_router.post("", response_model=SalesHistoryRecordOut, status_code=201)
def post_sales_history_record(
    payload: SalesHistoryRecordCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> SalesHistoryRecordOut:
    return sales_history_service.create_sales_history_record(db, payload)
