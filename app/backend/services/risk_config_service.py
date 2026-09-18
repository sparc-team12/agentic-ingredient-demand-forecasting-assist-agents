"""Business logic for the spoilage materiality threshold (ACRI-44 US-009).

A single `RiskConfig` row acts as a live-adjustable singleton: reading it
lazily creates the one row (seeded with `DEFAULT_MATERIALITY_THRESHOLD_INR`)
the first time it's needed, so a fresh database doesn't require a
migration/seed step to have a threshold. `get_materiality_threshold` is read
fresh from the database on every call (never cached at import time or on
the request object), so a `PUT /risk-config` change is visible to the very
next spoilage-risk evaluation, no redeploy required (AC).

No HTTP concerns here — those live in `routes/risk.py`, mirroring the
`services/*_service.py` / `routes/*.py` split already established
throughout this codebase.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import RiskConfig
from schemas.risk import RiskConfigOut, RiskConfigUpdate

logger = logging.getLogger(__name__)

DEFAULT_MATERIALITY_THRESHOLD_INR = 500.0


def _get_or_create_risk_config(db: Session) -> RiskConfig:
    """The single `RiskConfig` row, creating it with the default threshold
    the first time it's read. Uses `LIMIT 1` rather than a fixed primary
    key, since nothing else ever inserts a second row."""
    config = db.execute(select(RiskConfig).limit(1)).scalar_one_or_none()
    if config is None:
        config = RiskConfig(materiality_threshold_inr=DEFAULT_MATERIALITY_THRESHOLD_INR)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def get_materiality_threshold(db: Session) -> float:
    """The raw `float` threshold, for `services/spoilage_risk_service.py` to
    compare `waste_cost_inr` against — always read live (see module
    docstring)."""
    return _get_or_create_risk_config(db).materiality_threshold_inr


def get_risk_config(db: Session) -> RiskConfigOut:
    """`GET /risk-config` (ACRI-44 US-009)."""
    return RiskConfigOut.model_validate(_get_or_create_risk_config(db))


def update_risk_config(db: Session, payload: RiskConfigUpdate) -> RiskConfigOut:
    """`PUT /risk-config` (ACRI-44 US-009) — applies immediately to every
    subsequent spoilage-risk evaluation."""
    config = _get_or_create_risk_config(db)
    config.materiality_threshold_inr = payload.materiality_threshold_inr
    db.commit()
    db.refresh(config)
    logger.info(
        "risk_config_updated",
        extra={"materiality_threshold_inr": config.materiality_threshold_inr},
    )
    return RiskConfigOut.model_validate(config)
