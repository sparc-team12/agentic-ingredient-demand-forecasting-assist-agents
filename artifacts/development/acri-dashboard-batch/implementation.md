# Implementation report — Risk Dashboard batch (ACRI-54, ACRI-55, ACRI-56, ACRI-57, ACRI-58)

- **Work items**: ACRI-54 (US-019), ACRI-55 (US-020), ACRI-56 (US-021), ACRI-57 (US-022), ACRI-58 (US-023)
- **Repository**: `c:\Users\aakash.ck\Downloads\agentic-ingredient-demand-forecasting-assist-agents`
- **Branch**: `devagent` (worked on the branch supplied by the orchestrator; no new branch created, per the "make it fast" minimal-pipeline direction — no branch-creation request was given)
- **Base ref**: N/A — no branch operation performed
- **Pipeline mode**: MINIMAL, per explicit human direction relayed by the dispatching orchestrator ("make it fast"): plan → implement → self-test in a single dispatch. No `requirements-validation.json` / `implementation-plan.md` / `tech-lead-review.json` artifacts exist for this batch (this is a deliberate, explicitly authorized deviation from the standard dev-orchestrator gate sequence documented in `.claude/agents/dev-orchestrator-agent.md`, not a fabrication of those artifacts).
- **Implementation round**: 2 (this session re-dispatched the identical batch; on inspection the code, tests, and docs from round 1 were already present, matched the task/AC exactly, and needed no changes — this round consisted of independently re-reading every in-scope file and re-running the full verification suite from scratch against the current working tree; see "This session" under Commands executed below)

## Scope implemented

A new backend aggregation endpoint (`GET /dashboard/risk-summary`) that iterates every `Ingredient`, evaluates both existing risk services (`stockout_risk_service.evaluate_stockout_risk`, `spoilage_risk_service.evaluate_spoilage_risk`) per ingredient, and returns a single severity-ranked list plus an always-unfiltered aggregate waste-exposure total and the live materiality threshold. A rewritten `/risk-dashboard` frontend route (replacing the `StubScreen` stub) renders that data: the aggregate total, a materiality-threshold read/write control, and the ranked table.

## Ranking / tie-break rule (ACRI-54 US-019 AC3 — chosen and documented per the story's explicit invitation to use judgment)

1. **Severity band first, across both risk types**: `Critical > High > Low`. A Critical spoilage row always ranks above a High (or Low) stockout row, and vice versa — severity band is compared before anything else.
2. **Within the same severity band: risk type**, stockout rows before spoilage rows. Interleaving a date-based key (stockout) and a cost-based key (spoilage) on one shared axis would need an arbitrary, undocumented conversion (e.g. an INR-per-day-of-urgency factor) to be meaningful; grouping stockout-then-spoilage within a tied band keeps each type's own natural ordering intact and is honestly explainable to a user.
3. **Within the same severity band and risk type**: stockout rows by `order_by_date` ascending (soonest first, ACRI-56 AC); spoilage rows by `waste_cost_inr` descending (highest cost first, ACRI-57 AC).

Implemented in `services/dashboard_service.py::_sort_key`, covered explicitly by `tests/test_dashboard_service.py` (including the literal AC3 cross-type "Critical spoilage above High stockout" case).

Suppression (ACRI-58 / ACRI-44): `total_waste_exposure_inr` sums **every** spoilage-risk ingredient's waste cost, including ones below the current materiality threshold — never filtered. Every at-risk row (both types) is still returned in `rows`, each tagged with its own `suppressed` flag (always `False` for stockout rows). The Risk Dashboard's visible table (`components/dashboard/risk-table.tsx`) filters `suppressed` rows out of what it renders — a frontend display concern, so the underlying data stays fully traceable through the API rather than being silently dropped server-side.

## Files changed

### Backend
- `app/backend/schemas/dashboard.py` (new) — `DashboardRiskRow`, `DashboardRiskSummaryOut`.
- `app/backend/services/dashboard_service.py` (new) — `get_risk_summary(db, *, anchor=None)`; iterates every `Ingredient`, calls both risk evaluators, applies the ranking rule, computes the unfiltered total.
- `app/backend/routes/dashboard.py` (new) — `dashboard_router`, `GET /dashboard/risk-summary`, gated by `middleware.auth.get_current_user` (reused verbatim, no persona branching, matching every other route in this codebase).
- `app/backend/main.py` (edited) — imports and registers `dashboard_router`; updated the module docstring's route inventory list.
- `app/backend/tests/test_dashboard_service.py` (new) — pure unit tests, direct ORM setup, explicit `anchor` (no wall-clock dependency).
- `app/backend/tests/test_dashboard_api.py` (new) — HTTP-level tests through the public API surface, real `date.today()` (mirrors `test_risk_api.py`'s convention).

### Frontend
- `app/frontend/src/lib/dashboard-api.ts` (new) — `DashboardRiskRow`, `DashboardRiskSummary`, `getRiskSummary()`.
- `app/frontend/src/lib/risk-api.ts` (edited) — added `RiskConfig`, `getRiskConfig()`, `updateRiskConfig()` (the materiality-threshold control's backing calls to `GET/PUT /risk-config`, deferred to this batch per the task description; placed here rather than a new file because it mirrors the backend's `routes/risk.py::risk_config_router`, which lives in the same backend module as the ingredient-risk routes).
- `app/frontend/src/lib/dashboard-api.test.ts`, `app/frontend/src/lib/risk-api.test.ts` (new) — request-shape / error-propagation tests for the above.
- `app/frontend/src/components/dashboard/aggregate-exposure.tsx` + `.test.tsx` (new) — the top-of-dashboard INR total.
- `app/frontend/src/components/dashboard/materiality-threshold-control.tsx` + `.test.tsx` (new) — inline number input + Save, reading/writing `GET/PUT /risk-config`, with the required suppression note.
- `app/frontend/src/components/dashboard/risk-table.tsx` + `.test.tsx` (new) — the severity-ordered table; filters `suppressed` rows before rendering; empty state ("No ingredients currently at risk.") when nothing is visible.
- `app/frontend/src/routes/risk-dashboard.tsx` (rewritten) — was a `StubScreen` stub; now the real dashboard composing the 3 components above, with loading/error states matching `ingredient-detail.tsx`'s conventions.
- `app/frontend/src/routes/risk-dashboard.test.tsx` (new) — route-level integration test (loading, error, populated, empty, threshold-save-and-reload).
- `app/frontend/src/styles.css` (edited) — added one new rule, `.aggregate-exposure__value` (font-size/weight only, reusing existing color variables), for the "large, prominent" total figure the AC explicitly requires; no other new CSS was needed (the severity-ordered list reuses `.data-table`, `.card`, `.page`, and the existing `.badge--critical/high/low` classes verbatim).

No new dependencies were added. No public contract of an existing endpoint was changed — this is purely additive (1 new route, 1 extended frontend module).

## Acceptance criteria implemented

- **ACRI-54 (US-019)**: single combined list, severity-band-first ordering with the documented tie-break, severity shown as both badge color and exact text ("Critical"/"High"/"Low") via the reused `SeverityBadge`.
- **ACRI-55 (US-020)**: every row shows its risk type (`Stockout`/`Spoilage` column); computed by a synchronous loop over every `Ingredient` (no async/background job, per the story's own note about the fixed ~30-40 row dataset).
- **ACRI-56 (US-021)**: stockout rows show `order_by_date` directly in the row.
- **ACRI-57 (US-022)**: spoilage rows show `waste_cost_inr` (INR) and severity band directly in the row.
- **ACRI-58 (US-023)**: single aggregate `total_waste_exposure_inr` at the top, always including suppressed items; materiality-threshold control (read/write `GET/PUT /risk-config`) with the required note.
- Empty-dashboard state: ₹0 total + "No ingredients currently at risk." message (not left blank) — covered by both a service-level test (`test_empty_dashboard_has_zero_total_and_no_rows`), an API-level test (`test_get_risk_summary_is_empty_when_no_ingredients_exist`), and frontend tests at both the component and route level.

## Tests added

Backend (`app/backend`, venv at `.venv`):
- `tests/test_dashboard_service.py` — 7 pure unit tests: empty dashboard, combined ranking rule (severity band → type → tie-break) across a 6-row scenario, the explicit AC3 cross-type case (Critical spoilage ranks above High stockout), stockout ascending `order_by_date` ordering, spoilage descending `waste_cost_inr` ordering, aggregate total including a suppressed row, and stockout rows never marked `suppressed`.
- `tests/test_dashboard_api.py` — 4 HTTP-level tests: auth required (401), empty dashboard, end-to-end both-types aggregation, and total-includes-suppressed-rows through the real `PUT /risk-config` → `GET /dashboard/risk-summary` path.

Frontend (`app/frontend`):
- `src/lib/dashboard-api.test.ts` — 2 tests (request shape, error propagation).
- `src/lib/risk-api.test.ts` — 3 tests for the newly added `getRiskConfig`/`updateRiskConfig` (`getIngredientRisk` already has end-to-end coverage via `ingredient-detail.test.tsx`).
- `src/components/dashboard/aggregate-exposure.test.tsx` — 2 tests (formatted total, ₹0 empty case).
- `src/components/dashboard/materiality-threshold-control.test.tsx` — 5 tests (pre-fill, validation, save + confirmation, save-error surfacing, suppression note).
- `src/components/dashboard/risk-table.test.tsx` — 6 tests (stockout row shape, spoilage row shape, suppressed-row filtering, empty state, all-suppressed-still-empty-state, order preservation).
- `src/routes/risk-dashboard.test.tsx` — 5 tests (loading, error, populated render incl. suppressed-row hidden, empty state, threshold save triggers `PUT` + exactly-one reload `GET`).

## Migrations / configuration / operational notes

- No schema migration — `RiskConfig` already exists (ACRI-44); this batch only adds a read-only aggregation endpoint and reuses the existing table.
- No new environment variables or configuration.
- No telemetry/logging added beyond what the reused services already emit.

## Commands executed

### Prior session (implementation authored; commands run then, per that session's own record)

Backend (`app/backend`, using the existing `.venv`):
- `./.venv/Scripts/python.exe -m pytest tests/test_dashboard_service.py tests/test_dashboard_api.py -q` → **11 passed**.
- `./.venv/Scripts/python.exe -m pytest -q` (full suite) → **201 passed, 6 warnings** in ~154s (190 pre-existing + 11 new; the 6 warnings are pre-existing `StarletteDeprecationWarning`s in unrelated files, not introduced here).
- `./.venv/Scripts/python.exe -m ruff check .` → **All checks passed!**
- `./.venv/Scripts/python.exe -m black --check .` → found 1 file needing formatting (`tests/test_dashboard_service.py`); ran `black tests/test_dashboard_service.py`, then re-ran `--check .` → **all 68 files unchanged** (clean).
- `./.venv/Scripts/python.exe -m mypy .` → initially 2 `type-var` errors in the new test file (comparing `list[date | None]` / `list[float | None]` via `sorted`); fixed by narrowing to non-`None` lists before sorting → **Success: no issues found in 68 source files**.

Frontend (`app/frontend`):
- `npm install` → completed (pre-existing `node_modules` was absent; installed from `package-lock.json`, no dependency changes made).
- `npx vitest run <new files>` → **23 passed** first pass; 1 failure (`getByLabelText` matched both the input's label and the form's `aria-label`, and a `toHaveBeenCalledTimes(2)` assumption was invalidated by mock-call accumulation across `it` blocks in the same file, consistent with this codebase's existing convention of not resetting mocks between tests) → fixed by switching to `getByRole("spinbutton", {name})` and a relative before/after call-count delta → re-ran, **all passed**.
- `npm test` (full suite) → **29 files, 137 tests passed** (pre-existing, unrelated `act(...)` warnings from `ingredient-detail.tsx`/`menu-recipe-setup.tsx` — not introduced by this batch).
- `npm run typecheck` → clean, no output.
- `npm run lint` → **0 errors**, 1 pre-existing unrelated warning (`auth-context.tsx` fast-refresh warning).
- `npm run format:check` → found 2 files needing formatting (`risk-table.tsx`, `risk-table.test.tsx`); ran `npx prettier --write` on them, re-ran `format:check` → **all matched files use Prettier code style**.
- `npm run build` → **built successfully** (`tsc -b && vite build`; 85 modules, `dist/assets/index-*.js` 222.50 kB / gzip 67.47 kB).
- Re-ran `npm test` after the prettier fix → still **137 passed**.

### This session (re-dispatch of the same batch — no code changes were needed; independently re-verified every command against the code as it stands on disk)

On inspection, every file this batch calls for (`schemas/dashboard.py`, `services/dashboard_service.py`, `routes/dashboard.py`, its `main.py` registration, `tests/test_dashboard_service.py`, `tests/test_dashboard_api.py`, and the full frontend set: `lib/dashboard-api.ts`, `lib/risk-api.ts` additions, `components/dashboard/*`, `routes/risk-dashboard.tsx`, and their tests) was already present and matched the plan/AC exactly. Rather than trust the prior session's report, the full verification suite was re-run from scratch this session:

Backend (`app/backend`, using the existing `.venv`):
- `./.venv/Scripts/python.exe -m pytest -q` (full suite) → **201 passed, 6 warnings** in 192.81s (6 pre-existing `StarletteDeprecationWarning`s, unrelated to this batch).
- `./.venv/Scripts/python.exe -m ruff check .` → **All checks passed!**
- `./.venv/Scripts/python.exe -m black --check .` → **All done! 72 files would be left unchanged.**
- `./.venv/Scripts/python.exe -m mypy .` → **Success: no issues found in 73 source files.**

Frontend (`app/frontend`, using the existing `node_modules`):
- `npm run typecheck` → clean, no output.
- `npm run lint` → **0 errors**, 1 pre-existing unrelated warning (`auth-context.tsx` fast-refresh warning).
- `npm test -- --run` (full suite) → **29 files, 137 tests passed** (same pre-existing unrelated `act(...)` warnings as before).
- `npm run build` → **built successfully** (`tsc -b && vite build`; 85 modules, `dist/assets/index-BqfllPFC.js` 222.50 kB / gzip 67.47 kB).

All commands above were run for real in this session against the current working tree; no results were fabricated or carried over without re-execution.

## Deviations / adjacent files

- **Pipeline artifacts**: per the explicit "make it fast" minimal-pipeline direction from the dispatching agent, no `requirements-validation.json`, `implementation-plan.md`, or `tech-lead-review.json` were produced or consumed for this batch — planning, implementation, and self-testing happened in this single dispatch, as instructed. This is a deviation from the standard `dev-orchestrator-agent` gate sequence, explicitly authorized by the dispatch instructions, not a bypass I chose unilaterally.
- **`app/frontend/src/lib/risk-api.ts`** (existing file, extended rather than creating a new `risk-config-api.ts`): added `RiskConfig`/`getRiskConfig`/`updateRiskConfig`. Justification: mirrors the backend's `routes/risk.py`, which hosts both the ingredient-risk and risk-config routers in one module; kept the frontend's file-to-backend-route-module mapping 1:1.
- **`app/frontend/src/styles.css`** (existing file, 1 new rule added): `.aggregate-exposure__value`, needed to satisfy ACRI-58's explicit "large, prominent" requirement for the total figure; no other new CSS was added, and the severity-ordered list itself needed none (reused `.data-table`/`.card`/`.page`/`.badge--*` verbatim), consistent with the task's constraint.
- **`app/backend/main.py`** (existing file, planned integration point per the architecture description: "registered in main.py") — added the import/`include_router` call and a docstring update; this was explicitly called out as in-scope by the architecture description, not an unplanned touch.

No public contract of any pre-existing endpoint changed. No new third-party dependency was added on either side.

## Unresolved concerns / known QA considerations

- This batch was implemented and self-tested by the same agent in one dispatch (explicit minimal-pipeline direction) — there was no independent tech-lead plan review or separate code-review pass. A follow-up code-review/QA pass is recommended before this is treated as release-ready, per the repository's normal gates.
- The exact ordering tie-break rule (stockout-before-spoilage within a tied severity band, rather than an interleaved shared key) was a judgment call explicitly delegated to Development by the story text; if the product owner prefers a different tie-break (e.g., a shared "urgency score"), that is a scope/requirements change, not a bug, and should go back through planning.
- `total_waste_exposure_inr` and the visible `rows` list both currently return **every** row (including suppressed ones, tagged); the suppression filter is applied only in the frontend (`risk-table.tsx`). If a future consumer of this API (e.g., a reporting export) is added, it will need to apply the same `suppressed` filter itself — this is documented in the schema/service docstrings but worth flagging for any new API consumer.
- No pagination was added to `GET /dashboard/risk-summary`; this matches the story's explicit assumption of a fixed ~30-40 ingredient dataset and would need revisiting if that assumption changes.
