"""Stockout/Spoilage Risk HTTP routes (ACRI-38..44, ACRI-64).

Two `APIRouter`s (`ingredient_risk_router`, `risk_config_router`), both
depending on `middleware.auth.get_current_user` — reused verbatim, the
identical gating pattern used by every other data-setup/risk route. No
persona-based branching.

Kept in a dedicated module rather than added to `routes/ingredients.py` /
`routes/current_stock.py` so the ACRI-61/ACRI-62 route files stay untouched
(no unplanned edits to those approved files).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.risk import IngredientRiskOut, RiskConfigOut, RiskConfigUpdate
from services import risk_config_service, spoilage_risk_service, stockout_risk_service

ingredient_risk_router = APIRouter(prefix="/ingredients", tags=["risk"])
risk_config_router = APIRouter(prefix="/risk-config", tags=["risk"])


@ingredient_risk_router.get("/{ingredient_id}/risk", response_model=IngredientRiskOut)
def get_ingredient_risk(
    ingredient_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """`GET /ingredients/{id}/risk` — both the stockout (ACRI-38..41) and
    spoilage (ACRI-42..44, ACRI-64) evaluations for one ingredient, either
    of which may be `null` when that risk isn't present. Raises `404` for
    an unknown `ingredient_id`."""
    return {
        "stockout": stockout_risk_service.evaluate_stockout_risk(ingredient_id, db),
        "spoilage": spoilage_risk_service.evaluate_spoilage_risk(ingredient_id, db),
    }


@risk_config_router.get("", response_model=RiskConfigOut)
def get_risk_config(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RiskConfigOut:
    """`GET /risk-config` (ACRI-44 US-009)."""
    return risk_config_service.get_risk_config(db)


@risk_config_router.put("", response_model=RiskConfigOut)
def put_risk_config(
    payload: RiskConfigUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RiskConfigOut:
    """`PUT /risk-config` (ACRI-44 US-009) — applies immediately, no
    redeploy required."""
    return risk_config_service.update_risk_config(db, payload)
