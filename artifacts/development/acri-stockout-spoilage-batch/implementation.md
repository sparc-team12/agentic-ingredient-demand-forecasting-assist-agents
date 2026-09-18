# Implementation report — ACRI-38/39/40/41 (US-003..006) + ACRI-42/43/44 (US-007..009) + ACRI-64 (US-029)

Minimal pipeline per explicit human direction ("make it fast"): planning,
implementation, and testing performed in one dispatch by the developer
agent. No separate planning/tech-lead/code-review artifacts exist for this
batch. Requirements source: Jira stories ACRI-38..44, ACRI-64
(DEC-004/DEC-005 — no PRD/HLD/LLD gate for this track).

- Repository: `c:\Users\aakash.ck\Downloads\agentic-ingredient-demand-forecasting-assist-agents`
- Branch: `devagent` (no branch created/switched, no commit/push — per instructions)
- Work items: ACRI-38 (US-003), ACRI-39 (US-004), ACRI-40 (US-005), ACRI-41 (US-006), ACRI-42 (US-007), ACRI-43 (US-008), ACRI-44 (US-009), ACRI-64 (US-029)
- Implementation round: 1

## Files changed

| File | Why |
|---|---|
| `app/backend/db/models.py` (edit) | Added `RiskConfig` (singleton row holding the ACRI-44 materiality threshold) and updated the module docstring's table inventory. |
| `app/backend/schemas/risk.py` (new) | Pydantic response/request schemas mirroring the service dataclasses/ORM row 1:1 (`RiskConfigOut`, `RiskConfigUpdate`, `StockoutRiskOut`, `SpoilageRiskOut`, `IngredientRiskOut`). |
| `app/backend/services/risk_config_service.py` (new) | Lazily-created singleton `RiskConfig` row, `get_materiality_threshold` (read live on every call), `get_risk_config`/`update_risk_config` for the HTTP contract. |
| `app/backend/services/stockout_risk_service.py` (new) | `evaluate_stockout_risk` — ACRI-38/39/40/41 pure maths, built on `demand_projection_service.project_ingredient_demand_series`, `CurrentStock`, `Supplier.lead_time_days`, and `ingredient_service.resolve_safety_margin` (reused verbatim). |
| `app/backend/services/spoilage_risk_service.py` (new) | `evaluate_spoilage_risk` — ACRI-42/43/44/64 pure maths, built on the same demand series plus `CurrentStock.use_by_date`, `Ingredient.unit_cost`, and the live materiality threshold. |
| `app/backend/routes/risk.py` (new) | `GET /ingredients/{id}/risk`, `GET /risk-config`, `PUT /risk-config`, all gated by `middleware.auth.get_current_user` (reused verbatim). Kept separate from `routes/ingredients.py`/`routes/current_stock.py` so those approved files stay untouched. |
| `app/backend/main.py` (edit) | Registered `ingredient_risk_router`/`risk_config_router`; updated the module docstring's route inventory. |
| `app/backend/tests/test_stockout_risk_service.py` (new) | Pure unit tests for `stockout_risk_service` (ORM rows constructed directly, explicit `anchor` for determinism). |
| `app/backend/tests/test_spoilage_risk_service.py` (new) | Pure unit tests for `spoilage_risk_service`. |
| `app/backend/tests/test_risk_config_service.py` (new) | Pure unit tests for the singleton threshold row. |
| `app/backend/tests/test_risk_api.py` (new) | HTTP-level tests for the 3 new routes (auth, 404, end-to-end evaluation, materiality threshold live-update). |
| `app/frontend/src/lib/risk-api.ts` (new) | Typed `getIngredientRisk` on the shared `apiClient` (no direct `fetch`). |
| `app/frontend/src/components/ingredient-detail/severity-badge.tsx` (new) | Shared severity badge — color + exact text, both always shown. |
| `app/frontend/src/components/ingredient-detail/stockout-risk-block.tsx` (new) | Stockout detail block (date/order-by/qty/severity/gap flags). |
| `app/frontend/src/components/ingredient-detail/spoilage-risk-block.tsx` (new) | Spoilage detail block (use-by date/waste cost/severity/suppressed note). |
| `app/frontend/src/components/ingredient-detail/ingredient-picker.tsx` (new) | Plain `<select>` ingredient picker (no dashboard navigation exists yet). |
| `app/frontend/src/routes/ingredient-detail.tsx` (rewrite) | Replaced the `StubScreen` usage with the real screen: fetch ingredient list, pick one, fetch its risk, render stockout/spoilage blocks per the stacking rule. |
| `app/frontend/src/routes/ingredient-detail.test.tsx` (new) | Vitest coverage: loading/error, stockout-only, spoilage-only, both-stacked, neither-flagged, gap-flag text, severity badge text. |
| `app/frontend/src/styles.css` (edit) | Added `--color-low`/`-bg`/`-border` tokens and `.badge--critical`/`.badge--high`/`.badge--low` (same structure as the existing `.badge--warning`, no redesign). |

No dependencies added. No existing public contract (route, schema field, or component prop) changed — all additions. `routes/ingredients.py`, `routes/current_stock.py`, `lib/screens.ts`, and `components/common/stub-screen.tsx` were read but **not** modified (the SCREENS array still lists `ingredient-detail` for the top-nav label; only `routes/ingredient-detail.tsx` stopped using `StubScreen`, per the instructions — the other 3 stub screens are untouched).

## Formulas and boundary semantics — exact definitions

### Stockout risk (ACRI-38/39/40/41)

- **Stockout flag (ACRI-38):** cumulative-sum the demand series' daily
  `total` over `demand_projection_service.DEFAULT_FORWARD_HORIZON_DAYS`
  (14) days; the **first day `cumulative >= stock_on_hand`** is the
  stockout date. If the running sum never reaches `stock_on_hand` within
  that horizon, `evaluate_stockout_risk` returns `None` (not at risk). A
  missing `CurrentStock` snapshot is also `None` — never fabricated as a
  `0` stock-on-hand (that gap belongs to ACRI-62).
- **Order-by date (ACRI-39):** `order_by_date = stockout_date -
  lead_time_days - safety_margin_days`. `safety_margin_days` comes from
  `resolve_safety_margin` (ingredient override → supplier default → gap),
  reused verbatim, unmodified. A gap (`None`) is **always** surfaced as
  `safety_margin_gap: true` on the result/trace — never silently treated
  as present — but the date subtraction itself needs a concrete number, so
  a gap contributes `0` days to that arithmetic (documented, not hidden).
  The same treatment applies to a missing supplier (`lead_time_days` is
  `None`): `lead_time_gap: true`, contributes `0` days.
- **Suggested order quantity (ACRI-40):** sum of the demand series' daily
  `total` over the **first `lead_time_days` days** of the series (the
  consumption expected while a freshly placed order is in transit). `0.0`
  when `lead_time_days` is a gap.
- **Severity (ACRI-41):** banded off `days_away = (order_by_date -
  today).days`: `Critical` when `days_away <= 2` (an already-passed /
  negative order-by date is also `Critical` — no separate "overdue"
  state), `High` when `3 <= days_away <= 7`, `Low` when `days_away > 7`.
  Boundary-tested at -5, 0, 2 (Critical), 3, 7 (High), 8, 100 (Low).

### Spoilage risk (ACRI-42/43/44/64)

- **Spoilage flag (ACRI-42):** a non-`perishable` ingredient is **never**
  flagged (`evaluate_spoilage_risk` returns `None` immediately, before
  looking at stock at all). A `perishable` ingredient with no recorded
  `CurrentStock`/`use_by_date` also returns `None` (data gap owned by
  ACRI-62). Otherwise: sum the demand series' daily `total` for every day
  on or before `use_by_date`; flagged when that cumulative demand is
  **strictly less than** `stock_on_hand` (exactly equal → not flagged, no
  waste). If `use_by_date` is today or already in the past, there are zero
  forward days to sum, so cumulative demand is `0.0` (the entire current
  stock is treated as unconsumed) — a documented assumption, not fabricated
  data, since there is no AC covering this edge explicitly.
- **Waste cost (ACRI-43):** `waste_cost_inr = unconsumed_quantity *
  unit_cost`, where `unconsumed_quantity = max(stock_on_hand -
  cumulative_demand, 0.0)` (floored at 0, never negative).
- **Materiality threshold (ACRI-44):** `suppressed = waste_cost_inr <
  materiality_threshold_inr`, read live from `risk_config_service` on every
  evaluation (never cached), so a `PUT /risk-config` change applies to the
  very next call — no redeploy. `suppressed` is returned **alongside** the
  raw `waste_cost_inr`; a caller building a visible list can filter on
  `suppressed`, a caller summing an aggregate total never has to (never
  silently short-changed). Exactly-at-threshold is **not** "below" it →
  not suppressed (boundary-tested at threshold=50/cost=50 → not
  suppressed). A single `RiskConfig` row is lazily created on first read,
  seeded with `DEFAULT_MATERIALITY_THRESHOLD_INR = 500.0`.
- **Severity (ACRI-64):** banded off `waste_cost_inr`: `Critical` when
  `>= 2000`, `High` when `500 <= waste_cost_inr < 2000`, `Low` when
  `< 500`. Boundary-tested at 2000 (Critical), 1999.99/500 (High),
  499.99/0 (Low).

## Acceptance criteria implemented

**ACRI-38 (US-003):** not flagged when consumption never exceeds stock in
the horizon (`test_not_flagged_when_consumption_never_exceeds_stock_in_horizon_ac_acri_38`,
`test_neither_flagged_when_no_stock_recorded_at_all`); deterministic
(explicit `anchor`, no wall-clock read inside the maths); traces to
stock-on-hand + the full per-day cumulative demand
(`test_flagged_result_traces_to_stock_on_hand_and_demand_series_ac5`);
boundary at exact equality
(`test_stockout_boundary_is_first_day_cumulative_demand_meets_or_exceeds_stock`,
`test_stockout_one_unit_above_boundary_pushes_to_the_next_day`).

**ACRI-39 (US-004):** order-by date formula; ingredient override wins over
supplier default (`test_order_by_date_prefers_ingredient_override_over_supplier_default_ac_acri_39`);
supplier default used when no override
(`test_order_by_date_falls_back_to_supplier_default_safety_margin`); a
safety-margin gap is visibly flagged, never silently zeroed
(`test_safety_margin_gap_is_visibly_flagged_and_never_silently_treated_as_present`);
a missing supplier flags `lead_time_gap` too
(`test_missing_supplier_flags_lead_time_gap_and_contributes_zero_days`).

**ACRI-40 (US-005):** suggested order quantity = sum over the lead-time
window (`test_suggested_order_quantity_sums_the_lead_time_day_window_ac_acri_40`),
`0.0` when the lead time is a gap (covered in the missing-supplier test
above).

**ACRI-41 (US-006):** severity boundaries at ≤2/3-7/>7 days away, including
negative days-away as Critical
(`test_severity_band_boundaries_ac_acri_41`, parametrized -5/0/2/3/7/8/100).

**ACRI-42 (US-007):** non-perishable ingredients never flagged
(`test_non_perishable_ingredient_is_never_flagged_ac_acri_42`); data gaps
(no stock/no use-by date) return `None`
(`test_no_current_stock_snapshot_is_not_fabricated`,
`test_no_use_by_date_recorded_cannot_be_evaluated`); exact-equality boundary
not flagged (`test_not_flagged_when_cumulative_demand_exactly_meets_stock_boundary_ac_acri_42`);
flagged when strictly below
(`test_flagged_when_cumulative_demand_is_strictly_below_stock_ac_acri_42`);
past/today use-by date treated as zero cumulative demand
(`test_use_by_date_today_or_in_the_past_treats_cumulative_demand_as_zero`,
parametrized 0/2 days before anchor).

**ACRI-43 (US-008):** waste cost formula and the zero-floor
(`test_flagged_when_cumulative_demand_is_strictly_below_stock_ac_acri_42`,
`test_waste_cost_floors_unconsumed_quantity_at_zero_never_negative`).

**ACRI-44 (US-009):** threshold suppresses below but not at the boundary
(`test_materiality_threshold_suppresses_below_but_not_at_the_boundary_ac_acri_44`);
a `PUT /risk-config` change applies immediately and never alters the raw
cost (`test_materiality_threshold_change_applies_immediately_and_never_alters_raw_cost`);
singleton row behavior + default
(`test_default_threshold_is_500_when_unset`,
`test_reading_the_config_lazily_creates_exactly_one_row`,
`test_update_takes_effect_immediately_for_the_next_read`); no UI control
built (deferred to the Dashboard track, per instructions) — backend +
tests only.

**ACRI-64 (US-029):** severity boundaries at 500/2000
(`test_severity_band_boundaries_ac_acri_64`, parametrized 2000/1999.99/
500/499.99/0).

**Frontend — Ingredient Detail screen:** ingredient picker + fetch,
stockout block (date/order-by/qty/severity + safety-margin-gap/lead-time-gap
flags), spoilage block (use-by date/waste cost/severity/suppressed note),
both stacked when both are flagged, plain "no risk" message when neither is
— all covered in `ingredient-detail.test.tsx` (7 tests: loading, list-fetch
error, stockout-only + gap flag, spoilage-only + suppressed note,
both-stacked, neither-flagged). Severity is always shown as both a colored
badge and the exact text ("Critical"/"High"/"Low"), asserted via
`screen.getByText("Critical"/"High"/"Low")` in every scenario.

## Tests added

Backend (pytest, all new):
- `tests/test_stockout_risk_service.py` — 15 tests (pure, direct ORM setup, explicit `anchor`).
- `tests/test_spoilage_risk_service.py` — 15 tests (same convention).
- `tests/test_risk_config_service.py` — 3 tests.
- `tests/test_risk_api.py` — 13 tests (HTTP-level: auth, 404, end-to-end stockout, end-to-end spoilage, neither-flagged, risk-config GET/PUT/validation).

Frontend (Vitest, all new):
- `src/routes/ingredient-detail.test.tsx` — 7 tests.

## Commands executed (all run for real, in this repository)

Backend (`app/backend`, venv at `.venv`):
- `python -m pytest tests/test_stockout_risk_service.py tests/test_spoilage_risk_service.py tests/test_risk_config_service.py tests/test_risk_api.py -q` → **46 passed** (first pass, before final lint fixes).
- `python -m pytest -q` (full suite, after lint fixes) → **190 passed, 6 warnings** in 193.43s. The 6 warnings are all pre-existing `StarletteDeprecationWarning`s in unrelated, pre-existing test files (`HTTP_422_UNPROCESSABLE_ENTITY` deprecation) — not introduced by this batch.
- `python -m ruff check .` → initially 11 errors (import order + line length in the 3 new test files) → fixed → **All checks passed!**
- `python -m black --check .` → **All done, 63 files would be left unchanged.**
- `python -m mypy .` → **Success: no issues found in 63 source files.**

Frontend (`app/frontend`):
- `npm run test -- --run` → **23 test files, 114 tests passed** (all pre-existing tests still green plus the 7 new ones).
- `npm run typecheck` (`tsc --noEmit`) → clean, no output.
- `npm run lint` (`eslint .`) → **0 errors**, 1 pre-existing warning in `src/lib/auth-context.tsx` (react-refresh, unrelated to this change).
- `npm run format:check` (`prettier --check .`) → initially flagged the 2 new files → fixed via `prettier --write` on those 2 files → **All matched files use Prettier code style!**
- `npm run build` (`tsc -b && vite build`) → succeeded, `dist/` produced (`index.html`, `index-*.css` 6.70 kB, `index-*.js` 218.71 kB).

## Migrations / configuration / operational notes

- No migration tool exists in this codebase (`Base.metadata.create_all` at
  startup, per the existing convention) — the new `risk_config` table is
  created the same way, and the single row is lazily created on first read
  (no seed step required).
- No new environment variables or dependencies.
- `GET/PUT /risk-config` requires authentication (`get_current_user`), same
  as every other route; no persona-based branching, matching the rest of
  this codebase.

## Deviations / adjacent files

- **`app/backend/db/models.py`** — edited to add the `RiskConfig` table.
  Not explicitly named in scope, but necessary (ACRI-44 explicitly requires
  "a tiny `RiskConfig` table/singleton row"). No existing model changed.
- No other adjacent/unplanned files were touched. `routes/ingredients.py`
  and `routes/current_stock.py` were deliberately **not** edited — the new
  `/ingredients/{id}/risk` route lives in a new `routes/risk.py` instead,
  to avoid touching those approved files.

## Unresolved concerns / known QA considerations

1. **Missing-stock/missing-use-by-date/missing-supplier data gaps are
   treated as "not evaluable" (`None`), not "at risk."** This is a
   reasonable, non-fabricating default given `CurrentStock`'s own
   `has_stock_recorded` distinction (ACRI-62), but no ACRI-38..44/64 AC
   explicitly states this — flag for product/QA confirmation.
2. **`use_by_date` today-or-in-the-past → cumulative demand treated as
   `0.0`** (entire stock unconsumed). Reasonable and documented, but not
   explicitly specified by any AC — flag for product/QA confirmation.
3. **Suggested order quantity window (ACRI-40)** is defined as "the first
   `lead_time_days` days of the series" (i.e. demand expected while a
   freshly placed order is in transit), independent of the stockout/
   order-by dates, per the story's own trace wording ("Trace to lead time
   and demand projection" only). An alternative reading (a window anchored
   at the order-by or stockout date) was considered and rejected as less
   consistent with the story's stated trace scope — flag for product/QA
   confirmation if a different anchor was intended.
4. **Frontend `ingredient-detail.test.tsx`** emits benign
   `act(...)`-wrapping console warnings from React Testing Library on the
   async state updates that follow `fireEvent.change` (all 7 tests still
   pass deterministically); this is cosmetic test-console noise, not a
   functional defect, consistent with this component's fetch-driven async
   pattern.
5. Per the story text, **no UI control for the materiality threshold**
   was built (ACRI-44 explicitly defers this to the Dashboard track) —
   only the backend `GET/PUT /risk-config` endpoint and its tests exist.
