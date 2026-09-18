"""Pure unit tests for `resolve_safety_margin` (ACRI-61 AC4/AC5) — all four
combinations of override set/unset x supplier value set/unset, plus the
explicit-zero edge case. No DB session needed: `Ingredient`/`Supplier` are
constructed in memory only, never persisted."""

from __future__ import annotations

from db.models import Ingredient, Supplier
from services.ingredient_service import resolve_safety_margin


def test_ingredient_override_wins_when_supplier_also_has_a_value() -> None:
    ingredient = Ingredient(safety_margin_days_override=4)
    supplier = Supplier(safety_margin_days=9)

    value, source = resolve_safety_margin(ingredient, supplier)

    assert value == 4
    assert source == "ingredient"


def test_supplier_value_used_when_ingredient_has_no_override() -> None:
    ingredient = Ingredient(safety_margin_days_override=None)
    supplier = Supplier(safety_margin_days=6)

    value, source = resolve_safety_margin(ingredient, supplier)

    assert value == 6
    assert source == "supplier"


def test_no_override_and_no_mapped_supplier_is_a_gap_not_zero() -> None:
    ingredient = Ingredient(safety_margin_days_override=None)

    value, source = resolve_safety_margin(ingredient, None)

    assert value is None
    assert source is None


def test_no_override_and_mapped_supplier_with_no_value_is_a_gap_not_zero() -> None:
    ingredient = Ingredient(safety_margin_days_override=None)
    supplier = Supplier(safety_margin_days=None)

    value, source = resolve_safety_margin(ingredient, supplier)

    assert value is None
    assert source is None


def test_an_explicit_zero_override_is_respected_and_not_confused_with_missing() -> None:
    """`0` is a legitimate override value — AC5 forbids *defaulting* to zero
    when a value is missing, but an explicitly-entered `0` must still be
    honored (not treated as falsy/missing)."""
    ingredient = Ingredient(safety_margin_days_override=0)
    supplier = Supplier(safety_margin_days=9)

    value, source = resolve_safety_margin(ingredient, supplier)

    assert value == 0
    assert source == "ingredient"


def test_an_explicit_zero_supplier_default_is_respected_and_not_confused_with_missing() -> None:
    ingredient = Ingredient(safety_margin_days_override=None)
    supplier = Supplier(safety_margin_days=0)

    value, source = resolve_safety_margin(ingredient, supplier)

    assert value == 0
    assert source == "supplier"
