# Implementation Report — ACRI-60, ACRI-62, ACRI-63, ACRI-59 (Data Setup batch)

**Work items:** ACRI-60 (US-025, Menu & Recipe Setup), ACRI-62 (US-027, Current Stock Setup),
ACRI-63 (US-028, Sales History Import), ACRI-59 (US-024, Data Setup Hub) — epic ACRI-35
"[Data Setup] Data Setup"
**Plan checksum:** N/A — human-directed minimal pipeline (no separate planning/tech-lead/code-review
agents for this batch; this agent planned, implemented, and tested in one dispatch per explicit
instruction). Governing overrides: DEC-004 (Jira stories are the requirements source, no PRD gate)
and DEC-005 (HLD/LLD/architecture-validation gate bypassed for ACRI development) in
`workflow/decisions.md`.
**Repository:** agentic-ingredient-demand-forecasting-assist-agents
**Branch/base ref:** `devagent` (pre-existing working branch; no branch/commit/push operations
performed)
**Implementation round:** 1

Build order followed the dispatch: ACRI-60 → ACRI-62 → ACRI-63 → ACRI-59 (hub depends on the
other 3 plus the already-`READY_FOR_QA` ACRI-61). All 4 items reuse `get_current_user`/
`RequireAuth` verbatim (untouched) and the existing design-system classes/`AppShell` nav from
ACRI-61/ACRI-66 — no new CSS classes were introduced except reusing `.badge--warning` (already
existed) for every new gap flag; the Data Setup hub's "Loaded" state deliberately uses plain text
rather than inventing a new badge variant.

## Files changed

### Backend — CREATE

- `app/backend/schemas/menu_recipe.py`, `app/backend/services/menu_recipe_service.py`,
  `app/backend/routes/menu_recipe.py`, `app/backend/tests/test_menu_recipe_api.py` (ACRI-60)
- `app/backend/schemas/current_stock.py`, `app/backend/services/current_stock_service.py`,
  `app/backend/routes/current_stock.py`, `app/backend/tests/test_current_stock_api.py` (ACRI-62)
- `app/backend/schemas/sales_history.py`, `app/backend/services/sales_history_service.py`,
  `app/backend/routes/sales_history.py`, `app/backend/tests/test_sales_history_api.py` (ACRI-63)
- `app/backend/schemas/data_setup.py`, `app/backend/services/data_setup_service.py`,
  `app/backend/routes/data_setup.py`, `app/backend/tests/test_data_setup_status_api.py` (ACRI-59)

### Backend — MODIFY (additive only)

- `app/backend/db/models.py` — added `Dish`, `RecipeLine`, `CurrentStock`,
  `SalesHistoryRecord` ORM models + `CheckConstraint`/`UniqueConstraint`s. `User`/`UserSession`/
  `LoginAttempt`/`Supplier`/`Ingredient` untouched.
- `app/backend/main.py` — registered the 4 new routers (`dishes_router`, `current_stock_router`,
  `sales_history_router`, `data_setup_router`). No lifespan/seeding change.

### Frontend — CREATE

- `app/frontend/src/lib/menu-recipe-api.ts` (+test), `app/frontend/src/routes/menu-recipe-setup.tsx`
  (+test), `app/frontend/src/components/menu-recipe/{dish-form.tsx (+test), recipe-line-form.tsx
  (+test), dish-recipe-card.tsx}` (ACRI-60)
- `app/frontend/src/lib/current-stock-api.ts` (+test),
  `app/frontend/src/routes/current-stock-setup.tsx` (+test),
  `app/frontend/src/components/current-stock/{current-stock-form.tsx (+test),
  current-stock-table.tsx}` (ACRI-62)
- `app/frontend/src/lib/sales-history-api.ts` (+test),
  `app/frontend/src/routes/sales-history-import.tsx` (+test),
  `app/frontend/src/components/sales-history/{sales-history-record-form.tsx (+test),
  dish-sales-history-section.tsx}` (ACRI-63)
- `app/frontend/src/lib/data-setup-api.ts` (+test), `app/frontend/src/routes/data-setup-hub.tsx`
  (+test), `app/frontend/src/components/data-setup/data-setup-category-card.tsx` (+test) (ACRI-59)

### Frontend — MODIFY

- `app/frontend/src/App.tsx` — added routes `/data-setup` (hub), `/data-setup/menu-recipe-setup`,
  `/data-setup/current-stock-setup`, `/data-setup/sales-history-import`, each wrapped in
  `RequireAuth`; `/data-setup/ingredients-suppliers` (ACRI-61) untouched.
- `app/frontend/src/components/common/app-shell.tsx` — `DATA_SETUP_LINK` re-pointed from
  `/data-setup/ingredients-suppliers` to `/data-setup` (the new hub). `SCREENS`
  (`lib/screens.ts`, the top-nav's other source) was deliberately **not** modified — the 3 new
  category screens are reached from the hub, not the top nav, per the dispatch instruction.
  `lib/screens.ts` itself was inspected but not changed.
- `app/frontend/src/test/App.test.tsx` — extended with auth-gating + rendering assertions for all
  4 new routes.

No dependency changes, no public-contract changes to any ACRI-61/ACRI-66 file, no CSS file
changes.

## Acceptance criteria implemented

### ACRI-60 — Menu & Recipe Setup

| AC | Evidence |
|---|---|
| Load/view 15-20 dishes, each dish's recipe viewable in full (not summarized) | `GET /dishes` returns every dish with its complete `recipe_lines` array (no pagination/truncation); `menu-recipe-setup.tsx` renders one `DishRecipeCard` per dish with its full recipe table; `test_dish_recipe_is_viewable_in_full_not_summarized_ac1` |
| Recipe line referencing an ingredient not in the Ingredient table is flagged (not rejected) | `resolve_ingredient_id()` case-insensitive name lookup; unmatched name stores `ingredient_id=NULL` and `ingredient_flagged=True`, still `201 Created`; `GapFlag` renders "Not in Ingredients master"; `test_create_recipe_line_with_unmatched_ingredient_is_flagged_not_rejected_ac2`, `menu-recipe-setup.test.tsx` |
| Manual add/edit only | `POST`/`PUT` on `/dishes` and `/dishes/{id}/recipe-lines/{id}`; no delete endpoint |

### ACRI-62 — Current Stock Setup

| AC | Evidence |
|---|---|
| Load/view quantity-on-hand + use-by-date per existing ingredient (one row per ingredient) | `GET /current-stock` returns exactly one entry per `Ingredient` row (left-joined with any snapshot); `test_lists_one_row_per_existing_ingredient_even_with_no_snapshot_yet_ac1` |
| Upsert on edit, not a log | `PUT /current-stock/{ingredient_id}` creates the row if absent, else updates it in place (unique `ingredient_id`); `test_upsert_current_stock_updates_existing_row_not_a_log` asserts row count stays 1 after 2 edits |
| Perishable ingredient with no use-by date is flagged | `use_by_date_gap = perishable and use_by_date is None`; `test_perishable_ingredient_with_no_use_by_date_is_flagged_ac2`, `test_non_perishable_ingredient_with_no_use_by_date_is_never_flagged` |
| Snapshot, not live | No polling/websocket; screen only refreshes on explicit load/edit, documented in the route's own comment header |

### ACRI-63 — Sales History Import

| AC | Evidence |
|---|---|
| Load/view up to 12 weeks (84 days) of daily units-sold per dish (FK to Dish) | `SalesHistoryRecord.dish_id` FK → `Dish`; `GET /sales-history` returns every dish's full `records` list; `test_dish_with_84_distinct_days_has_full_history_flag_true_ac2` |
| Manual add-record form | `POST /sales-history` only (no bulk import); `SalesHistoryRecordForm` |
| Compute/display distinct days of history per dish; flag if <84 | `distinct_days_of_history = len({record.sale_date ...})`; `has_full_history = distinct_days >= 84`; `TARGET_DAYS_OF_HISTORY = 84`; `test_dish_with_fewer_than_84_distinct_days_is_flagged_ac2` |

### ACRI-59 — Data Setup Hub

| AC | Evidence |
|---|---|
| Lists all 4 categories with loaded/not-loaded status | `GET /data-setup/status` (new endpoint) returns 4 `DataSetupCategoryStatus` entries; `loaded` = row-count > 0 per category's own table (`Dish`, `Ingredient`, `CurrentStock`, `SalesHistoryRecord`); `test_all_categories_not_loaded_on_a_fresh_database_ac1`, `test_category_becomes_loaded_once_at_least_one_row_exists_ac1` |
| Not-loaded visibly distinguished | `.badge--warning` "Not loaded" vs plain "Loaded" text — never color-only, text always present |
| All-4-loaded state reflected | `all_loaded` computed server-side; hub shows "All 4 data categories are loaded." only when true; `test_all_loaded_is_true_only_once_every_category_has_a_row_ac2` |
| Each card links to its screen; built last, depends on items 1-3 + ACRI-61 | `DataSetupCategoryCard` renders a `<Link>` to `category.path`; `test_category_entries_carry_label_and_path`, `data-setup-hub.test.tsx::links each card to its own screen` |
| Nav re-pointed at hub; 3 new screens not on top nav | `app-shell.tsx` `DATA_SETUP_LINK.path` → `/data-setup`; `lib/screens.ts` unmodified (no new top-nav entries) |

## Tests added

**Backend** (all new, 36 tests; full suite 90 → 126, all passing):
- `test_menu_recipe_api.py` (14 tests)
- `test_current_stock_api.py` (8 tests)
- `test_sales_history_api.py` (8 tests)
- `test_data_setup_status_api.py` (5 tests)
(Note: totals above are per-file test counts as run by pytest; combined new-test count is 36,
verified by the collected/passed count below.)

**Frontend** (all new, 51 tests; full suite 56 → 107, all passing):
- `lib/menu-recipe-api.test.ts`, `lib/current-stock-api.test.ts`, `lib/sales-history-api.test.ts`,
  `lib/data-setup-api.test.ts`
- `routes/menu-recipe-setup.test.tsx`, `routes/current-stock-setup.test.tsx`,
  `routes/sales-history-import.test.tsx`, `routes/data-setup-hub.test.tsx`
- `components/menu-recipe/dish-form.test.tsx`, `components/menu-recipe/recipe-line-form.test.tsx`
- `components/current-stock/current-stock-form.test.tsx`
- `components/sales-history/sales-history-record-form.test.tsx`
- `components/data-setup/data-setup-category-card.test.tsx`
- `test/App.test.tsx` extended (+5 cases: hub + 3 category-screen auth-gating/rendering)

## Migrations/configuration/operational notes

No migration tool exists for this codebase (same interim approach as ACRI-61/ACRI-66); the 4 new
tables (`dishes`, `recipe_lines`, `current_stock`, `sales_history_records`) are created via the
existing `Base.metadata.create_all()` call at backend startup — no changes to that startup logic
were needed. No new environment variables, no new dependencies (backend or frontend). No seed
script was added for these 4 items (none was requested; ACRI-61's `seed_demo_ingredients.py` is
unaffected).

## Commands executed (real results)

**Backend** (`app/backend`, `.venv`):
- `python -m pytest -q` → **126 passed**, 5 warnings (pre-existing `StarletteDeprecationWarning`s
  unrelated to this change; ran twice, before and after `black .` reformatting, both green)
- `ruff check .` → **All checks passed!**
- `black .` (reformatted 4 newly-created files to the project's line-length/style) then
  `black --check .` → **49 files would be left unchanged** (clean)
- `python -m mypy .` → **Success: no issues found in 49 source files**

**Frontend** (`app/frontend`):
- `npm run test -- --run` → **107 passed** (22 test files); ran twice, before and after
  `prettier --write` reformatting, both green
- `npm run typecheck` → clean (no output, `tsc --noEmit` exit 0)
- `npm run lint` → **0 errors** (1 pre-existing warning in `auth-context.tsx`, unrelated to this
  change, same baseline noted in ACRI-61's report)
- `npx prettier --write <new/changed files>` (fixed line-wrapping in a handful of new files) then
  `npm run format:check` → **All matched files use Prettier code style!**
- `npm run build` → **succeeds** (`tsc -b && vite build`, `dist/` produced, no errors)

No live/browser (Playwright) verification was performed for this batch — the dispatch's minimal
pipeline directed a single automated-verification pass, not a manual/browser smoke test.

## Deviations / adjacent files

- `app/frontend/src/components/common/app-shell.tsx` was modified (1-line `DATA_SETUP_LINK.path`
  change + comment) exactly as instructed by the dispatch ("re-point the existing 'Data Setup' nav
  link at this new hub route"). This is an ACRI-61-era file but the change was explicitly
  requested, not an undisclosed deviation.
- `app/frontend/src/test/App.test.tsx` (ACRI-66/ACRI-61-era file) was extended with new test cases
  for the new routes — additive only, no existing assertions changed or removed.
- No other adjacent/unplanned files were touched. No new dependencies were added. No public
  contract of ACRI-61/ACRI-66 (schemas, routes, auth) was altered.
- Design choice, disclosed: `RecipeLine.ingredient_id` is a nullable FK resolved by a
  case-insensitive name match at write time (not a live/dynamic re-check on every read). If an
  ingredient is added to the Ingredient master *after* an unmatched recipe line was created, that
  line stays flagged until it is explicitly re-saved (edit re-triggers resolution). This was the
  most direct way to satisfy "flagged, never rejected" while keeping `ingredient_id` a real FK as
  specified in the dispatch's data model.
- Design choice, disclosed: the Data Setup hub's "Loaded" state uses plain text rather than a new
  badge class, to avoid inventing new CSS per the styling instruction — only the pre-existing
  `.badge--warning` class is reused (for "Not loaded"), which still visibly distinguishes the two
  states without a color-only signal.

## Unresolved concerns / known QA considerations

- No delete endpoints anywhere in this batch (dishes, recipe lines, current-stock snapshots, sales
  history records), consistent with ACRI-61's own precedent of "manual add/edit only, no delete."
- Sales History Import has no edit/delete of an already-entered record — only add — matching the
  dispatch's "Manual add-record form" wording literally; a data-entry mistake currently requires a
  fresh record for a different (or duplicate-conflict `409`) date rather than a correction path.
- `RecipeLine`'s ingredient-match resolution is snapshot-at-write, not live (see Deviations above)
  — flagged here explicitly as a QA consideration, not hidden.
- The Data Setup hub's per-category "loaded" signal is a simple row-count check (>= 1 row), not a
  completeness/quality check — e.g. 1 dish with 0 recipe lines still counts as "menu-recipe loaded."
  This matches the literal AC wording ("loaded = at least 1 row exists") but QA should confirm this
  matches stakeholder expectations before demo.
- This batch used the human-directed minimal pipeline (no separate tech-lead/code-review agent
  gate) — all planning, implementation, and verification were performed by this single agent
  dispatch, per explicit instruction recorded in DEC-004/DEC-005.

**Status per item:**
- **ACRI-60 (Menu & Recipe Setup): COMPLETED**
- **ACRI-62 (Current Stock Setup): COMPLETED**
- **ACRI-63 (Sales History Import): COMPLETED**
- **ACRI-59 (Data Setup Hub): COMPLETED**

"COMPLETED" here means local automated verification (tests, lint, typecheck, format, build) is
green for all 4 items, per the commands and evidence above. It does not constitute code review or
QA sign-off.
