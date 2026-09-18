"""ASGI entry point for the Agentic Ingredient Demand Forecasting Assistant
backend.

Exposes the health-check route, the ACRI-66 authentication routes
(`/auth/*`), the 4 protected stub screen routes (`/screens/*`), the ACRI-61
`/suppliers`/`/ingredients` routes, the ACRI-60 `/dishes` routes, the
ACRI-62 `/current-stock` routes, the ACRI-63 `/sales-history` routes, the
ACRI-36/ACRI-37 `/demand-projection` debug/introspection route, the
ACRI-38..44/ACRI-64 `/ingredients/{id}/risk` and `/risk-config` routes, the
ACRI-54..58 `/dashboard/risk-summary` route, the ACRI-59
`/data-setup/status` route, and the ACRI-45/ACRI-49..52 `/chat-agent/ask`
route. On startup, creates the schema (no
migration tool exists yet — Assumption A9) and seeds the 2 documented demo
accounts (idempotent). Ingredient/supplier fixture seeding is opt-in CLI
only (`scripts/seed_demo_ingredients.py`) — deliberately not run here, so a
fresh dev/test database never silently gains fake ingredient rows just by
starting the server (ACRI-61 Assumption A6).
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Must run before any other local import — db/session.py, middleware/auth.py,
# services/auth_service.py, and services/llm_client.py all read os.environ.get(...)
# at module import time. python-dotenv has been a declared dependency since
# ACRI-66, but nothing ever actually called load_dotenv() until this fix — every
# os.environ.get(..., default) call was silently falling back to its hardcoded
# default, never the real .env value (discovered via GEMINI_API_KEY appearing
# "missing" despite being set in .env).
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from db.seed import seed_demo_accounts  # noqa: E402
from db.session import Base, SessionLocal, engine  # noqa: E402
from routes.auth import router as auth_router  # noqa: E402
from routes.chat_agent import chat_agent_router  # noqa: E402
from routes.current_stock import current_stock_router  # noqa: E402
from routes.dashboard import dashboard_router  # noqa: E402
from routes.data_setup import data_setup_router  # noqa: E402
from routes.demand_projection import demand_projection_router  # noqa: E402
from routes.ingredients import ingredients_router, suppliers_router  # noqa: E402
from routes.menu_recipe import dishes_router  # noqa: E402
from routes.purchase_order_draft import purchase_order_draft_router  # noqa: E402
from routes.risk import ingredient_risk_router, risk_config_router  # noqa: E402
from routes.sales_history import sales_history_router  # noqa: E402
from routes.screens import router as screens_router  # noqa: E402

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create the schema (if needed) and seed the 2 demo accounts on startup."""
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        seed_demo_accounts(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Ingredient Demand Forecasting Assistant API",
    description="FastAPI backend for the Agentic Ingredient Demand Forecasting Assistant.",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(screens_router)
app.include_router(suppliers_router)
app.include_router(ingredients_router)
app.include_router(dishes_router)
app.include_router(current_stock_router)
app.include_router(sales_history_router)
app.include_router(demand_projection_router)
app.include_router(ingredient_risk_router)
app.include_router(risk_config_router)
app.include_router(purchase_order_draft_router)
app.include_router(dashboard_router)
app.include_router(data_setup_router)
app.include_router(chat_agent_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Minimal liveness probe used by the bootstrap/smoke test and CI."""
    return {"status": "ok"}
