"""Fixture-only seed script idempotency and shape (ACRI-61 demo data for
AC3/AC5). Uses the isolated per-test SQLite database from
`tests/conftest.py`'s `db_session`/`test_engine` fixtures (tech-lead review
SUGGESTION) — never the developer's real `app.db`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Ingredient, Supplier
from scripts.seed_demo_ingredients import seed_demo_ingredients


def test_seed_creates_exactly_two_suppliers_and_three_ingredients(db_session: Session) -> None:
    suppliers_created, ingredients_created = seed_demo_ingredients(db_session)

    assert suppliers_created == 2
    assert ingredients_created == 3
    assert len(db_session.execute(select(Supplier)).scalars().all()) == 2
    assert len(db_session.execute(select(Ingredient)).scalars().all()) == 3


def test_seed_includes_one_deliberately_unmapped_ingredient_ac3(db_session: Session) -> None:
    seed_demo_ingredients(db_session)

    ingredients = db_session.execute(select(Ingredient)).scalars().all()
    unmapped = [ingredient for ingredient in ingredients if ingredient.supplier_id is None]

    assert len(unmapped) == 1


def test_seed_includes_one_ingredient_supplier_pair_with_no_safety_margin_anywhere_ac5(
    db_session: Session,
) -> None:
    seed_demo_ingredients(db_session)

    ingredients = db_session.execute(select(Ingredient)).scalars().all()
    mapped_with_no_override = [
        ingredient
        for ingredient in ingredients
        if ingredient.supplier_id is not None and ingredient.safety_margin_days_override is None
    ]
    gap_pairs = [
        ingredient
        for ingredient in mapped_with_no_override
        if ingredient.supplier is not None and ingredient.supplier.safety_margin_days is None
    ]

    assert len(gap_pairs) == 1


def test_running_seed_twice_is_idempotent_and_creates_no_duplicates(db_session: Session) -> None:
    first_suppliers, first_ingredients = seed_demo_ingredients(db_session)
    second_suppliers, second_ingredients = seed_demo_ingredients(db_session)

    assert first_suppliers == 2
    assert first_ingredients == 3
    assert second_suppliers == 0
    assert second_ingredients == 0
    assert len(db_session.execute(select(Supplier)).scalars().all()) == 2
    assert len(db_session.execute(select(Ingredient)).scalars().all()) == 3
