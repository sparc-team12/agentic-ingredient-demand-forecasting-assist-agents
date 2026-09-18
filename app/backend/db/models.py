"""SQLAlchemy ORM models for authentication (ACRI-66), the Ingredients &
Suppliers Setup screen (ACRI-61), and the remaining Data Setup screens
(ACRI-60 Menu & Recipe, ACRI-62 Current Stock, ACRI-63 Sales History; the
ACRI-59 hub reads these tables but adds no table of its own).

Defines the greenfield tables introduced by these stories:

- ``users`` — one row per persona (kitchen-manager, fb-manager), per-user
  credentials (DEC-004 supersedes the single-shared-login model in ARCH-016).
- ``user_sessions`` — opaque server-side session tokens (DEC-005).
- ``login_attempts`` — audit trail of every login attempt, success and
  failure, doubling as the data source for the failed-login rolling-window
  alert (ARCH-020).
- ``suppliers`` / ``ingredients`` (ACRI-61) — supplier list and ingredient
  master data, independent of the auth tables above; see ``Supplier`` and
  ``Ingredient`` below for the safety-margin precedence data model.
- ``dishes`` / ``recipe_lines`` (ACRI-60) — dish + per-serving recipe lines.
  ``RecipeLine.ingredient_id`` is a *nullable* FK, resolved by a
  case-insensitive name lookup against ``ingredients`` at write time: a
  recipe line whose typed ``ingredient_name`` does not match any existing
  ``Ingredient`` is stored anyway (``ingredient_id`` stays ``NULL``) so it
  can be flagged, never rejected — see ``services/menu_recipe_service.py``.
- ``current_stock`` (ACRI-62) — one snapshot row per ``Ingredient``
  (``ingredient_id`` unique), upserted on edit; not a log of history.
- ``sales_history_records`` (ACRI-63) — one row per ``Dish`` per calendar
  day of manually-entered units-sold; ``(dish_id, sale_date)`` is unique so
  "distinct days of history" is just a row count per dish.
- ``risk_config`` (ACRI-44) — a single-row, live-adjustable materiality
  threshold used by spoilage risk; see ``RiskConfig`` below.

No migration tool exists yet; schema is created via ``Base.metadata.create_all``
at backend startup (see ``main.py`` and Assumption A9 in the ACRI-66
implementation plan / A9 in the ACRI-61 implementation plan carried forward).
"""

from __future__ import annotations

import enum
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class Persona(str, enum.Enum):
    """The exactly-two personas in scope for this story (no extra roles)."""

    KITCHEN_MANAGER = "kitchen_manager"
    FB_MANAGER = "fb_manager"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    """A single per-persona login account."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "persona IN ('kitchen_manager', 'fb_manager')",
            name="ck_users_persona_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    sessions: Mapped[list[UserSession]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    """An opaque, server-side session token issued at login (DEC-005)."""

    __tablename__ = "user_sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User] = relationship("User", back_populates="sessions")


class LoginAttempt(Base):
    """Audit record of a single login attempt (success or failure)."""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Supplier(Base):
    """A supplier providing one or more ingredients (ACRI-61 AC2/AC4).

    ``safety_margin_days`` is nullable-until-set and acts as the *default*
    safety margin for every ingredient mapped to this supplier, unless the
    ingredient's own ``safety_margin_days_override`` is set (see
    ``services/ingredient_service.py::resolve_safety_margin``). Never
    defaulted to ``0`` — AC5 requires a missing value to be visibly flagged,
    not silently coerced.
    """

    __tablename__ = "suppliers"
    __table_args__ = (
        CheckConstraint("lead_time_days >= 0", name="ck_suppliers_lead_time_non_negative"),
        CheckConstraint(
            "safety_margin_days IS NULL OR safety_margin_days >= 0",
            name="ck_suppliers_safety_margin_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    safety_margin_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    ingredients: Mapped[list[Ingredient]] = relationship("Ingredient", back_populates="supplier")


class Ingredient(Base):
    """A single ingredient master record (ACRI-61 AC1/AC2/AC3/AC4/AC5).

    ``supplier_id`` is a single nullable FK (1:1 mapping) — multiple
    suppliers per ingredient is explicitly out of scope for this story.
    ``safety_margin_days_override``, when set, takes precedence over the
    mapped supplier's ``safety_margin_days`` (see
    ``services/ingredient_service.py::resolve_safety_margin``).
    """

    __tablename__ = "ingredients"
    __table_args__ = (
        CheckConstraint("unit_cost >= 0", name="ck_ingredients_unit_cost_non_negative"),
        CheckConstraint(
            "shelf_life_days IS NULL OR shelf_life_days > 0",
            name="ck_ingredients_shelf_life_positive",
        ),
        CheckConstraint(
            "safety_margin_days_override IS NULL OR safety_margin_days_override >= 0",
            name="ck_ingredients_safety_margin_override_non_negative",
        ),
        CheckConstraint(
            "perishable = 0 OR shelf_life_days IS NOT NULL",
            name="ck_ingredients_shelf_life_when_perishable",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    perishable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    safety_margin_days_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    supplier: Mapped[Supplier | None] = relationship("Supplier", back_populates="ingredients")


class Dish(Base):
    """A single dish on the menu (ACRI-60 AC1). Manual add/edit only — no
    delete, matching the ACRI-61 precedent for master-data screens."""

    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    recipe_lines: Mapped[list[RecipeLine]] = relationship(
        "RecipeLine", back_populates="dish", cascade="all, delete-orphan"
    )
    sales_history_records: Mapped[list[SalesHistoryRecord]] = relationship(
        "SalesHistoryRecord", back_populates="dish", cascade="all, delete-orphan"
    )


class RecipeLine(Base):
    """One ingredient-quantity line of a dish's recipe (ACRI-60 AC1/AC2).

    ``ingredient_id`` is resolved (case-insensitive exact match against
    ``Ingredient.name``) at create/update time in
    ``services/menu_recipe_service.py::resolve_ingredient_id``; when no
    match exists the line is still stored, with ``ingredient_id`` left
    ``NULL`` so the API can flag it (AC2) rather than reject it.
    """

    __tablename__ = "recipe_lines"
    __table_args__ = (
        CheckConstraint(
            "quantity_per_serving > 0", name="ck_recipe_lines_quantity_per_serving_positive"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), nullable=False, index=True)
    ingredient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ingredient_id: Mapped[int | None] = mapped_column(ForeignKey("ingredients.id"), nullable=True)
    quantity_per_serving: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    dish: Mapped[Dish] = relationship("Dish", back_populates="recipe_lines")
    ingredient: Mapped[Ingredient | None] = relationship("Ingredient")


class CurrentStock(Base):
    """Current quantity-on-hand + use-by-date snapshot for one ingredient
    (ACRI-62 AC1/AC2). One row per ``Ingredient`` (``ingredient_id`` unique);
    edits upsert this single row rather than appending a log entry."""

    __tablename__ = "current_stock"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="ck_current_stock_quantity_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"), unique=True, nullable=False, index=True
    )
    quantity_on_hand: Mapped[float] = mapped_column(Float, nullable=False)
    use_by_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    ingredient: Mapped[Ingredient] = relationship("Ingredient")


class RiskConfig(Base):
    """Singleton row holding the spoilage materiality threshold (ACRI-44
    US-009). Live-adjustable via `GET/PUT /risk-config` — a change takes
    effect on the very next spoilage-risk evaluation, no redeploy required.
    ``services/risk_config_service.py`` lazily creates the single row (with
    the documented default) the first time it is read; nothing seeds it at
    startup.
    """

    __tablename__ = "risk_config"
    __table_args__ = (
        CheckConstraint(
            "materiality_threshold_inr >= 0",
            name="ck_risk_config_threshold_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    materiality_threshold_inr: Mapped[float] = mapped_column(Float, nullable=False, default=500.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class SalesHistoryRecord(Base):
    """One day of manually-entered units-sold for one dish (ACRI-63
    AC1/AC2). ``(dish_id, sale_date)`` is unique — a second entry for the
    same dish/day is rejected as a `409` (mirrors the duplicate-name
    backstop used elsewhere), so "distinct days of history" is simply a row
    count per dish."""

    __tablename__ = "sales_history_records"
    __table_args__ = (
        UniqueConstraint("dish_id", "sale_date", name="uq_sales_history_dish_id_sale_date"),
        CheckConstraint("units_sold >= 0", name="ck_sales_history_units_sold_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), nullable=False, index=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    units_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    dish: Mapped[Dish] = relationship("Dish", back_populates="sales_history_records")
