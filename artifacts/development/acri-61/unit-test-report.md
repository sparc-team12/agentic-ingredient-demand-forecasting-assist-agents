# Unit Test Report — ACRI-61 (Ingredients & Suppliers Setup)

**Work item:** ACRI-61
**Plan checksum:** sha256:cde7761056f7b1c74b0bbfe1b9f7bfb0e6008ac983461b09d823510d0e234276 (matches `implementation.md` and `tech-lead-review.json`, status `PASS`)
**Preconditions verified:** `implementation.md` status `COMPLETED`; `tech-lead-review.json` status `PASS` (MINOR finding on PUT full-replace semantics — confirmed resolved in code, see below).

## Scope of this pass

Test-code and fixture changes only. No production file under `app/backend` or `app/frontend/src` (excluding `*.test.ts(x)`) was modified. One backend test added; all other Development-owned scenarios were found already covered by real, meaningful assertions (not tautological/over-mocked) after independent inspection of the production code in `app/backend/{db/models.py,schemas/ingredients.py,services/ingredient_service.py,routes/ingredients.py}` and `app/frontend/src/{lib/ingredients-api.ts,routes/ingredients-suppliers-setup.tsx,components/ingredients-suppliers/*}`.

## Coverage matrix (implementation-plan.md §9 test scenarios, AC1–AC5)

| ID | AC/concern | Expected result | Status | Test(s) |
|---|---|---|---|---|
| TS-BE-01 | AC1 | POST/GET round-trips unit/unit_cost/perishable/shelf_life_days | Covered | `test_create_and_list_ingredient_round_trips_ac1_fields` |
| TS-BE-02 | AC1 | Perishable + null shelf_life_days → 422 | Covered | `test_perishable_ingredient_with_null_shelf_life_returns_422` |
| TS-BE-03 | AC2 | Supplier round-trip; nested supplier summary on ingredient | Covered | `test_create_and_list_suppliers_round_trips_name_and_lead_time`, `test_ingredient_created_with_valid_supplier_id_shows_nested_supplier_summary_ac2` |
| TS-BE-04 | AC3 | `supplier_id: null` → `has_supplier: false` | Covered | `test_ingredient_created_with_no_supplier_is_flagged_ac3` |
| TS-BE-05 | AC4 | Override + supplier value both set → override wins, source "ingredient" | Covered | `test_ingredient_override_takes_precedence_over_supplier_default_ac4` |
| TS-BE-06 | AC4/AC5 | Supplier fallback when no override; gap (never 0) when neither set | Covered | `test_ingredient_falls_back_to_supplier_default_when_no_override_ac4`, `test_ingredient_with_no_override_and_no_mapped_supplier_value_is_gap_never_zero_ac5`, `test_ingredient_with_no_supplier_and_no_override_is_gap_never_zero_ac5` |
| TS-BE-07 | AC4/AC5 (pure fn) | All 4 override×supplier combinations, incl. explicit-zero not conflated with missing | Covered | `test_safety_margin_gap_logic.py` (6 tests, incl. the two explicit-zero cases) |
| TS-BE-08 | Validation | Nonexistent `supplier_id` on create → 422; duplicate name → 409; unknown id on PUT → 404 | Covered (gap closed this pass) | Create: `test_create_ingredient_with_nonexistent_supplier_id_returns_422`, `test_create_supplier_with_duplicate_name_returns_409`, `test_create_ingredient_with_duplicate_name_returns_409`. Update: `test_update_ingredient_with_nonexistent_supplier_id_returns_422`, `test_update_unknown_supplier_returns_404`, `test_update_unknown_ingredient_returns_404`, `test_update_supplier_to_a_duplicate_name_returns_409`, and **new** `test_update_ingredient_to_a_duplicate_name_returns_409` |
| TS-BE-09 | Auth reuse | 401 with no session, 200 with valid session | Covered | `test_get_suppliers_requires_authentication`, `test_get_ingredients_requires_authentication` (+ all `_login`-gated tests exercising the 200 path) |
| TS-BE-10 | Fixture seed | Idempotent 2 suppliers/3 ingredients; unmapped + no-safety-margin rows present | Covered | `test_seed_demo_ingredients.py` (4 tests) |
| TS-FE-01 | AC1/AC2 | Loading → data render with expected columns | Covered | `ingredients-suppliers-setup.test.tsx` |
| TS-FE-02 | Empty state | Empty-state message per section | Covered | same file |
| TS-FE-03 | AC3 | Gap flag vs. supplier name per row | Covered | same file |
| TS-FE-04 | AC5 | Gap flag, never literal 0 | Covered | same file |
| TS-FE-05 | Validation | Perishable→shelf-life required; supplier `<select>` only lists real suppliers | Covered | `ingredient-form.test.tsx` |
| TS-FE-06 | Validation | Empty name / negative lead time blocked | Covered | `supplier-form.test.tsx` |
| TS-FE-07 | Error state | `ApiError` → visible error message | Covered | `ingredients-suppliers-setup.test.tsx` |
| TS-FE-08 | API layer | Method/path/body + `ApiError` propagation | Covered | `ingredients-api.test.ts` |
| TS-E2E-01/02/03 | e2e/manual/accessibility | Out of scope for this unit-test agent (QA-owned) | Not applicable here | — |

## Specifically requested checks

- **FK-existence validation for `supplier_id` on create AND update:** both paths call the same `_check_supplier_exists` and both were already tested (`test_create_ingredient_with_nonexistent_supplier_id_returns_422`, `test_update_ingredient_with_nonexistent_supplier_id_returns_422`). No gap.
- **Safety-margin precedence boundary cases (override=0 vs None, supplier default=0 vs None):** `test_safety_margin_gap_logic.py` explicitly covers `override=0` (`test_an_explicit_zero_override_is_respected_and_not_confused_with_missing`) and `supplier.safety_margin_days=0` (`test_an_explicit_zero_supplier_default_is_respected_and_not_confused_with_missing`), plus both-None (gap) and each set/unset combination. `resolve_safety_margin` itself uses `is not None` checks throughout (never a falsy/truthy check), so zero can't be conflated with unset. No gap.
- **Duplicate-name conflict, suppliers and ingredients, create and update:** suppliers had all four (create/update × duplicate); ingredients had create-duplicate but **no update-duplicate test**, despite `update_ingredient` having the identical `IntegrityError`→409 handling as `update_supplier`. This was a genuine test-code gap — closed by adding `test_update_ingredient_to_a_duplicate_name_returns_409`.
- **PUT full-replace semantics (tech-lead MINOR finding):** verified in code — `update_supplier`/`update_ingredient` unconditionally assign every field from the payload (no `if field is not None` merge logic), and Pydantic's `SupplierUpdate`/`IngredientUpdate` share the exact same required-field shape as `*Create` (an omitted optional field resolves to its schema default, i.e. `None`, not "keep existing"). Already backed by real, meaningful tests: `test_update_supplier_full_replace_clears_an_omitted_optional_field`, `test_update_ingredient_full_replace_unmaps_supplier_when_omitted`, `test_update_ingredient_full_replace_also_clears_safety_margin_override_when_omitted`, plus the frontend's `supplier-form.test.tsx`/`ingredient-form.test.tsx` "pre-fills every field from `initialValue`" tests confirming the client always resubmits the complete object. No gap; tech-lead's MINOR finding is fully resolved and tested.

## Test files changed

- `app/backend/tests/test_ingredients_api.py` — added `test_update_ingredient_to_a_duplicate_name_returns_409` (closes the one identified gap). No other file touched.

## Commands run (from a fresh shell) and results

```
# Targeted new test
cd app/backend
.venv/Scripts/python.exe -m pytest -q tests/test_ingredients_api.py -k duplicate
→ 2 passed, 16 deselected  (exit 0)

# Full backend suite
.venv/Scripts/python.exe -m pytest -q
→ 91 passed, 4 warnings (StarletteDeprecationWarning, pre-existing/unrelated)  (exit 0)
  (90 pre-existing + 1 new; 0 failed, 0 skipped)

# Full frontend suite
cd app
npm run test --workspace frontend -- --run
→ Test Files: 9 passed (9); Tests: 44 passed (44)  (exit 0)
  0 failed, 0 skipped
```

No coverage command/threshold is configured in this repo (`pyproject.toml` has no `--cov` in `[tool.pytest.ini_options]`; `package.json`'s `test` script runs plain `vitest run`) — none was invented or run.

## Findings on the test diff itself

- No arbitrary sleeps, no order dependence, no shared mutable state (each backend test gets its own isolated temp-SQLite DB via `conftest.py`'s per-test `test_engine`/`db_session_factory`/`client` fixtures; each frontend test mocks `apiClient` fresh per test).
- No snapshot tests; all frontend assertions use `getByRole`/`getByLabelText`/text queries per the repo's own convention (confirmed by the disclosed visual-design pass note in `implementation.md`, and independently verified by reading the test files above).
- No over-mocking: backend tests hit the real FastAPI app + real SQLAlchemy models through `TestClient`; frontend tests mock only the `apiClient` boundary, not the components under test.
- No secrets in fixtures (`conftest.py`'s test credentials are clearly test-only strings, consistent with existing ACRI-66 convention already in the repo).
- The one test added follows the exact existing naming/structure convention of its neighboring `test_update_supplier_to_a_duplicate_name_returns_409`.

## Production defects found

None. No genuine production defect was identified during this pass; the FK-check, precedence-function, duplicate-handling, and full-replace behaviors all matched their tests and their documented intent.

## Status: PASS

All ACRI-61 Development-owned test scenarios (TS-BE-01…10, TS-FE-01…08) are mapped to real, substantive tests; the one identified gap (ingredient-update duplicate-name conflict) was closed with a new test; the full backend (`pytest`, 91 passed) and frontend (`npm run test --workspace frontend -- --run`, 44 passed) suites both pass with exit code 0 from a fresh shell.
