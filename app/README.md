# Agentic Ingredient Demand Forecasting Assistant — Application

Scaffold-only application code. **No business features are implemented yet** —
this is the buildable/testable foundation for subsequent, requirements-driven
development work (see `.claude/agents/dev-orchestrator-agent.md`).

Stack resolved per `workflow/decisions.md` DEC-005 (human-directed bypass of
the HLD/LLD/architecture-validation gate for this build):

- **Frontend** (`app/frontend`): React + TypeScript + Vite, npm
- **Backend** (`app/backend`): Python + FastAPI, pip + `requirements.txt`
- **Persistence**: SQLAlchemy ORM over SQLite
- **Test tooling**: Vitest (frontend), pytest (backend)

## Prerequisites

- Node.js >= 20 and npm >= 10
- Python >= 3.12 and pip

(Verified in this environment: Node v24.20.0 / npm 11.19.0 / Python 3.14.5 / pip 26.1.1.)

## Frontend (`app/frontend`)

Run all commands from `app/` unless noted otherwise.

| Task | Command |
|---|---|
| Install | `npm install` |
| Run dev server | `npm run dev --workspace frontend` |
| Lint | `npm run lint --workspace frontend` |
| Format check | `npm run format:check --workspace frontend` |
| Typecheck | `npm run typecheck --workspace frontend` |
| Build | `npm run build --workspace frontend` |
| Test | `npm run test --workspace frontend` |

Copy `app/frontend/.env.example` to `app/frontend/.env.local` and adjust `VITE_API_URL` as needed.

## Backend (`app/backend`)

Run all commands from `app/backend`.

| Task | Command |
|---|---|
| Create virtual environment | `python -m venv .venv` |
| Activate (Windows) | `.venv\Scripts\activate` |
| Activate (macOS/Linux) | `source .venv/bin/activate` |
| Install (runtime) | `pip install -r requirements.txt` |
| Install (dev/test/lint) | `pip install -r requirements-dev.txt` |
| Run dev server | `uvicorn main:app --reload --port 8000` |
| Lint | `ruff check .` |
| Format check | `black --check .` |
| Typecheck | `mypy .` |
| Test | `pytest` |

Copy `app/backend/.env.example` to `app/backend/.env` and adjust as needed.

### Seeding demo accounts (ACRI-66)

Two demo accounts (one per persona — kitchen-manager, fb-manager) are required to log in. They
are seeded automatically, idempotently, on backend startup (`main.py`'s lifespan hook), sourced
from the `SEED_KITCHEN_MANAGER_EMAIL`/`SEED_KITCHEN_MANAGER_PASSWORD`/`SEED_FB_MANAGER_EMAIL`/
`SEED_FB_MANAGER_PASSWORD` environment variables (documented, non-production-real placeholder
values in `.env.example`; override in your own untracked `.env` for different local demo
credentials).

The same seeding logic is also exposed as a standalone CLI, for explicit/manual invocation
without starting the full ASGI app:

```
python -m scripts.seed_demo_accounts
```

## Repository layout

```
app/
├── frontend/   # React + TypeScript + Vite SPA (npm workspace)
└── backend/    # Python + FastAPI service (independent pip project)
```

## CI

`.github/workflows/ci.yml` (repo root) runs the frontend lint/typecheck/test/build
commands and the backend lint/test commands above on every push/PR.

## Scope note

The initial scaffold provided infrastructure only (manifests, configuration, module
placeholders, one bootstrap/smoke test per workspace) — see
`artifacts/development/_scaffold/project-initialization.json` for that scaffold evidence and
`workflow/decisions.md` (DEC-004, DEC-005) for the sourcing/override decisions that govern this
build.

Per-user login (ACRI-66) is now implemented: a kitchen-manager or fb-manager authenticates with
their own email+password before reaching any of the 4 gated screens (risk dashboard, ingredient
detail, Chat Agent, purchase-order draft). See `artifacts/development/acri-66/implementation-plan.md`
for the full design. The 4 screens themselves remain authenticated placeholders — their real
business logic lands in later, dedicated stories.

### Ingredients & Suppliers Setup (ACRI-61)

A new gated screen at `/data-setup/ingredients-suppliers` (standalone for now — the Data Setup
hub, ACRI-59, is not yet built) lets a kitchen-manager view/add/edit the supplier list (name, lead
time, optional default safety-margin-in-days) and the ingredient master (unit, unit cost,
perishable flag, shelf life, mapped supplier, safety-margin override). An ingredient with no
mapped supplier, or with no resolvable safety-margin value (from its own override or its mapped
supplier's default), is visibly flagged rather than silently defaulted to zero. New backend routes:
`GET/POST /suppliers`, `PUT /suppliers/{id}`, `GET/POST /ingredients`, `PUT /ingredients/{id}` —
all behind the same `get_current_user` session gate as the 4 stub screens. `PUT` is full-replace:
edit forms always resubmit the complete current object. See
`artifacts/development/acri-61/implementation-plan.md` for the full design.

A fixture-only demo dataset (2 suppliers, 3 ingredients — deliberately including one un-mapped
ingredient and one ingredient/supplier pair with no safety margin, to exercise the gap-flag UI) can
be seeded via an opt-in CLI, **not** run automatically at backend startup:

```
python -m scripts.seed_demo_ingredients
```
