# Implementation report — ACRI-36 (US-001) + ACRI-37 (US-002)

Minimal pipeline per explicit human direction ("make it fast"): planning,
implementation, and testing performed in one dispatch by the developer
agent. No separate planning/tech-lead/code-review artifacts exist for this
batch. Requirements source: Jira stories ACRI-36/ACRI-37 (DEC-004/DEC-005 —
no PRD/HLD/LLD gate for this track).

- Repository: `c:\Users\aakash.ck\Downloads\agentic-ingredient-demand-forecasting-assist-agents`
- Branch: `devagent` (no branch created/switched; worked on the supplied branch, no commit/push per instructions)
- Work items: ACRI-36 (US-001, "Ingredient demand is projected over a forward horizon with day-of-week and trend awareness"), ACRI-37 (US-002, "Ingredient-level demand is aggregated from every dish that uses it")
- Implementation round: 1

## Files changed

| File | Why |
|---|---|
| `app/backend/services/demand_projection_service.py` (new) | Core pure-function projection/aggregation logic: `project_dish_demand`, `_project_dish_demand_with_trace`, `project_ingredient_demand`, `project_ingredient_demand_series`, and their dataclass return shapes (`WeekdayDataPoint`, `DishProjectionTrace`, `DishProjectionResult`, `ContributingDish`, `IngredientDemandProjection`, `IngredientDemandSeriesDay`, `IngredientDemandSeries`). |
| `app/backend/schemas/demand_projection.py` (new) | Pydantic response schemas for the debug/introspection endpoint, mirroring the service dataclasses 1:1 via `from_attributes=True` (`WeekdayDataPointOut`, `DishProjectionTraceOut`, `ContributingDishOut`, `IngredientDemandSeriesDayOut`, `IngredientDemandSeriesOut`). |
| `app/backend/routes/demand_projection.py` (new) | `GET /demand-projection/{ingredient_id}?days=14`, gated by `middleware.auth.get_current_user` (same pattern as every other data-setup route). |
| `app/backend/main.py` (edit) | Registered `demand_projection_router`; updated the module docstring's route inventory. |
| `app/backend/tests/test_demand_projection_service.py` (new) | Pure unit tests against the service functions, constructing DB rows directly via the ORM models (no HTTP layer) — mirrors the `test_safety_margin_gap_logic.py` convention. |
| `app/backend/tests/test_demand_projection_api.py` (new) | HTTP-level tests for the new route via the `client`/`db_session` fixtures, following the `_login`/`_create_dish`/`_create_ingredient` conventions in `test_sales_history_api.py`/`test_menu_recipe_api.py`. |

No other files were touched. No dependencies added, no public contract of an existing route/schema changed.

## Recency-weighting formula (US-001 AC2) — exact definition

Within one dish's `SalesHistoryRecord` rows that fall on the target date's
weekday (sorted oldest → newest), the *i*-th data point (1-indexed, i=1 is
the oldest match, i=n is the most recent) is given a **linear** weight of
`i`. The projection is the weight-normalized average:

```
weighted_average = sum(weight_i * units_sold_i) / sum(weight_i)
                  = sum(i * units_sold_i for i in 1..n) / sum(1..n)
```

Example: two prior Saturdays, older=10 units, newer=20 units → weights 1
and 2 → `(1*10 + 2*20) / (1+2) = 50/3 ≈ 16.67`, vs. a flat average of 15 —
the newer week is weighted more heavily, satisfying AC2. This weighting
depends only on the historical rows' relative order (never on
`date.today()`/wall-clock time), so it is deterministic (AC4).

## Acceptance criteria implemented

**ACRI-36 / US-001**
- AC1 (own weekday history, not flat average): `_weekday_history` filters a dish's `SalesHistoryRecord` rows to exactly the target date's Python weekday (Monday=0..Sunday=6) before any averaging. Covered by `test_projection_for_a_saturday_uses_only_saturday_history_not_flat_average_ac1`.
- AC2 (recency weighting): linear weights per the formula above. Covered by `test_recency_weighting_differs_from_a_flat_weekday_average_ac2`.
- AC3 (>=14-day forward horizon): `DEFAULT_FORWARD_HORIZON_DAYS = 14`; `project_ingredient_demand_series` accepts any `horizon_days >= 1`. Covered by `test_forward_horizon_series_covers_at_least_14_days_ac3` (service) and `test_default_horizon_is_at_least_14_days_ac3` / `test_custom_days_query_param_controls_the_series_length` (API).
- AC4 (determinism): pure arithmetic over already-persisted rows, no randomness, no wall-clock read inside `project_dish_demand`/`project_ingredient_demand`. Covered by `test_same_inputs_run_twice_produce_identical_output_ac4` and `test_ingredient_demand_result_is_deterministic_ac2`.
- AC5 (explicit arithmetic trace): `DishProjectionTrace` carries every matched data point (`sale_date`, `units_sold`, `weight`) plus the resulting `weighted_average`, returned on every `ContributingDish`. Covered by `test_trace_reconstructs_the_arithmetic_back_to_sales_history_ac5` and the API end-to-end test's trace assertions.
- Zero-history-for-weekday returns `0.0`, not an error, with `gap=True` on the trace (never silently hidden). Covered by `test_zero_history_for_target_weekday_returns_zero_not_an_error_ac1` and `test_zero_history_trace_flags_the_gap_instead_of_hiding_it`.

**ACRI-37 / US-002**
- AC1 (aggregation = sum of dish demand × quantity_per_serving): `project_ingredient_demand` sums `project_dish_demand(dish, date) * line.quantity_per_serving` over every `RecipeLine` whose `ingredient_id` matches. Only rows with a resolved (non-`NULL`) `ingredient_id` can ever match this equality filter. Covered by `test_ingredient_demand_aggregates_across_three_contributing_dishes_ac1` (3 contributing dishes) and `test_ingredient_demand_excludes_unresolved_recipe_lines`.
- AC2 (determinism): Covered by `test_ingredient_demand_result_is_deterministic_ac2`.
- AC3 (per-dish traceability): `contributing_dishes` returns every dish's `projected_dish_demand`, `quantity_per_serving`, `contribution`, and trace — never just the total. Covered by `test_ingredient_demand_is_traceable_to_each_contributing_dishes_amount_ac3` and the API end-to-end test.

**Forward-looking design (for Stockout/Spoilage, not yet consumed):**
`project_ingredient_demand_series(ingredient_id, horizon_days, db, start_date=None)` returns one `IngredientDemandSeriesDay` (`date`, `total`, `contributing_dishes`) per day from `start_date + 1` to `start_date + horizon_days`, defaulting `start_date` to `date.today()` at the call boundary (the per-day maths itself never reads the clock). This is exactly the shape described in the story ("does projected consumption exceed stock within the forward horizon").

Ingredient-not-found raises `404` (`_get_ingredient_or_404`), consistent with the existing `ingredient_service.py`/`menu_recipe_service.py` pattern of the service layer raising `HTTPException` directly. `horizon_days < 1` raises `422`.

## New endpoint

`GET /demand-projection/{ingredient_id}?days=14` (default `days=14`, `ge=1`), behind `get_current_user` (401 if unauthenticated, 404 for an unknown ingredient). Returns `IngredientDemandSeriesOut`: `ingredient_id`, `ingredient_name`, `horizon_days`, and `series[]` (each day's `date`, `total`, and `contributing_dishes[]` with `dish_id`, `dish_name`, `projected_dish_demand`, `quantity_per_serving`, `unit`, `contribution`, and the full `trace` object). Registered in `main.py` alongside the other data-setup routers.

## Tests added

- `app/backend/tests/test_demand_projection_service.py` — 13 tests: day-of-week grouping (AC1), recency weighting vs. flat average (AC2), determinism (AC4), zero-history gap (AC1), arithmetic trace reconstruction (AC5), forward-horizon length (AC3), invalid horizon (422), 3-dish aggregation math (US-002 AC1), aggregation determinism (US-002 AC2), per-dish traceability (US-002 AC3), exclusion of unresolved recipe lines, unknown-ingredient 404.
- `app/backend/tests/test_demand_projection_api.py` — 5 tests: 401 when unauthenticated, 404 for unknown ingredient, default 14-day horizon, custom `days` query param, and a full end-to-end test (dish + ingredient + recipe line + 14 days of sales history created entirely through the public HTTP API) asserting the response's per-dish breakdown and trace match the expected arithmetic. Seeded with a constant `units_sold` across 14 consecutive real-clock days so the assertions are correct regardless of which weekday the suite happens to run on (avoids date-flakiness while still exercising the real `date.today()` code path).

## Migrations / configuration / operational notes

- No schema changes — reuses the existing `Dish`, `RecipeLine`, `SalesHistoryRecord`, `Ingredient` tables from the already-built Menu & Recipe / Sales History stories.
- No new dependencies.
- No environment/config changes.
- Nothing else currently consumes this service over HTTP; the new route exists solely so the maths is independently testable/inspectable ahead of the Stockout/Spoilage track, per the dispatch instructions.

## Commands executed (this session)

1. `pytest tests/test_demand_projection_service.py tests/test_demand_projection_api.py -v` → **18 passed**, 3 warnings (pre-existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation pattern, same as other modules).
2. `pytest` (full suite) → **144 passed**, 6 warnings, 217.50s. No pre-existing test broken.
3. `ruff check .` → **All checks passed!**
4. `black --check .` → initially flagged 1 file (`services/demand_projection_service.py`, an over-wrapped line); ran `black services/demand_projection_service.py` to auto-format, then `black --check .` → **All done! 54 files would be left unchanged.**
5. `mypy .` → **Success: no issues found in 54 source files.**
6. Re-ran `pytest tests/test_demand_projection_service.py tests/test_demand_projection_api.py -q` after the black reformat → **18 passed** (confirms formatting-only change didn't regress behavior).

All commands were run from `app/backend` using the project's own `.venv` interpreter (`./.venv/Scripts/python.exe -m <tool>`).

## Deviations / adjacent files

- `app/backend/main.py` was edited (router registration + docstring) — required to expose the new route per the dispatch instructions ("Register the router in main.py"); this is explicitly in scope, not an adjacent-file deviation.
- No other files outside the planned scope were touched. No commit, push, or branch operation was performed.

## Unresolved concerns / known QA considerations

- The debug endpoint's `days` query param currently has no upper bound (`ge=1` only) — fine for an introspection endpoint at this stage, but the Stockout/Spoilage consumer may want a sane cap; left open since the story didn't specify one.
- `project_ingredient_demand_series`'s `start_date` defaults to `date.today()` when the HTTP route calls it (the route itself has no `start_date` override) — this is intentional per the story (a real forward-looking horizon), but means the API test suite seeds 14 days of *real* trailing calendar history relative to whenever the suite runs; this was deliberately designed to be weekday-agnostic (constant `units_sold` across a full 2-week window) so it isn't flaky, but a reviewer should confirm that reasoning holds.
- If a dish has more than one `RecipeLine` resolving to the same ingredient (schema allows it, unusual in practice), `project_ingredient_demand` will recompute that dish's projection once per matching line and sum both contributions — correct per AC1's per-recipe-line semantics, but not explicitly tested since the story didn't call out that edge case.
- Recipe lines with `ingredient_id IS NULL` (never resolved) are correctly excluded from any ingredient's aggregation (tested), since they can never equal a concrete `ingredient_id` in the SQL filter.
