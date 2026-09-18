"""Standalone CLI: create schema (if needed) and seed a fixture-only demo
suppliers/ingredients dataset (ACRI-61).

Usage (from `app/backend`, with the venv activated):

    python -m scripts.seed_demo_ingredients

Deliberately **not** wired into `main.py`'s startup lifespan (Assumption A6
in the implementation plan): a fresh dev/test database never silently gains
fake ingredient/supplier rows just by starting the backend server, unlike
`scripts/seed_demo_accounts.py` (whose accounts *are* required to log in at
all). This is opt-in only, for manual smoke-testing of the AC3 ("no mapped
supplier") and AC5 ("no safety margin") gap flags.

No real 30-40 ingredient / 3-5 supplier dataset exists anywhere in this
repository (per `requirements-validation.json`'s own sourcing note); this
fixture is a minimal, explicitly-labeled 2-supplier/3-ingredient set that
deliberately includes one un-mapped ingredient and one ingredient/supplier
pair with no safety margin value anywhere, so the gap-flag UI has something
real to demonstrate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Ingredient, Supplier
from db.session import Base, SessionLocal, engine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _SupplierFixture:
    name: str
    lead_time_days: int
    safety_margin_days: int | None


@dataclass(frozen=True)
class _IngredientFixture:
    name: str
    unit: str
    unit_cost: float
    perishable: bool
    shelf_life_days: int | None
    supplier_name: str | None
    safety_margin_days_override: int | None


# Fixture-only demo dataset. "Metro Wholesale Foods" deliberately has no
# `safety_margin_days`, and "Basmati Rice" (mapped to it, with no override
# of its own) exercises AC5's gap flag. "Fresh Basil" is deliberately left
# unmapped to exercise AC3's gap flag.
_SUPPLIERS: list[_SupplierFixture] = [
    _SupplierFixture(name="Acme Produce Co", lead_time_days=3, safety_margin_days=2),
    _SupplierFixture(name="Metro Wholesale Foods", lead_time_days=5, safety_margin_days=None),
]

_INGREDIENTS: list[_IngredientFixture] = [
    _IngredientFixture(
        name="Roma Tomatoes",
        unit="kg",
        unit_cost=2.5,
        perishable=True,
        shelf_life_days=7,
        supplier_name="Acme Produce Co",
        safety_margin_days_override=None,
    ),
    _IngredientFixture(
        name="Basmati Rice",
        unit="kg",
        unit_cost=1.8,
        perishable=False,
        shelf_life_days=None,
        supplier_name="Metro Wholesale Foods",
        safety_margin_days_override=None,
    ),
    _IngredientFixture(
        name="Fresh Basil",
        unit="bunch",
        unit_cost=0.9,
        perishable=True,
        shelf_life_days=3,
        supplier_name=None,
        safety_margin_days_override=None,
    ),
]


def seed_demo_ingredients(db: Session) -> tuple[int, int]:
    """Create the fixture-only demo suppliers/ingredients if they don't
    already exist (looked up by name). Idempotent — a repeat call is a
    no-op for rows already present. Returns
    `(suppliers_created, ingredients_created)`.
    """
    suppliers_created = 0
    supplier_by_name: dict[str, Supplier] = {}
    for supplier_fixture in _SUPPLIERS:
        existing = db.execute(
            select(Supplier).where(Supplier.name == supplier_fixture.name)
        ).scalar_one_or_none()
        if existing is not None:
            supplier_by_name[supplier_fixture.name] = existing
            continue
        supplier = Supplier(
            name=supplier_fixture.name,
            lead_time_days=supplier_fixture.lead_time_days,
            safety_margin_days=supplier_fixture.safety_margin_days,
        )
        db.add(supplier)
        db.flush()
        supplier_by_name[supplier_fixture.name] = supplier
        suppliers_created += 1

    ingredients_created = 0
    for ingredient_fixture in _INGREDIENTS:
        existing_ingredient = db.execute(
            select(Ingredient).where(Ingredient.name == ingredient_fixture.name)
        ).scalar_one_or_none()
        if existing_ingredient is not None:
            continue
        supplier_id = (
            supplier_by_name[ingredient_fixture.supplier_name].id
            if ingredient_fixture.supplier_name is not None
            else None
        )
        ingredient = Ingredient(
            name=ingredient_fixture.name,
            unit=ingredient_fixture.unit,
            unit_cost=ingredient_fixture.unit_cost,
            perishable=ingredient_fixture.perishable,
            shelf_life_days=ingredient_fixture.shelf_life_days,
            supplier_id=supplier_id,
            safety_margin_days_override=ingredient_fixture.safety_margin_days_override,
        )
        db.add(ingredient)
        ingredients_created += 1

    if suppliers_created or ingredients_created:
        db.commit()
        logger.info(
            "seed_demo_ingredients",
            extra={
                "suppliers_created": suppliers_created,
                "ingredients_created": ingredients_created,
            },
        )
    return suppliers_created, ingredients_created


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        suppliers_created, ingredients_created = seed_demo_ingredients(db)
        if suppliers_created or ingredients_created:
            logger.info(
                "Seeded %d supplier(s) and %d ingredient(s).",
                suppliers_created,
                ingredients_created,
            )
        else:
            logger.info("Demo ingredients/suppliers already exist — no-op.")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
