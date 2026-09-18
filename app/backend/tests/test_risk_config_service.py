"""Pure unit tests for `services/risk_config_service.py` (ACRI-44 US-009):
the lazily-created singleton row, its documented default, and the
live-adjustable update path."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import RiskConfig
from schemas.risk import RiskConfigUpdate
from services.risk_config_service import (
    DEFAULT_MATERIALITY_THRESHOLD_INR,
    get_materiality_threshold,
    get_risk_config,
    update_risk_config,
)


def test_default_threshold_is_500_when_unset(db_session: Session) -> None:
    assert get_materiality_threshold(db_session) == DEFAULT_MATERIALITY_THRESHOLD_INR
    assert DEFAULT_MATERIALITY_THRESHOLD_INR == 500.0


def test_reading_the_config_lazily_creates_exactly_one_row(db_session: Session) -> None:
    get_risk_config(db_session)
    get_risk_config(db_session)

    rows = db_session.execute(select(RiskConfig)).scalars().all()
    assert len(rows) == 1


def test_update_takes_effect_immediately_for_the_next_read(db_session: Session) -> None:
    update_risk_config(db_session, RiskConfigUpdate(materiality_threshold_inr=750.0))

    assert get_materiality_threshold(db_session) == 750.0
    assert get_risk_config(db_session).materiality_threshold_inr == 750.0
