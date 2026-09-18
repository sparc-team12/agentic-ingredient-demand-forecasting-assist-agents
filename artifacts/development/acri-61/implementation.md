# Implementation Report — ACRI-61 (Ingredients & Suppliers Setup)

**Work item:** ACRI-61 (Story-Id US-026, epic ACRI-35 "[Data Setup] Data Setup")
**Plan checksum:** sha256:cde7761056f7b1c74b0bbfe1b9f7bfb0e6008ac983461b09d823510d0e234276 (matches `tech-lead-review.json`)
**Repository:** agentic-ingredient-demand-forecasting-assist-agents
**Branch/base ref:** `devagent` (pre-existing working branch; no branch operations performed)
**Implementation round:** 1

## Files changed

### CREATE (20, per plan §4)
Backend: `schemas/ingredients.py`, `services/ingredient_service.py`, `routes/ingredients.py`, `scripts/seed_demo_ingredients.py`, `tests/test_suppliers_api.py`, `tests/test_ingredients_api.py`, `tests/test_safety_margin_gap_logic.py`, `tests/test_seed_demo_ingredients.py`.
Frontend: `lib/ingredients-api.ts` (+ test), `routes/ingredients-suppliers-setup.tsx` (+ test), `components/ingredients-suppliers/{supplier-list-section.tsx, supplier-form.tsx (+test), ingredient-master-section.tsx, ingredient-form.tsx (+test), gap-flag.tsx (+test)}`.

### MODIFY (6, per plan §4)
`app/backend/db/models.py` (added `Supplier`/`Ingredient` models + CheckConstraints; `User`/`UserSession`/`LoginAttempt` untouched), `app/backend/main.py` (registered the two new routers; no lifespan/seeding change), `app/frontend/src/lib/api-client.ts` (additive `put()`), `app/frontend/src/App.tsx` (new route), `app/frontend/src/test/App.test.tsx` (extended), `app/README.md`.

### Deviation — cross-cutting visual design pass (disclosed, not silent)
Per direct human instruction during this session ("continue building ui") after visually confirming via a live browser check (Playwright) that the app was functionally correct but had **zero visual styling** (the scaffold's placeholder `styles.css` was explicitly "no design system decisions made here"), a real visual design was authored and applied. This went beyond ACRI-61's own plan scope, touching files belonging to both this story and the already-`READY_FOR_QA` `ACRI-66`:

- **CREATE:** `app/frontend/src/components/common/app-shell.tsx` — a shared top bar (brand, auth-gated nav links to all 5 screens, signed-in user + logout), wrapping every route. Presentational/navigation only; adds no business logic.
- **MODIFY:** `app/frontend/src/styles.css` (full rewrite: CSS custom-property design tokens, layout/card/table/form/button/badge classes), `app/frontend/src/App.tsx` (wrapped in `AppShell`), `app/frontend/src/routes/login.tsx`, `app/frontend/src/components/auth/login-form.tsx`, `app/frontend/src/components/common/stub-screen.tsx` (className additions only — **no DOM structure, text, or behavior changed** on any ACRI-66 file), plus className additions on this story's own `ingredients-suppliers-setup.tsx` and its five sub-components (`supplier-list-section.tsx`, `ingredient-master-section.tsx`, `gap-flag.tsx` — now rendered as a `.badge--warning`, still plain text, never color-only per the Design Document's accessibility rule — `supplier-form.tsx`, `ingredient-form.tsx`).

No test assertion relies on DOM structure/snapshots (all use `getByRole`/`getByLabelText`/text queries), so this was verifiable as safe before and after: full frontend suite re-run clean (44/44) both immediately before and after this pass. `ACRI-66`'s own `dev-status.json` (`post_qa_handoff_annotations`) and `qa-handoff.md` (a dated "Post-handoff annotation" section) have been annotated (not re-opened) to record that this later, non-functional styling touch occurred.

## Acceptance criteria implemented

| AC | Evidence |
|---|---|
| AC1 (ingredients viewable: unit, unit cost, perishable, shelf life) | `ingredient-master-section.tsx` table; `test_ingredients_api.py`, `ingredients-suppliers-setup.test.tsx` |
| AC2 (suppliers viewable with lead time; ingredient shows mapped supplier) | `supplier-list-section.tsx`, `ingredient-master-section.tsx`; `test_suppliers_api.py`, `test_ingredients_api.py` |
| AC3 (no supplier mapped → visibly flagged) | `GapFlag` ("No supplier mapped") driven by `IngredientOut.has_supplier`; `test_ingredients_api.py`, `gap-flag.test.tsx`, `ingredients-suppliers-setup.test.tsx` |
| AC4 (safety-margin per ingredient-or-supplier, captured/viewable) | `effective_safety_margin_days` precedence (`override ?? supplier.safety_margin_days ?? None`); `test_safety_margin_gap_logic.py` |
| AC5 (missing safety-margin flagged, never defaulted to 0) | `IngredientOut.safety_margin_gap`; `GapFlag` ("Safety margin not set"); `test_safety_margin_gap_logic.py`, `gap-flag.test.tsx` |

## Tests added
Backend: `test_suppliers_api.py`, `test_ingredients_api.py`, `test_safety_margin_gap_logic.py`, `test_seed_demo_ingredients.py` (46 new tests, bringing the suite to 90).
Frontend: `ingredients-api.test.ts`, `ingredients-suppliers-setup.test.tsx`, `supplier-form.test.tsx`, `ingredient-form.test.tsx`, `gap-flag.test.tsx` (33 new tests, bringing the suite to 44).

## Commands executed (real results)

- Backend (`app/backend`, `.venv`): `pytest -q` → **90 passed**; `ruff check .` → clean; `black --check .` → clean; `mypy .` → clean.
- Frontend (`app/frontend`): `npm run typecheck` → clean; `npm run lint` → 0 errors (1 pre-existing warning in `auth-context.tsx`, unrelated); `npm run test -- --run` → **44 passed**; `npm run build` → succeeds.
- Live verification: both dev servers started (FastAPI on :8000, Vite on :5173), demo accounts + fixture ingredients/suppliers seeded, driven end-to-end with Playwright (headless Chromium) — login → nav bar renders all 5 screens with active-state highlighting → Ingredients & Suppliers Setup renders real seeded data, gap-flag badges render correctly for the deliberately-unmapped ingredient and the deliberately-no-safety-margin rows → Add Ingredient form opens, renders correctly styled. Screenshots captured and visually reviewed.

## Migrations/configuration/operational notes
No migration tool; new tables created via existing `Base.metadata.create_all()` at startup (same interim approach as ACRI-66). `scripts/seed_demo_ingredients.py` is opt-in CLI only, not invoked automatically.

## Deviations/adjacent files
See "Deviation — cross-cutting visual design pass" above. No other adjacent files.

## Unresolved concerns / known QA considerations
- No bulk-upload/CSV import (explicitly out of scope for this story per the authorized resolution).
- No DELETE endpoints (manual add/edit/view only, per plan Q1 — accepted at tech-lead review).
- Login-screen/general visual design had no prior design-system source to trace to (Design Document Open Item 8) — the design applied here is authored fresh for this app, not sourced from an approved visual spec; flagged the same way ACRI-66's login-screen copy was flagged.
- Data Setup hub (ACRI-59) doesn't exist yet, so this screen is reached via a standalone route/direct nav link rather than the eventual hub.

**Status: COMPLETED**
