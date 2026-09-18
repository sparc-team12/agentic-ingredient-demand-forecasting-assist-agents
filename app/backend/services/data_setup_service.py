"""Business logic for the Data Setup Hub screen (ACRI-59).

Responsibility: compute the loaded/not-loaded status of each of the 4 Data
Setup categories (AC1/AC2). Reads the other categories' own tables
directly (`Ingredient` here; `Dish`/`CurrentStock`/`SalesHistoryRecord` via
their own services' `count_*` helpers) rather than duplicating their
business logic. No HTTP concerns here — those live in
`routes/data_setup.py`.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Ingredient
from schemas.data_setup import DataSetupCategoryStatus, DataSetupStatusOut
from services import current_stock_service, menu_recipe_service, sales_history_service


def _count_ingredients(db: Session) -> int:
    return db.execute(select(func.count()).select_from(Ingredient)).scalar_one()


def get_data_setup_status(db: Session) -> DataSetupStatusOut:
    """`GET /data-setup/status` — AC1/AC2. ``loaded`` means "at least 1 row
    exists"; never conflated with "complete"."""
    categories = [
        DataSetupCategoryStatus(
            id="menu-recipe",
            label="Menu & Recipe Setup",
            path="/data-setup/menu-recipe-setup",
            loaded=menu_recipe_service.count_dishes(db) > 0,
        ),
        DataSetupCategoryStatus(
            id="ingredients-suppliers",
            label="Ingredients & Suppliers Setup",
            path="/data-setup/ingredients-suppliers",
            loaded=_count_ingredients(db) > 0,
        ),
        DataSetupCategoryStatus(
            id="current-stock",
            label="Current Stock Setup",
            path="/data-setup/current-stock-setup",
            loaded=current_stock_service.count_recorded_stock(db) > 0,
        ),
        DataSetupCategoryStatus(
            id="sales-history",
            label="Sales History Import",
            path="/data-setup/sales-history-import",
            loaded=sales_history_service.count_sales_history_records(db) > 0,
        ),
    ]
    return DataSetupStatusOut(
        categories=categories,
        all_loaded=all(category.loaded for category in categories),
    )
