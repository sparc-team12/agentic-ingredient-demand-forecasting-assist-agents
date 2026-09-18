"""Standalone CLI: seed a full fixture-only demo scenario (dishes, recipes,
84 days of sales history, and current-stock snapshots) so the Risk
Dashboard, Ingredient Detail, and Purchase Order Draft screens have a
compelling, explainable story to show — a hackathon-demo dataset, not
production data.

Usage (from `app/backend`, with the venv activated):

    python -m scripts.seed_demo_scenario

Deliberately **not** wired into `main.py`'s startup lifespan, same rationale
as `scripts.seed_demo_ingredients`: opt-in only, for manual demo/smoke use.
Idempotent by name/date — safe to re-run.

Story this dataset tells:
- Roma Tomatoes: used by 2 growing-trend dishes, low stock on hand ->
  genuine STOCKOUT risk, Critical severity (order-by date already passed
  given the 3-day supplier lead time + 2-day safety margin).
- Fresh Basil: used by 2 dishes with declining recent demand, stocked well
  above what will be consumed before its short use-by date -> genuine
  SPOILAGE risk, High severity (a few hundred rupees of waste exposure).
- Basmati Rice: flat demand, ample stock -> no risk at all (the contrast
  case).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import CurrentStock, Dish, Ingredient, RecipeLine, SalesHistoryRecord
from db.session import Base, SessionLocal, engine

logger = logging.getLogger(__name__)

HISTORY_DAYS = 84
RECENT_WEEKS_DAYS = 28  # most-recent 4 weeks get the trend multiplier


@dataclass(frozen=True)
class _DishFixture:
    name: str
    weekday_base: float
    weekend_multiplier: float
    recent_trend_multiplier: float  # >1 growing, <1 declining, 1 flat
    recipe: list[tuple[str, float, str]]  # (ingredient_name, qty_per_serving, unit)


_DISHES: list[_DishFixture] = [
    _DishFixture(
        name="Margherita Pizza",
        weekday_base=15,
        weekend_multiplier=1.6,
        recent_trend_multiplier=1.4,
        recipe=[("Roma Tomatoes", 0.15, "kg"), ("Fresh Basil", 0.05, "bunch")],
    ),
    _DishFixture(
        name="Pasta Arrabbiata",
        weekday_base=12,
        weekend_multiplier=1.6,
        recent_trend_multiplier=1.4,
        recipe=[("Roma Tomatoes", 0.2, "kg")],
    ),
    _DishFixture(
        name="Chicken Biryani",
        weekday_base=10,
        weekend_multiplier=1.5,
        recent_trend_multiplier=1.0,
        recipe=[("Basmati Rice", 0.25, "kg")],
    ),
    _DishFixture(
        name="Caprese Salad",
        weekday_base=10,
        weekend_multiplier=1.4,
        recent_trend_multiplier=0.5,
        recipe=[("Roma Tomatoes", 0.12, "kg"), ("Fresh Basil", 0.06, "bunch")],
    ),
]

# (ingredient_name, quantity_on_hand, use_by_days_from_today_or_None)
_CURRENT_STOCK: list[tuple[str, float, int | None]] = [
    ("Roma Tomatoes", 15.0, 30),
    ("Fresh Basil", 25.0, 3),
    ("Basmati Rice", 100.0, None),
]

# Fresh Basil's original fixture unit_cost (0.9) is too low to produce a
# demo-legible waste-cost figure at a realistic stock quantity; bumped to a
# more representative per-bunch cost so the spoilage story is visible.
_INGREDIENT_UNIT_COST_OVERRIDES: dict[str, float] = {"Fresh Basil": 40.0}


def _daily_units(fixture: _DishFixture, day_offset_from_oldest: int, day: date) -> int:
    is_recent = day_offset_from_oldest >= (HISTORY_DAYS - RECENT_WEEKS_DAYS)
    trend = fixture.recent_trend_multiplier if is_recent else 1.0
    weekend = fixture.weekend_multiplier if day.weekday() >= 5 else 1.0
    return max(0, round(fixture.weekday_base * trend * weekend))


def seed_demo_scenario(db: Session) -> dict[str, int]:
    counts = {"dishes": 0, "recipe_lines": 0, "sales_history_records": 0, "current_stock": 0}

    ingredient_by_name: dict[str, Ingredient] = {
        i.name: i for i in db.execute(select(Ingredient)).scalars().all()
    }
    for name, cost in _INGREDIENT_UNIT_COST_OVERRIDES.items():
        ingredient = ingredient_by_name.get(name)
        if ingredient is not None and ingredient.unit_cost != cost:
            ingredient.unit_cost = cost

    today = date.today()
    oldest_day = today - timedelta(days=HISTORY_DAYS)

    for fixture in _DISHES:
        dish = db.execute(select(Dish).where(Dish.name == fixture.name)).scalar_one_or_none()
        if dish is None:
            dish = Dish(name=fixture.name)
            db.add(dish)
            db.flush()
            counts["dishes"] += 1

        for ingredient_name, qty, unit in fixture.recipe:
            existing_line = db.execute(
                select(RecipeLine).where(
                    RecipeLine.dish_id == dish.id, RecipeLine.ingredient_name == ingredient_name
                )
            ).scalar_one_or_none()
            if existing_line is None:
                ingredient = ingredient_by_name.get(ingredient_name)
                db.add(
                    RecipeLine(
                        dish_id=dish.id,
                        ingredient_name=ingredient_name,
                        ingredient_id=ingredient.id if ingredient is not None else None,
                        quantity_per_serving=qty,
                        unit=unit,
                    )
                )
                counts["recipe_lines"] += 1

        existing_days = {
            r.sale_date
            for r in db.execute(
                select(SalesHistoryRecord).where(SalesHistoryRecord.dish_id == dish.id)
            )
            .scalars()
            .all()
        }
        for offset in range(HISTORY_DAYS):
            day = oldest_day + timedelta(days=offset)
            if day in existing_days:
                continue
            db.add(
                SalesHistoryRecord(
                    dish_id=dish.id,
                    sale_date=day,
                    units_sold=_daily_units(fixture, offset, day),
                )
            )
            counts["sales_history_records"] += 1

    for ingredient_name, quantity_on_hand, use_by_offset in _CURRENT_STOCK:
        ingredient = ingredient_by_name.get(ingredient_name)
        if ingredient is None:
            continue
        existing_stock = db.execute(
            select(CurrentStock).where(CurrentStock.ingredient_id == ingredient.id)
        ).scalar_one_or_none()
        use_by_date = today + timedelta(days=use_by_offset) if use_by_offset is not None else None
        if existing_stock is None:
            db.add(
                CurrentStock(
                    ingredient_id=ingredient.id,
                    quantity_on_hand=quantity_on_hand,
                    use_by_date=use_by_date,
                )
            )
            counts["current_stock"] += 1
        else:
            existing_stock.quantity_on_hand = quantity_on_hand
            existing_stock.use_by_date = use_by_date

    db.commit()
    return counts


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        counts = seed_demo_scenario(db)
        logger.info("seed_demo_scenario: %s", counts)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
