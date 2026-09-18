"""Business logic for the Sales History Import screen (ACRI-63).

Responsibility: manual add-record CRUD (create only — no delete/edit is
specified for this story) for `SalesHistoryRecord`, and the per-dish
distinct-days-of-history computation/flag (AC2). No HTTP concerns here —
those live in `routes/sales_history.py`.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Dish, SalesHistoryRecord
from schemas.sales_history import (
    TARGET_DAYS_OF_HISTORY,
    DishSalesHistoryOut,
    SalesHistoryRecordCreate,
    SalesHistoryRecordOut,
)

logger = logging.getLogger(__name__)


def _to_dish_sales_history_out(dish: Dish) -> DishSalesHistoryOut:
    records = sorted(dish.sales_history_records, key=lambda record: record.sale_date)
    distinct_days = len({record.sale_date for record in records})
    return DishSalesHistoryOut(
        dish_id=dish.id,
        dish_name=dish.name,
        distinct_days_of_history=distinct_days,
        has_full_history=distinct_days >= TARGET_DAYS_OF_HISTORY,
        records=[SalesHistoryRecordOut.model_validate(record) for record in records],
    )


def list_sales_history(db: Session) -> list[DishSalesHistoryOut]:
    """`GET /sales-history` — AC1/AC2, one entry per `Dish` ordered by
    name, each with its full daily record list and computed history
    coverage."""
    dishes = db.execute(select(Dish).order_by(Dish.name)).scalars().all()
    return [_to_dish_sales_history_out(dish) for dish in dishes]


def create_sales_history_record(
    db: Session, payload: SalesHistoryRecordCreate
) -> SalesHistoryRecordOut:
    """`POST /sales-history` — AC1. Raises `422` for a nonexistent
    `dish_id`, `409` for a duplicate `(dish_id, sale_date)` entry."""
    if db.get(Dish, payload.dish_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="dish_id does not reference an existing dish",
        )
    record = SalesHistoryRecord(
        dish_id=payload.dish_id,
        sale_date=payload.sale_date,
        units_sold=payload.units_sold,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A sales history record already exists for this dish and date",
        ) from exc
    db.refresh(record)
    logger.info(
        "sales_history_record_created",
        extra={"dish_id": record.dish_id, "sale_date": str(record.sale_date)},
    )
    return SalesHistoryRecordOut.model_validate(record)


def count_sales_history_records(db: Session) -> int:
    """Used by `services/data_setup_service.py` for the ACRI-59 hub's
    loaded/not-loaded status (at least 1 record exists)."""
    return db.execute(select(func.count()).select_from(SalesHistoryRecord)).scalar_one()
