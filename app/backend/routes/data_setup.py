"""Data Setup Hub HTTP routes (ACRI-59).

One `APIRouter` (`data_setup_router`), depending on
`middleware.auth.get_current_user` — reused verbatim. No persona-based
branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.data_setup import DataSetupStatusOut
from services import data_setup_service

data_setup_router = APIRouter(prefix="/data-setup", tags=["data-setup"])


@data_setup_router.get("/status", response_model=DataSetupStatusOut)
def get_data_setup_status(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DataSetupStatusOut:
    return data_setup_service.get_data_setup_status(db)
