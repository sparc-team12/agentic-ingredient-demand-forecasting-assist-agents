"""Purchase Order Draft HTTP route (ACRI-53 US-018).

One `APIRouter` (`purchase_order_draft_router`), depending on
`middleware.auth.get_current_user` — reused verbatim, the identical gating
pattern used by every other risk/data-setup route. No persona-based
branching. Kept in a dedicated module (mirroring `routes/demand_projection.py`
and `routes/risk.py`) rather than added to `routes/ingredients.py`, so that
approved file stays untouched.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.purchase_order_draft import PurchaseOrderDraftOut
from services import purchase_order_draft_service

purchase_order_draft_router = APIRouter(prefix="/ingredients", tags=["purchase-order-draft"])


@purchase_order_draft_router.get(
    "/{ingredient_id}/purchase-order-draft", response_model=PurchaseOrderDraftOut
)
def get_purchase_order_draft(
    ingredient_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> purchase_order_draft_service.PurchaseOrderDraftResult:
    """`GET /ingredients/{id}/purchase-order-draft` (US-018 AC1) — the
    editable-draft fields for a stockout-flagged ingredient. Raises `404`
    both for an unknown `ingredient_id` (propagated from
    `evaluate_stockout_risk`) and for an ingredient that is not currently
    stockout-flagged (no draft available)."""
    draft = purchase_order_draft_service.generate_purchase_order_draft(ingredient_id, db)
    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This ingredient is not currently flagged for stockout risk "
            "(or has no recorded stock snapshot) — no purchase order draft is available.",
        )
    return draft
