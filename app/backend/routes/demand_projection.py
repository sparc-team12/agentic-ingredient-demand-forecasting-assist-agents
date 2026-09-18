"""Ingredient demand projection debug/introspection routes (ACRI-36 US-001 /
ACRI-37 US-002).

Nothing consumes `services/demand_projection_service.py` over HTTP yet — the
Stockout/Spoilage track will, next — so this single read-only endpoint
exists to make the projection maths independently testable and inspectable
end-to-end. One `APIRouter` (`demand_projection_router`), depending on
`middleware.auth.get_current_user` — reused verbatim, the identical gating
pattern used by every other data-setup route. No persona-based branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.demand_projection import IngredientDemandSeriesOut
from services import demand_projection_service

demand_projection_router = APIRouter(prefix="/demand-projection", tags=["demand-projection"])


@demand_projection_router.get("/{ingredient_id}", response_model=IngredientDemandSeriesOut)
def get_demand_projection(
    ingredient_id: int,
    days: int = Query(default=demand_projection_service.DEFAULT_FORWARD_HORIZON_DAYS, ge=1),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> demand_projection_service.IngredientDemandSeries:
    """`GET /demand-projection/{ingredient_id}?days=14` — the forward-horizon
    projection series (US-001 AC3), each day's per-dish breakdown and
    arithmetic trace included (US-001 AC5, US-002 AC3). Raises `404` for an
    unknown `ingredient_id`."""
    return demand_projection_service.project_ingredient_demand_series(ingredient_id, days, db)
