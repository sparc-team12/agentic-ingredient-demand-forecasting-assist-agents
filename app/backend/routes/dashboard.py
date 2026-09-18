"""Risk Dashboard aggregation HTTP route (ACRI-54..58).

One `APIRouter` (`dashboard_router`), depending on
`middleware.auth.get_current_user` — reused verbatim, the identical gating
pattern used by every other route in this codebase. No persona-based
branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.dashboard import DashboardRiskSummaryOut
from services import dashboard_service

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/risk-summary", response_model=DashboardRiskSummaryOut)
def get_risk_summary(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DashboardRiskSummaryOut:
    """`GET /dashboard/risk-summary` (ACRI-54 US-019, ACRI-55 US-020,
    ACRI-56 US-021, ACRI-57 US-022, ACRI-58 US-023)."""
    return dashboard_service.get_risk_summary(db)
