# Implementation Plan — ACRI-61 (Ingredients & Suppliers Setup)

## 1. Metadata

| Field | Value |
|---|---|
| Work item | `ACRI-61` (Story-Id `US-026`, epic `ACRI-35` "[Data Setup] Data Setup") |
| Title | Kitchen-manager loads/views ingredient master data, supplier list, and safety-margin values on an Ingredients & Suppliers Setup screen |
| Status | **PENDING_TECH_LEAD** |
| Repository | `agentic-ingredient-demand-forecasting-assist-agents` |
| Artifact dir | `artifacts/development/acri-61/` |
| Sources | Jira `ACRI-61` (AC1–AC5, Out-of-Scope list, given verbatim in the planning task); `workflow/decisions.md` `DEC-004` (PRD superseded by Jira stories) and `DEC-005` (explicit bypass of the HLD/LLD/architecture-validation development gate; resolved tech stack — FastAPI/SQLAlchemy/SQLite backend, React/Vite/TS frontend, pytest/Vitest); `artifacts/development/acri-61/requirements-validation.json` (status `PASS`, confidence 0.85); Confluence "Technology Stack" (id `5885657157`, Approved) and "Design Document" (id `5885722653`, Approved, UI-007 "Ingredients & Suppliers Setup") per DEC-005; `artifacts/architecture/solution-architecture.md` (`ARCH-012` SQLite storage, `ARCH-013` configuration surface incl. safety margin, `ARCH-002` React) — the only architecture document that is actually `Status: Approved`; the planning task's own authorized resolutions for the four open questions raised by `requirements-validation.json` (safety-margin data model, bulk-upload scope, auth gate, dataset source), treated as authorized decisions per the task prompt; `artifacts/development/acri-66/` (requirements-validation.json, implementation-plan.md, implementation.md, qa-handoff.md) — ACRI-66 is `READY_FOR_QA`; its auth infrastructure (`get_current_user`, `RequireAuth`, `AuthProvider`, `apiClient`) is reused here exactly as-is, not modified; direct repository inspection (this session) of `app/backend/{main.py,db/models.py,db/session.py,routes/*,middleware/auth.py,schemas/auth.py,services/auth_service.py,db/seed.py,pyproject.toml,requirements.txt}` and `app/frontend/src/{App.tsx,main.tsx,lib/*,hooks/*,components/*,routes/*}` — confirms current repo state described in §3 below. |
| HLD/LLD/architecture-validation gate | **Explicitly bypassed per `DEC-005`**, repository-wide, for every `ACRI` story. `artifacts/architecture/high-level-design.md` and `artifacts/architecture/low-level-design.md` exist in this repo but both carry `Status: DRAFT — pending human approval` (confirmed by direct inspection of their headers) and are **not used** as inputs to this plan, consistent with `requirements-validation.json`'s own sources list (which cites the Confluence Tech Stack/Design Document pages and `DEC-005`, not the draft HLD/LLD). No `architecture-validation.json` exists or is used. Every design decision below that would normally cite an `LLD-` ID is instead labeled `[ASSUMPTION]` and traced to an `ARCH-`/`DEC-`/AC id or to the task prompt's explicit resolutions. `config/project.yaml`'s `development.require_approved_hld/require_approved_lld/require_architecture_validation` still read `true` — the same known, previously-flagged discrepancy already carried in `ACRI-66`'s evidence chain; not newly discovered here, not silently ignored. |
| Stack (this story) | Frontend: React 18 + TypeScript + Vite 5, npm, React Router v7 (already added by ACRI-66), Vitest + Testing Library (all already in place, no new frontend dependency needed). Backend: Python (venv on 3.14.5) + FastAPI 0.141.1 + SQLAlchemy 2.0.54 ORM over SQLite, pytest (all already in place, no new backend dependency needed). |
| Base ref | Current `main` working tree at time of planning. Git status shows modified docs/config files unrelated to this scope (`.claude/*`, `README.md`, `artifacts/README.md`, `config/project.yaml`, `docs/01-prd/...`) and untracked `app/` + `artifacts/development/` (the whole application and its development-evidence tree are not yet committed). No in-flight edit overlaps any file this plan touches. |

---

## 2. Requirement / acceptance-criterion traceability

| AC / behavior | Source | How this plan satisfies it |
|---|---|---|
| `ACRI-61-AC1` — 30–40 ingredients viewable with unit, unit cost, perishable flag, shelf life (where perishable) | Jira AC1 | Backend: `Ingredient` model + `GET /ingredients` (§4, §6). Frontend: `ingredient-master-section.tsx` renders a table with `unit`, `unit_cost`, a real checkbox for `perishable`, and `shelf_life_days` (blank/"—" when not perishable, since it's only meaningful for perishable items) (§5, §6). |
| `ACRI-61-AC2` — 3–5 suppliers viewable with lead time; each ingredient shows its mapped supplier | Jira AC2 | Backend: `Supplier` model + `GET /suppliers`; `Ingredient.supplier_id` FK, `GET /ingredients` response nests a `supplier` summary object (§4, §6). Frontend: `supplier-list-section.tsx` shows name + lead time; `ingredient-master-section.tsx` shows the mapped supplier's name per row via the nested object (§5). |
| `ACRI-61-AC3` — ingredient with no mapped supplier is visibly flagged | Jira AC3 | `supplier_id` is nullable; `IngredientOut.has_supplier` is `false` when null; `gap-flag.tsx` renders a visible, non-color-only flag ("No supplier mapped") in that row (§5, §6, TS-FE-03/TS-BE-04). |
| `ACRI-61-AC4` — safety-margin value (days) per ingredient-or-supplier is captured and viewable | Jira AC4 | Data model per the task's authorized resolution: `Supplier.safety_margin_days` (nullable, acts as default for every ingredient mapped to it) + `Ingredient.safety_margin_days_override` (nullable, takes precedence when set) — see §7 data model. Both forms capture the value; `IngredientOut.effective_safety_margin_days`/`safety_margin_source` make the resolved value and its origin viewable per ingredient (§5, §6, TS-BE-05/TS-BE-06). |
| `ACRI-61-AC5` — missing safety-margin visibly flagged, never defaulted to zero | Jira AC5 | `effective_safety_margin_days` is computed as `override ?? (supplier?.safety_margin_days) ?? None` — **never** coerced to `0`. When it resolves to `None`, `IngredientOut.safety_margin_gap = true` and `gap-flag.tsx` renders a visible flag ("Safety margin not set") in that row (§5, §6, §7, TS-FE-04/TS-BE-06/TS-BE-07). |
| Out of scope: multiple suppliers per ingredient | Jira "Out of scope" | `Ingredient.supplier_id` is a single nullable FK (1:1 mapping), not a many-to-many join table — no multi-supplier UI/model is built (§7). |
| Out of scope: ongoing price/lead-time updates after initial load | Jira "Out of scope" | The screen supports add/edit (§below), which is sufficient for "initial load"; no scheduled/automatic price-refresh, external feed, or update-history feature is built. |
| Safety-margin data model resolution | Task prompt (authorized resolution) | Implemented exactly as specified: `Supplier.safety_margin_days` nullable-until-set, default for every mapped ingredient; `Ingredient.safety_margin_days_override` nullable, takes precedence when set; both null → AC5 gap flag (§7). |
| Bulk upload out of scope | Task prompt (authorized resolution) | No CSV/spreadsheet parser is built. `supplier-form.tsx`/`ingredient-form.tsx` are the only data-entry path; a small, clearly-labeled fixture-only seed script covers the manual smoke test (§4, §9, §12 A6). |
| Auth gate | Task prompt (authorized resolution) | New route `/data-setup/ingredients-suppliers` wrapped in the existing `RequireAuth`; new backend routes depend on the existing `get_current_user` — reused verbatim, not modified (§5, §6). |
| Dataset source | Task prompt (authorized resolution) | No 30–40/3–5 real dataset is fabricated. A minimal, explicitly fixture-only 2-supplier/3-ingredient seed (deliberately including one un-mapped ingredient and one ingredient/supplier pair with no safety margin, to exercise AC3/AC5) is added as an opt-in CLI script, not auto-run at backend startup (§4, §7, §12 A6). |

---

## 3. Repository findings and commands discovered

Findings (from direct inspection, not assumed):

- `app/backend/db/models.py` currently defines exactly three tables from `ACRI-66`: `users`, `user_sessions`, `login_attempts`. No `ingredients`/`suppliers` tables exist. The new `Supplier`/`Ingredient` classes added by this plan introduce two new tables with no name collision and no FK into the existing auth tables (they are independent of `User`).
- `app/backend/main.py` currently registers only `auth_router` and `screens_router`, and performs `Base.metadata.create_all(engine)` + `seed_demo_accounts(db)` in its `lifespan` startup hook. This plan adds two more `include_router(...)` calls; it does **not** add ingredient/supplier seeding to the startup hook (see §12 A6 — deliberate, to avoid always polluting a fresh dev DB with fixture rows).
- `app/backend/routes/screens.py` defines 4 protected **stub** routes (`risk-dashboard`, `ingredient-detail`, `chat-agent`, `purchase-order-draft`), all gated by `get_current_user`, all returning an identical placeholder shape. **None of these is the "Ingredients & Suppliers Setup" screen** — there is no existing stub route for this screen to "replace or extend." This plan therefore adds a **brand-new** standalone route and a brand-new pair of backend routers, consistent with the Confluence Design Document's own note that this screen is reached from a not-yet-built Data Setup hub (`ACRI-59`) and is a standalone route for now.
- `app/backend/middleware/auth.py::get_current_user` and `app/backend/db/session.py` (`Base`, `engine`, `SessionLocal`, `get_db`) are reused verbatim — no changes needed or made.
- `app/backend/pyproject.toml`'s `[tool.mypy] files` list already enumerates `["main.py", "db", "routes", "services", "middleware", "schemas", "scripts", "tests"]` (extended by `ACRI-66`) — this already covers every new module this plan adds; **no change needed**.
- `app/backend/requirements.txt`/`requirements-dev.txt` already provide everything this story needs (`fastapi`, `sqlalchemy`, `pydantic`) — **no new backend dependency**.
- No migration tool (Alembic) exists; `ACRI-66`'s plan already flagged this and used `Base.metadata.create_all()` at startup. This story's two new tables are greenfield (no pre-existing data), so the same interim mechanism is sufficient and is reused, not re-litigated.
- `app/frontend/src/App.tsx` currently defines 5 routes (`/`, `/login`, and the 4 `RequireAuth`-wrapped stub screens) using React Router v7 (`react-router-dom`, added by `ACRI-66`). `app/frontend/src/lib/screens.ts` is a static array specifically for the 4 generic stub screens consumed by `components/common/stub-screen.tsx`; the new screen has real business logic (not a generic placeholder fetch), so it is **not** added to `SCREENS`/`stub-screen.tsx` — it gets its own route component and its own feature components, consistent with how `login.tsx` (also not a generic stub) is already handled outside that mechanism.
- `app/frontend/src/lib/api-client.ts` (`apiClient.get`/`apiClient.post`, `credentials: 'include'`, typed `ApiError`) supports GET/POST only; this story's edit flows need `PUT`. This plan **adds a `put` method to `apiClient`** (additive, non-breaking — existing `get`/`post` call sites are unaffected) rather than duplicating the fetch wrapper.
- `app/frontend/src/components/auth/require-auth.tsx`, `app/frontend/src/hooks/use-auth.ts`, and `app/frontend/src/lib/auth-context.tsx` are reused verbatim (session-gating for the new route).
- `app/frontend/src/components/` currently has exactly two feature-grouping subfolders: `auth/` and `common/` (flat, not nested under an intermediate `features/` layer). This plan follows that exact existing pattern and adds a third sibling folder, `components/ingredients-suppliers/`, rather than inventing a new `components/features/<name>/` nesting convention.
- The unrelated `c:\Users\aakash.ck\Downloads\CLAUDE.md` (Zustand/TanStack Query/shadcn/ui/React Hook Form conventions for a "solar panel inspection" Vite app) does **not** govern this repository — confirmed by direct inspection of the actual `app/frontend/src` code, which uses plain React Context (`AuthProvider`), `useState`, and a hand-rolled fetch wrapper, not any of those libraries. `ACRI-66`'s plan already flagged and disregarded this file for the same reason; this plan does the same and does not introduce TanStack Query, Zustand, or shadcn/ui for this story.
- CI (`.github/workflows/ci.yml`) runs, per workspace: frontend `npm install`, `lint`, `typecheck`, `test`, `build` (from `app/`); backend `pip install -r requirements-dev.txt`, `ruff check .`, `black --check .`, `pytest` (from `app/backend/`). It requires no modification — new test files under `app/frontend/src/**/*.test.tsx` and `app/backend/tests/test_*.py` are auto-discovered by Vitest/pytest respectively.
- Git status confirms no in-flight edits overlap any file this plan creates or modifies.

Exact commands this plan relies on for verification (§10), all discovered from `app/README.md` and `.github/workflows/ci.yml`, none invented:

```
# from app/
npm install
npm run lint --workspace frontend
npm run typecheck --workspace frontend
npm run format:check --workspace frontend
npm run test --workspace frontend
npm run build --workspace frontend

# from app/backend/ (after: python -m venv .venv && activate)
pip install -r requirements-dev.txt
ruff check .
black --check .
mypy .
pytest
```

---

## 4. Scope

### CREATE

| # | File | Purpose |
|---|---|---|
| 1 | `app/backend/schemas/ingredients.py` | Pydantic schemas: `SupplierCreate`, `SupplierUpdate`, `SupplierOut`; `IngredientCreate`, `IngredientUpdate`, `IngredientOut` (incl. computed `has_supplier`, `effective_safety_margin_days`, `safety_margin_source`, `safety_margin_gap`); cross-field validator (perishable ⇒ `shelf_life_days` required) |
| 2 | `app/backend/services/ingredient_service.py` | CRUD service functions for `Supplier`/`Ingredient` (list/create/update), FK-existence check for `supplier_id`, the safety-margin precedence/gap computation used to build `IngredientOut` |
| 3 | `app/backend/routes/ingredients.py` | Two `APIRouter`s: `suppliers_router` (`GET/POST/PUT /suppliers`, `/suppliers/{id}`) and `ingredients_router` (`GET/POST/PUT /ingredients`, `/ingredients/{id}`), both depending on `get_current_user` |
| 4 | `app/backend/scripts/seed_demo_ingredients.py` | Opt-in CLI (`python -m scripts.seed_demo_ingredients`): creates schema + inserts a **fixture-only** 2-supplier/3-ingredient dataset (one ingredient with no supplier, one ingredient/supplier pair with no safety margin) for manual smoke-testing. **Not** invoked from `main.py`'s startup hook. |
| 5 | `app/backend/tests/test_suppliers_api.py` | AC2/AC4: create/list/update suppliers; validation (name required, lead time ≥ 0, safety margin ≥ 0 or null); duplicate-name conflict |
| 6 | `app/backend/tests/test_ingredients_api.py` | AC1/AC2/AC3/AC4: create/list/update ingredients; perishable ⇒ shelf-life-required validation; supplier picker rejects a nonexistent `supplier_id`; nested `supplier` summary shape |
| 7 | `app/backend/tests/test_safety_margin_gap_logic.py` | AC4/AC5: pure unit tests of the precedence function — override wins, supplier default used when no override, both-null ⇒ gap (never `0`) |
| 8 | `app/backend/tests/test_seed_demo_ingredients.py` | Fixture-only seed idempotency + shape (exactly 2 suppliers/3 ingredients; the deliberately-un-mapped and deliberately-no-safety-margin rows are present) |
| 9 | `app/frontend/src/lib/ingredients-api.ts` | Typed API functions (`listSuppliers`, `createSupplier`, `updateSupplier`, `listIngredients`, `createIngredient`, `updateIngredient`) built on `apiClient`; shared `Supplier`/`Ingredient` TS types |
| 10 | `app/frontend/src/lib/ingredients-api.test.ts` | Request shape / error-propagation behavior of the new API functions (mirrors `api-client.test.ts`'s pattern) |
| 11 | `app/frontend/src/routes/ingredients-suppliers-setup.tsx` | `/data-setup/ingredients-suppliers` page: fetches suppliers + ingredients, owns loading/empty/error page-level state, composes the two sections below |
| 12 | `app/frontend/src/routes/ingredients-suppliers-setup.test.tsx` | Loading/empty/error/data states; AC3/AC5 flags visible in rendered rows; add/edit forms open and submit |
| 13 | `app/frontend/src/components/ingredients-suppliers/supplier-list-section.tsx` | Supplier list table (name, lead time, safety margin) + "Add supplier" entry point, using `supplier-form.tsx` |
| 14 | `app/frontend/src/components/ingredients-suppliers/supplier-form.tsx` | Controlled add/edit form: name, lead time (number input), safety margin (optional number input) |
| 15 | `app/frontend/src/components/ingredients-suppliers/supplier-form.test.tsx` | Validation: name/lead-time required, lead time non-negative; submit calls the right create/update function |
| 16 | `app/frontend/src/components/ingredients-suppliers/ingredient-master-section.tsx` | Ingredient master table (unit, unit cost, perishable checkbox, shelf life, mapped supplier, effective safety margin) + "Add ingredient" entry point, using `ingredient-form.tsx` and `gap-flag.tsx` |
| 17 | `app/frontend/src/components/ingredients-suppliers/ingredient-form.tsx` | Controlled add/edit form: name, unit, unit cost, perishable checkbox, shelf life (enabled/required only when perishable), supplier `<select>` picker (populated only from existing suppliers — cannot free-type a nonexistent supplier), safety-margin override (optional) |
| 18 | `app/frontend/src/components/ingredients-suppliers/ingredient-form.test.tsx` | Validation: perishable requires shelf life; picker only offers existing suppliers; submit payload shape |
| 19 | `app/frontend/src/components/ingredients-suppliers/gap-flag.tsx` | Small reusable component: renders a visible, textual (not color-only) flag when a boolean gap prop is `true`; renders nothing otherwise. Reused for both AC3 (no supplier) and AC5 (no safety margin) |
| 20 | `app/frontend/src/components/ingredients-suppliers/gap-flag.test.tsx` | Renders the flag text when `true`; renders nothing when `false` |

### MODIFY

| # | File | Change |
|---|---|---|
| 1 | `app/backend/db/models.py` | Add `Supplier` (`id`, `name` unique, `lead_time_days`, `safety_margin_days` nullable, `created_at`) and `Ingredient` (`id`, `name` unique, `unit`, `unit_cost`, `perishable`, `shelf_life_days` nullable, `supplier_id` nullable FK, `safety_margin_days_override` nullable, `created_at`) SQLAlchemy models, plus their `CheckConstraint`s (§7). No change to `User`/`UserSession`/`LoginAttempt`. |
| 2 | `app/backend/main.py` | `app.include_router(suppliers_router)`, `app.include_router(ingredients_router)`. No change to the `lifespan` hook's seeding behavior (ingredient/supplier fixture seeding is opt-in CLI only, §12 A6). |
| 3 | `app/frontend/src/lib/api-client.ts` | Add `apiClient.put(path, body)` (same pattern as `post`) — additive; `get`/`post` signatures and behavior are unchanged. |
| 4 | `app/frontend/src/App.tsx` | Add one new route: `/data-setup/ingredients-suppliers`, wrapped in the existing `RequireAuth`, rendering `IngredientsSuppliersSetupRoute`. |
| 5 | `app/frontend/src/test/App.test.tsx` | Extend the routing smoke test to also cover the new route (redirects to `/login` when unauthenticated; renders when authenticated), mirroring how this same test was extended when `ACRI-66` introduced routing. |
| 6 | `app/README.md` | Add a short "Ingredients & Suppliers Setup (ACRI-61)" note under "Scope note" (new endpoints, new route, fixture-seed CLI), mirroring the existing ACRI-66 entry there. |

### DELETE

None.

### REUSE (unmodified, load-bearing for this story)

`app/backend/db/session.py` (`Base`, `engine`, `get_db`), `app/backend/middleware/auth.py` (`get_current_user` — reused exactly as-is, per the task's explicit instruction not to modify it), `app/backend/routes/auth.py`, `app/backend/routes/screens.py`, `app/backend/schemas/auth.py`, `app/backend/services/auth_service.py`, `app/backend/db/seed.py`, `app/backend/scripts/seed_demo_accounts.py`, `app/backend/pyproject.toml`, `app/backend/requirements.txt`, `app/backend/requirements-dev.txt`, `app/backend/tests/conftest.py` (its `client`/`db_session_factory` fixtures are reused by the new backend tests), `app/frontend/src/hooks/use-auth.ts`, `app/frontend/src/lib/auth-context.tsx`, `app/frontend/src/components/auth/require-auth.tsx`, `app/frontend/src/components/common/stub-screen.tsx` (unmodified — not used by this screen), `app/frontend/src/lib/screens.ts` (unmodified — unrelated to this screen), `app/frontend/vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`, `eslint.config.js`, `.prettierrc.json`, `vitest.config.ts`, `app/frontend/src/test/setup.ts`, `app/package.json`, `.github/workflows/ci.yml`.

---

## 5. Execution and data flow

**Page load:** Navigating to `/data-setup/ingredients-suppliers` → React Router renders `RequireAuth` (unmodified) → if authenticated, renders `IngredientsSuppliersSetupRoute` → on mount, calls `listSuppliers()` and `listIngredients()` (from `lib/ingredients-api.ts`, both via `apiClient.get`, `credentials: 'include'`) in parallel → page-level state: `loading` while in flight, `error` if either call rejects (`ApiError`), otherwise renders `supplier-list-section` and `ingredient-master-section` with the fetched arrays. An explicit empty-state message is shown per section when its array is empty (Design Document's documented empty state).

**Viewing (AC1/AC2/AC3/AC4/AC5):** `ingredient-master-section` renders one row per `IngredientOut`: `unit`, `unit_cost`, a checkbox bound to `perishable` (disabled/read-only in the table, real editable checkbox in the form), `shelf_life_days` (or "—" if not perishable), the mapped `supplier.name` (or `gap-flag` "No supplier mapped" when `has_supplier` is `false`), and `effective_safety_margin_days` (or `gap-flag` "Safety margin not set" when `safety_margin_gap` is `true`). `supplier-list-section` renders one row per `SupplierOut`: `name`, `lead_time_days`, `safety_margin_days` (or a lighter "Not set — used as default only when set" hint, not a hard error flag, since a supplier's own missing value only becomes an AC5 gap for ingredients that have no override either).

**Add/edit supplier:** `supplier-form` (controlled inputs: name, lead time, optional safety margin) → on submit, `createSupplier`/`updateSupplier` (`apiClient.post`/`apiClient.put`) → backend `routes/ingredients.py::create_supplier`/`update_supplier` → `services/ingredient_service.py` validates and persists via SQLAlchemy → 201/200 `SupplierOut` → page re-fetches (or optimistically merges) the supplier list → the ingredient section's supplier picker and any rows mapped to that supplier reflect the change on next render.

**Add/edit ingredient:** `ingredient-form` (controlled inputs: name, unit, unit cost, perishable checkbox, conditionally-required shelf life, supplier `<select>` picker populated from the already-fetched supplier list, optional safety-margin override) → on submit, `createIngredient`/`updateIngredient` → backend validates (`IngredientCreate`/`IngredientUpdate` Pydantic model incl. cross-field perishable/shelf-life check; service layer checks `supplier_id` references an existing row) → persists → returns `IngredientOut` with the computed `effective_safety_margin_days`/`safety_margin_source`/`safety_margin_gap`/`has_supplier` fields → page updates the ingredient list.

**Safety-margin precedence (AC4/AC5), computed server-side, never persisted twice:** `ingredient_service.py::resolve_safety_margin(ingredient, supplier)` → if `ingredient.safety_margin_days_override is not None`: return `(override, "ingredient")`; elif `supplier is not None and supplier.safety_margin_days is not None`: return `(supplier.safety_margin_days, "supplier")`; else: return `(None, None)` → `IngredientOut.safety_margin_gap = effective_safety_margin_days is None`. This function is pure and unit-tested in isolation (`test_safety_margin_gap_logic.py`) so the precedence rule has a single, directly-testable source of truth rather than being re-implemented in the route layer or the frontend.

---

## 6. Contracts, validation, error handling, and security

### Backend API contracts

| Endpoint | Auth required | Request | 200/201 Response | Error responses |
|---|---|---|---|---|
| `GET /suppliers` | Yes | none | `SupplierOut[]`, ordered by name | `401` (no/invalid session) |
| `POST /suppliers` | Yes | `SupplierCreate {name: str, lead_time_days: int, safety_margin_days: int \| null}` | `201 SupplierOut` | `401`; `422` (validation: empty name, negative lead time/safety margin); `409` (duplicate name) |
| `PUT /suppliers/{id}` | Yes | `SupplierUpdate` (same shape) | `200 SupplierOut` | `401`; `404` (unknown id); `422`; `409` (duplicate name) |
| `GET /ingredients` | Yes | none | `IngredientOut[]`, ordered by name, each with nested `supplier: {id, name, lead_time_days} \| null` and computed `has_supplier`, `effective_safety_margin_days`, `safety_margin_source`, `safety_margin_gap` | `401` |
| `POST /ingredients` | Yes | `IngredientCreate {name, unit, unit_cost, perishable, shelf_life_days: int\|null, supplier_id: int\|null, safety_margin_days_override: int\|null}` | `201 IngredientOut` | `401`; `422` (validation incl. perishable⇒shelf_life_days required, negative unit_cost/shelf_life/safety_margin); `422` (`supplier_id` does not reference an existing supplier); `409` (duplicate name) |
| `PUT /ingredients/{id}` | Yes | `IngredientUpdate` (same shape) | `200 IngredientOut` | `401`; `404`; `422` (same as above); `409` |

No `DELETE` endpoints and no single-resource `GET /suppliers/{id}` / `GET /ingredients/{id}` are added: the task's authorized resolution scopes this story to "manual add/edit/view" — the list (`GET`) endpoints serve "view," and edit forms are pre-filled from the already-fetched list in memory, so a per-id `GET` is not required. Deletion is out of scope for this story (see §12 Q1 — flagged, not silently assumed).

### Persistence (SQLite, via SQLAlchemy — `ARCH-012`)

- `suppliers`: `id INTEGER PK`, `name TEXT UNIQUE NOT NULL`, `lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0)`, `safety_margin_days INTEGER NULL CHECK (safety_margin_days IS NULL OR safety_margin_days >= 0)`, `created_at DATETIME NOT NULL DEFAULT now`.
- `ingredients`: `id INTEGER PK`, `name TEXT UNIQUE NOT NULL`, `unit TEXT NOT NULL`, `unit_cost FLOAT NOT NULL CHECK (unit_cost >= 0)`, `perishable BOOLEAN NOT NULL DEFAULT 0`, `shelf_life_days INTEGER NULL CHECK (shelf_life_days IS NULL OR shelf_life_days > 0)`, `supplier_id INTEGER NULL REFERENCES suppliers(id)`, `safety_margin_days_override INTEGER NULL CHECK (safety_margin_days_override IS NULL OR safety_margin_days_override >= 0)`, `created_at DATETIME NOT NULL DEFAULT now`, plus a table-level `CheckConstraint("perishable = 0 OR shelf_life_days IS NOT NULL", name="ck_ingredients_shelf_life_when_perishable")` as a DB-level backstop for the same rule the Pydantic cross-field validator enforces at the API boundary (defense in depth, same pattern `ACRI-66` used for `users.persona`).
- No FK `ON DELETE` behavior is configured (SQLite does not enforce FK actions without a `PRAGMA foreign_keys=ON` this repo does not currently set — not changed here to avoid an unrelated behavior change to the existing schema/session module). Since this story adds no `DELETE /suppliers/{id}` endpoint, the question of what happens to mapped ingredients on supplier deletion does not arise yet; flagged for whichever future story adds deletion.

### AuthN/AuthZ

- Both new routers depend on `middleware/auth.py::get_current_user`, reused verbatim (unmodified) — identical to how `routes/screens.py` gates its 4 stub routes. No persona-based branching: both personas (kitchen-manager, fb-manager) get identical access, consistent with `ACRI-66`'s AC5 precedent.
- No new session/cookie/CORS logic is introduced.

### Error handling

- Cross-field validation (perishable ⇒ shelf life required) raises inside a Pydantic `model_validator`, surfaced as a standard FastAPI `422` — consistent with how `LoginRequest`'s field validators already behave in this repo.
- `supplier_id` referencing a nonexistent supplier is checked in `ingredient_service.py` (requires a DB lookup, so it cannot be a pure Pydantic validator) and raises `HTTPException(422, "supplier_id does not reference an existing supplier")`.
- Unique-name collisions are pre-checked in the service layer (lookup-then-create/update) and, as a backstop, an `IntegrityError` on commit is caught and re-raised as `HTTPException(409, "<entity> with this name already exists")`.
- Unknown `id` on `PUT` → `HTTPException(404, "<Entity> not found")`.
- Missing/invalid session → generic `401 {"detail": "Not authenticated"}` (unchanged, from the reused dependency).

### Idempotency/concurrency

- `POST` is not idempotent by nature (each call creates a new row); duplicate-name attempts are rejected (`409`), not silently deduplicated.
- No optimistic-concurrency/versioning is introduced — POC scale, single kitchen-manager persona, and the story's own "no ongoing updates after initial load" out-of-scope note make last-write-wins on `PUT` an acceptable, low-risk default (`[ASSUMPTION]`, §12).
- SQLite single-writer model (already the architecture's accepted posture, `ARCH-012`) is unchanged and sufficient at this volume.

---

## 7. Data migration and backward compatibility

Greenfield tables (`suppliers`, `ingredients`) — no pre-existing data to migrate, and no existing table is altered. Schema is created via the already-established `Base.metadata.create_all(engine)` call in `main.py`'s startup hook (unchanged mechanism, now also creating these two new tables the first time it runs against a given `app.db`/test database) — consistent with the interim, no-Alembic posture `ACRI-66` already adopted for this scaffold. No backward-compatibility concern: this is the first version of these tables.

**Data model precedence (authorized resolution, restated precisely for the schema):** `safety_margin_days` is a required-but-nullable-until-set field on `Supplier`, acting as the default safety margin for every ingredient mapped to that supplier. `Ingredient.safety_margin_days_override` is optional and nullable; when set, it takes precedence over the mapped supplier's value for that ingredient. If both the ingredient's own override and its mapped supplier's value are null (or the ingredient has no mapped supplier at all), `AC5`'s gap flag applies (`effective_safety_margin_days = None`, `safety_margin_gap = true`) — the value is never silently defaulted to `0`.

---

## 8. Observability/configuration

- No new environment variables are required — the new routes/services use the existing `DATABASE_URL`/`get_db` plumbing and the existing CORS configuration (`FRONTEND_ORIGIN`) unchanged.
- A single `logger.info` call is added in `ingredient_service.py` on successful create/update of a `Supplier`/`Ingredient` (entity type + id, no PII), for minimal operational traceability consistent with this repo's existing lightweight logging style (`services/auth_service.py`'s `record_login_attempt`) — not mandated by any AC, low-risk addition, flagged as `[ASSUMPTION]` (§12 A5).
- `python -m scripts.seed_demo_ingredients` is documented in `app/README.md` as an opt-in, fixture-only command (mirroring the existing "Seeding demo accounts" subsection's structure) — explicitly not part of the automatic startup path, so a fresh `app.db` never silently gains fake ingredient data just by starting the backend.

---

## 9. Test scenarios

| ID | Level | AC / concern | Expected result | Owner |
|---|---|---|---|---|
| TS-BE-01 | Backend unit | AC1 | `POST /ingredients` then `GET /ingredients` round-trips `unit`, `unit_cost`, `perishable`, `shelf_life_days` exactly | Development |
| TS-BE-02 | Backend unit | AC1 | Creating a perishable ingredient with `shelf_life_days: null` returns `422` | Development |
| TS-BE-03 | Backend unit | AC2 | `POST /suppliers` then `GET /suppliers` round-trips `name`/`lead_time_days`; an ingredient created with a valid `supplier_id` shows that supplier's `name`/`lead_time_days` nested in `GET /ingredients` | Development |
| TS-BE-04 | Backend unit | AC3 | An ingredient created with `supplier_id: null` has `has_supplier: false` in the `GET /ingredients` response | Development |
| TS-BE-05 | Backend unit | AC4 | An ingredient with `safety_margin_days_override` set and a mapped supplier with its own `safety_margin_days` set returns `effective_safety_margin_days == override` and `safety_margin_source == "ingredient"` | Development |
| TS-BE-06 | Backend unit | AC4/AC5 | Ingredient with no override, mapped to a supplier with `safety_margin_days` set → `effective_safety_margin_days == supplier value`, `source == "supplier"`, `safety_margin_gap == false`; ingredient with no override and no mapped supplier (or a supplier with a null value) → `effective_safety_margin_days is None`, `safety_margin_gap == true` (never `0`) | Development |
| TS-BE-07 | Backend unit (pure function) | AC4/AC5 | `resolve_safety_margin()` unit-tested directly for all four combinations (override set/unset × supplier value set/unset) | Development |
| TS-BE-08 | Backend unit | Validation | `POST /ingredients` with `supplier_id: <nonexistent id>` returns `422`; `POST /suppliers`/`POST /ingredients` with a duplicate `name` returns `409`; `PUT` to an unknown id returns `404` | Development |
| TS-BE-09 | Backend unit | Auth reuse | `GET /suppliers` and `GET /ingredients` both return `401` with no session cookie, `200` with a valid one — same dependency, no regression to existing `/screens/*`/`/auth/*` behavior | Development |
| TS-BE-10 | Backend unit | Fixture seed | `seed_demo_ingredients` run twice produces exactly 2 suppliers/3 ingredients total (idempotent); the fixture's deliberately-un-mapped and deliberately-no-safety-margin rows are present and correctly flagged when fetched | Development |
| TS-FE-01 | Frontend component | AC1/AC2 | `ingredients-suppliers-setup` renders a loading state, then the supplier and ingredient tables with the expected columns once both fetches resolve | Development |
| TS-FE-02 | Frontend component | Empty state | With empty arrays from both endpoints, each section shows its documented empty-state message instead of an empty table | Development |
| TS-FE-03 | Frontend component | AC3 | An ingredient row with `has_supplier: false` renders the `gap-flag` "No supplier mapped" text; a mapped row renders the supplier's name instead | Development |
| TS-FE-04 | Frontend component | AC5 | An ingredient row with `safety_margin_gap: true` renders the `gap-flag` "Safety margin not set" text and never renders `0`; a row with a resolved value renders that number | Development |
| TS-FE-05 | Frontend component | Validation | `ingredient-form`: toggling the perishable checkbox on makes the shelf-life field required (blocks submit / shows inline error when empty); the supplier `<select>` only lists suppliers returned by `listSuppliers()`, never a free-text value | Development |
| TS-FE-06 | Frontend component | Validation | `supplier-form`: submitting with an empty name or a negative lead time is blocked with an inline error | Development |
| TS-FE-07 | Frontend component | Error state | If `listSuppliers()`/`listIngredients()` rejects (`ApiError`), the page renders a visible error message instead of silently showing empty tables | Development |
| TS-FE-08 | Frontend unit | API layer | `ingredients-api.ts` functions call `apiClient` with the expected method/path/body and propagate `ApiError` unchanged | Development |
| TS-E2E-01 | e2e / browser | AC1–AC5 | QA: log in, navigate directly to `/data-setup/ingredients-suppliers`, add 3+ ingredients and 2+ suppliers via the UI (one ingredient left unmapped, one left with no safety margin at any level), confirm both gap flags are visible without a page reload, and confirm an unauthenticated visit redirects to `/login` | QA |
| TS-E2E-02 | Manual / accessibility | Design Doc UI-007 | QA: confirm the perishable flag is a real, keyboard-operable checkbox (not a styled div), the supplier picker is a real `<select>`, and both gap flags are readable by a screen reader (not color-only) | QA |
| TS-E2E-03 | Manual | Out-of-scope confirmation | QA: confirm no bulk-upload/file-import control exists anywhere on the screen, and no delete action exists for either suppliers or ingredients (documented out-of-scope, not a defect) | QA |

---

## 10. Verification commands

```
# Frontend — from app/
npm install
npm run lint --workspace frontend
npm run typecheck --workspace frontend
npm run format:check --workspace frontend
npm run test --workspace frontend
npm run build --workspace frontend

# Backend — from app/backend/ (existing .venv, or: python -m venv .venv && .venv\Scripts\activate)
pip install -r requirements-dev.txt
ruff check .
black --check .
mypy .
pytest

# Manual smoke check (from app/backend/, after activating the venv)
uvicorn main:app --reload --port 8000
python -m scripts.seed_demo_ingredients
# then, from another shell, after logging in via the existing /auth/login flow to obtain a session cookie:
curl -i -b cookies.txt http://127.0.0.1:8000/suppliers
curl -i -b cookies.txt http://127.0.0.1:8000/ingredients
```

All commands above are taken verbatim from `app/README.md` and `.github/workflows/ci.yml`; none are invented for this story. CI already runs the frontend and backend blocks above (minus `format:check`/`mypy`, which remain available local-only commands per `README.md`) on every push/PR to `main` and needs no modification — new test files are auto-discovered.

---

## 11. Rollback/recovery

- All changes in this story are additive (two new tables, two new backend routers/services/schemas, one additive method on the existing `apiClient`, one new frontend route + its own feature components). No existing endpoint, table, or component is altered destructively; `app/backend/main.py`/`app/frontend/src/App.tsx`/`app/frontend/src/lib/api-client.ts`/`app/README.md` each receive small, additive edits only.
- Code rollback: revert the commit(s) introducing this story's files; the four modified files revert cleanly to their `ACRI-66` state via the same commit revert.
- Data rollback: `suppliers`/`ingredients` hold no pre-existing production data (greenfield, POC, local SQLite file). Recovery = delete the local `app.db` file (dev) or drop the two new tables; re-run `python -m scripts.seed_demo_ingredients` if the fixture is wanted again. No data-migration-down path is needed since nothing pre-existed.
- No irreversible external side effects: no email sent, no third-party account created, no production secret provisioned.

---

## 12. Risks, assumptions, deviations, and open questions

**Explicit assumptions (all labeled per the HLD/LLD bypass, none silently invented):**

- **A1** — This plan is grounded directly in Jira `ACRI-61` + `DEC-004`/`DEC-005` + the approved Confluence Tech Stack/Design Document pages + `solution-architecture.md`'s `ARCH-012`/`ARCH-013`, per the explicitly authorized HLD/LLD/architecture-validation bypass. Not a deviation — an authorized substitution of sources, identical treatment to `ACRI-66`.
- **A2** — Safety-margin data model (`Supplier.safety_margin_days` default + `Ingredient.safety_margin_days_override` precedence, both-null ⇒ gap) implemented exactly per the task prompt's authorized resolution for `ACRI-61`'s open question. Not re-litigated here.
- **A3** — Bulk upload is out of scope for this story; manual add/edit/view via the UI is the only data-entry path, per the task prompt's authorized resolution.
- **A4** — This screen sits behind the existing `RequireAuth`/`get_current_user` gate, reused exactly as-is (not modified), per the task prompt's authorized resolution.
- **A5** — A single `logger.info` on create/update is added for minimal traceability — not mandated by any AC, low-risk, reversible; flagged rather than silently added.
- **A6** — Dataset source: no real 30–40/3–5 dataset is fabricated. A minimal, explicitly fixture-only 2-supplier/3-ingredient seed is added as an **opt-in CLI script only** (not wired into backend startup, unlike the `ACRI-66` auth-account seed), so a fresh dev/test database never silently gains fake ingredient rows just by starting the server. The fixture deliberately includes one un-mapped ingredient and one ingredient/supplier pair with no safety margin, specifically so the AC3/AC5 gap-flag UI has something real to demonstrate during manual smoke testing.
- **A7** — `apiClient` gains an additive `put()` method (no existing call site is touched) rather than introducing a second HTTP wrapper — minimal, consistent with the existing `get`/`post` pattern.
- **A8** — Both `Supplier.name` and `Ingredient.name` are enforced unique at the DB level. Not explicitly required by any AC, but a reasonable, low-risk safeguard against duplicate-entry confusion in a small, manually-entered dataset; flagged as an assumption rather than silently added as an unstated hard requirement.
- **A9** — `unit_cost` is stored as `FLOAT`, not a fixed-precision `Numeric`/`Decimal` type — POC-scale pragmatism, consistent with this scaffold's general preference for the simplest adequate tool; flagged as a known rounding-precision tradeoff, not a correctness requirement of any AC.
- **A10** — No `DELETE` endpoint is added for either entity — the authorized resolution's own wording ("manual add/edit/view **only**") is read literally over its parenthetical "a form-based CRUD screen" label, since CRUD's "D" is not in the enumerated verb list. See open question Q1 below — this is flagged, not silently decided as final.
- **A11** — No optimistic-concurrency/versioning (e.g., `updated_at`-based conflict detection) is added to `PUT` — last-write-wins, consistent with the story's own "no ongoing updates after initial load" out-of-scope note and this being a single-kitchen-manager-persona POC.
- **A12** — No FK `ON DELETE` cascade/set-null behavior is configured for `ingredients.supplier_id` — moot for this story since no supplier-delete endpoint exists yet (A10); flagged for whichever future story adds deletion.
- **A13** — `config/project.yaml`'s `development.require_approved_hld/require_approved_lld/require_architecture_validation` still read `true`. This plan does not modify `config/project.yaml` (out of this agent's scope); the discrepancy with `DEC-005`'s bypass is the same, already-flagged gap carried from `ACRI-66`, not newly discovered.

**Open questions (non-blocking — forwarded to tech-lead review, none require a new architecture decision to proceed):**

- **Q1** — Whether "add/edit/view" (A10 above) should be read as deliberately excluding delete for this story, or whether the resolution's parenthetical "CRUD screen" label was meant literally and a `DELETE` endpoint/UI action should be added now. This plan takes the literal, narrower reading (no delete) as the safer, smaller, and more easily-extended-later scope; tech lead should confirm or direct otherwise before implementation.
- **Q2** — Whether a supplier's own missing `safety_margin_days` should itself be visibly flagged in the supplier-list section (independent of whether any ingredient relies on it), or whether the AC5 gap flag should surface only at the ingredient level (this plan's current design — a lighter, non-error hint on the supplier row, and the hard gap flag only where AC5 actually requires it: per-ingredient). Low risk either way; forwarded for tech-lead sign-off on the exact UX treatment.
- **Q3** — Exact visual treatment of the two gap flags (icon vs. text-only, inline vs. banner, row highlight) has no pixel-level spec beyond the Design Document's general description. This plan uses plain, accessible text (e.g. "No supplier mapped", "Safety margin not set") rendered inline in the affected cell; a human/tech-lead should sanity-check the copy and treatment before merge, since no visual design source exists to trace it to (same category of gap `ACRI-66` already left open for its login screen's copy).

**Deviations from approved architecture requiring a route back to architecture approval:** none identified. This plan does not alter any `ARCH-` element; it adds two new, previously-unmodeled data entities consistent with `ARCH-012` (SQLite storage) and `ARCH-013` (configuration surface explicitly anticipating a "safety margin" concept).

**BLOCKED status:** **No.** No material open question above requires an architecture decision this plan is not authorized to make; Q1–Q3 are scoping/UX judgment calls explicitly forwarded to tech-lead review, consistent with how `ACRI-66`'s own open questions were handled at that gate.

---

## 13. Plan checksum

**In-scope file list (CREATE + MODIFY, sorted):**

```
app/README.md
app/backend/db/models.py
app/backend/main.py
app/backend/routes/ingredients.py
app/backend/schemas/ingredients.py
app/backend/scripts/seed_demo_ingredients.py
app/backend/services/ingredient_service.py
app/backend/tests/test_ingredients_api.py
app/backend/tests/test_safety_margin_gap_logic.py
app/backend/tests/test_seed_demo_ingredients.py
app/backend/tests/test_suppliers_api.py
app/frontend/src/App.tsx
app/frontend/src/components/ingredients-suppliers/gap-flag.test.tsx
app/frontend/src/components/ingredients-suppliers/gap-flag.tsx
app/frontend/src/components/ingredients-suppliers/ingredient-form.test.tsx
app/frontend/src/components/ingredients-suppliers/ingredient-form.tsx
app/frontend/src/components/ingredients-suppliers/ingredient-master-section.tsx
app/frontend/src/components/ingredients-suppliers/supplier-form.test.tsx
app/frontend/src/components/ingredients-suppliers/supplier-form.tsx
app/frontend/src/components/ingredients-suppliers/supplier-list-section.tsx
app/frontend/src/lib/api-client.ts
app/frontend/src/lib/ingredients-api.test.ts
app/frontend/src/lib/ingredients-api.ts
app/frontend/src/routes/ingredients-suppliers-setup.test.tsx
app/frontend/src/routes/ingredients-suppliers-setup.tsx
app/frontend/src/test/App.test.tsx
```

**Counts:**

| Category | Count |
|---|---|
| CREATE | 20 |
| MODIFY | 6 |
| DELETE | 0 |
| REUSE (unmodified, referenced) | 26 |
| **Total in-scope (CREATE+MODIFY)** | **26** |
