"""Business logic for the Purchase Order Draft (ACRI-53 US-018).

Responsibility: assemble the editable-draft fields (supplier name, item
name, suggested order quantity, required delivery date, unit) for a single
ingredient, built entirely on top of
`services/stockout_risk_service.py::evaluate_stockout_risk` — no HTTP
concerns here — those live in `routes/purchase_order_draft.py`.

- A draft is available only for a stockout-flagged ingredient (US-018 AC1):
  `evaluate_stockout_risk` returning `None` (not at risk, or no recorded
  `CurrentStock` snapshot to evaluate against) means no draft is available;
  `generate_purchase_order_draft` returns `None` in that case too, and
  `routes/purchase_order_draft.py` turns that into a `404`. An unknown
  `ingredient_id` still raises `404` (propagated from
  `evaluate_stockout_risk`).
- `required_delivery_date` is deliberately `order_by_date` from the
  stockout evaluation, not `stockout_date` — the date arithmetic already
  bakes in the supplier's lead time and the safety margin (`order_by_date =
  stockout_date - lead_time_days - safety_margin_days`), so `order_by_date`
  is the date by which the order must be placed/land to avoid the
  stockout, which is the practical "required delivery date" a kitchen
  manager drafts a PO against. This is a documented assumption, not a
  separate figure computed here.
- `suggested_quantity` is `suggested_order_quantity` from the stockout
  evaluation verbatim (the consumption expected while a freshly placed
  order is in transit).
- `supplier_name` is `None`, with `supplier_gap=True`, when the ingredient
  has no supplier mapped — never fabricated as an empty string or a
  placeholder name, same "visibly flagged, never silently defaulted"
  convention as `StockoutRiskResult.lead_time_gap`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from db.models import Ingredient
from services import stockout_risk_service


@dataclass(frozen=True)
class PurchaseOrderDraftResult:
    """The editable-draft fields for one stockout-flagged ingredient."""

    ingredient_id: int
    item_name: str
    unit: str
    supplier_name: str | None
    supplier_gap: bool
    suggested_quantity: float
    required_delivery_date: date


def generate_purchase_order_draft(
    ingredient_id: int, db: Session, *, anchor: date | None = None
) -> PurchaseOrderDraftResult | None:
    """US-018 AC1. Returns `None` when the ingredient is not stockout-
    flagged (or has no recorded `CurrentStock` snapshot — see
    `evaluate_stockout_risk`). Raises `404` for an unknown `ingredient_id`.
    `anchor` defaults to `date.today()`, mirroring `evaluate_stockout_risk`.
    """
    stockout = stockout_risk_service.evaluate_stockout_risk(ingredient_id, db, anchor=anchor)
    if stockout is None:
        return None

    # `evaluate_stockout_risk` already raised 404 for an unknown ingredient
    # above, so this `Ingredient` row is guaranteed to exist here.
    ingredient = db.get(Ingredient, ingredient_id)
    assert ingredient is not None

    supplier = ingredient.supplier
    supplier_name = supplier.name if supplier is not None else None

    return PurchaseOrderDraftResult(
        ingredient_id=ingredient.id,
        item_name=ingredient.name,
        unit=ingredient.unit,
        supplier_name=supplier_name,
        supplier_gap=supplier is None,
        suggested_quantity=stockout.suggested_order_quantity,
        required_delivery_date=stockout.order_by_date,
    )
