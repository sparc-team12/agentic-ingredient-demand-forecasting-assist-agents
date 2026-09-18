# Unit Test Report — ACRI-66 (Per-user login / auth gate)

## 1. Preconditions checked

- `artifacts/development/acri-66/implementation.md` — status `COMPLETED`, read in full.
- `artifacts/development/acri-66/implementation-plan.md` — matching plan (checksum `sha256:e921a607cdfbe1da39afdc31461913c682fb5d4336a4357a9c387ca3b1959fe8`, as recorded in `tech-lead-review.json` and cited by `implementation.md`), read in full, including §9 Test scenarios (TS-01–TS-16) and §2 AC traceability table.
- Independently inspected production code under `app/backend` (`db/models.py`, `db/seed.py`, `services/auth_service.py`, `middleware/auth.py`, `routes/auth.py`, `routes/screens.py`, `schemas/auth.py`, `main.py`) and `app/frontend/src` (`lib/api-client.ts`, `lib/auth-context.tsx`, `components/common/stub-screen.tsx`) against the actual test files, rather than trusting `implementation.md`'s summary alone.

## 2. Scenario / acceptance-criterion coverage matrix

| ID | AC / concern | Owner | Existing test (pre-change) | Gap found | Action taken |
|---|---|---|---|---|---|
| TS-01 | AC1 — 401 with no session, all 4 screens | Dev | `test_auth_session_required.py::test_each_screen_returns_401_with_no_session_cookie` (parametrized) | None | none needed |
| — | AC1 — tampered/garbage cookie on screens | Dev | `test_auth_session_required.py::test_each_screen_returns_401_with_a_garbage_cookie` | None | none needed |
| TS-02 | AC1 — `RequireAuth` redirects when unauthenticated | Dev | `require-auth.test.tsx` (loading / redirect / renders-children) | None | none needed |
| TS-03/TS-04 | AC2 — valid login (both personas) → cookie + 200 on stub | Dev | `test_auth_login.py`, `test_auth_session_required.py` (200 cases) | None | none needed |
| TS-05 | AC2 — `LoginForm` calls `login()` on success | Dev | `login-form.test.tsx` | None | none needed |
| TS-06 | AC3 — wrong password / unknown email → generic 401, no cookie/session | Dev | `test_auth_login.py` | None | none needed |
| TS-07 | AC3 — `LoginForm` inline error, no navigation | Dev | `login-form.test.tsx` | None | none needed |
| TS-08 | AC4 — cross-credential login rejected | Dev | `test_auth_login.py` (both directions) | None | none needed |
| TS-09 | AC4/seeding — 2 distinct accounts, idempotent re-run | Dev | `test_seed_demo_accounts.py` | **Partial**: only all-or-nothing re-run tested, not a partial-state re-run (one account already present, one missing) | **Added** `test_seeding_when_only_one_demo_account_already_exists_creates_only_the_missing_one` |
| TS-10 | AC5 — identical response shape, both personas, all 4 screens | Dev | `test_auth_session_required.py::test_both_personas_get_a_byte_identical_response_shape` | None | none needed |
| TS-11 | Failed-login alerting — 4 vs 5 attempts | Dev | `test_failed_login_alerting.py` (4→none, 5→exactly one) | **Gap**: no test for (a) window-expiry (stale attempts outside 15-min window not counted, and not suppressing a fresh breach either), (b) behavior at the 6th attempt (boundary above threshold) | **Added** 3 tests: window-expiry (stale-only), window-expiry (stale + fresh-5), 6th-attempt boundary |
| TS-12 | Logout invalidates session | Dev | `test_auth_logout.py` | None | none needed |
| — | `GET /auth/me` (session bootstrap; in plan §6 contract table but no owning TS-ID and **zero prior tests**) | Dev | *(none existed)* | **Gap**: completely untested — 401/200/tampered-cookie/post-logout cases, despite being the endpoint `AuthProvider` calls on every page load | **Added** new file `test_auth_me.py` (5 tests) |
| — | Case-sensitivity / whitespace in email lookup | Dev (implicit, per `verify_credentials`'s normalization) | *(none existed)* | **Gap**: `verify_credentials`/`record_login_attempt` normalize email (`.strip().lower()`) but no test exercised mixed-case or whitespace-padded input | **Added** 3 tests in `test_auth_login.py`: case-insensitive match, whitespace-tolerant match, and a negative control (normalized email + wrong password still 401) |
| — | Session-cookie tampering / invalid-token handling | Dev | `test_auth_session_required.py` (garbage cookie on screens), `test_auth_logout.py` (invalid cookie on logout) | Screens/logout covered; `/auth/me` was not (see above) | Closed via the new `test_auth_me.py` tampered-cookie case |
| — | Concurrent/idempotent seed-script re-runs | Dev | `test_seed_demo_accounts.py` (full re-run idempotency, no password overwrite) | Partial-state idempotency gap (see TS-09 row). True multi-process concurrency is not attempted here — SQLite's single-writer posture (per plan §6 "Idempotency/concurrency") makes a real concurrent-write test either no-op or inherently flaky/non-deterministic with arbitrary sleeps, which this agent's conventions rule out; sequential partial-state idempotency is the correct unit-test-level proxy | **Added** (see TS-09 row) |
| TS-13–TS-16 | Browser/manual (redirect+session persistence, UX parity, cookie devtools inspection, out-of-scope confirmation) | **QA**, not Development | N/A | N/A — explicitly QA-owned per the plan | Not in this agent's scope |

Frontend component-level coverage (`api-client.test.ts`, `require-auth.test.tsx`, `login-form.test.tsx`, `App.test.tsx`) was independently re-read against the plan's frontend contracts (§5 Execution/data flow, §6 contracts) and found to already map cleanly to TS-02/05/07 with no meaningless assertions, no over-mocking beyond what's appropriate (mocking `useAuth`/`apiClient` at the boundary, not internals), and no snapshot tests. No frontend test files were changed.

## 3. Test files changed

All changes are additive (new test cases / new test file); no production code was touched.

- `app/backend/tests/test_auth_me.py` — **new file**, 5 tests (401 no-cookie, 401 tampered/forged cookie, 200 kitchen-manager identity, 200 fb-manager identity, 401 after logout)
- `app/backend/tests/test_auth_login.py` — **+3 tests** (case-insensitive email match, whitespace-tolerant email match, normalized-email-but-wrong-password negative control)
- `app/backend/tests/test_failed_login_alerting.py` — **+3 tests** (6th-attempt boundary re-alerting, stale-attempts-only window expiry, stale+fresh-5 window expiry) plus new imports (`datetime`/`timedelta`/`UTC`, `db.models.LoginAttempt`)
- `app/backend/tests/test_seed_demo_accounts.py` — **+1 test** (partial-state idempotent re-seed: one demo account already exists, the other doesn't)

No frontend test files were changed (existing coverage for the in-scope component contracts was judged adequate; see matrix above).

## 4. Commands run and results

**Targeted (new/changed) backend tests:**
```
cd app/backend
.venv/Scripts/python.exe -m pytest -q tests/test_auth_me.py tests/test_auth_login.py tests/test_failed_login_alerting.py tests/test_seed_demo_accounts.py
```
Result: **28 passed**, 2 pre-existing deprecation warnings (Starlette/anyio, unrelated), exit code 0, ~23s.

**Full backend suite:**
```
cd app/backend
.venv/Scripts/python.exe -m pytest -q
```
Result: **52 passed** (40 pre-existing + 12 new), 0 failed, 0 skipped, 2 pre-existing warnings, exit code 0, ~35s.

**Backend lint/format sanity on the changed test files (no production code touched):**
```
.venv/Scripts/python.exe -m ruff check tests/test_auth_me.py tests/test_auth_login.py tests/test_failed_login_alerting.py tests/test_seed_demo_accounts.py
.venv/Scripts/python.exe -m black --check tests/test_auth_me.py tests/test_auth_login.py tests/test_failed_login_alerting.py tests/test_seed_demo_accounts.py
```
Result: **All checks passed** / **4 files would be left unchanged**, exit code 0 both.

**Frontend suite (plan-defined `npm run test`), unchanged files, run to confirm no regression:**
```
cd app
npm run test --workspace frontend
```
Result: **4 test files, 11 tests, all passed**, exit code 0, ~2.9s.

No coverage command is defined in the plan's verification commands (§10) or CI config for either workspace, so no coverage percentage is reported — this is a pre-existing project characteristic, not something this agent's scope changes.

## 5. Failures

None. All targeted, full-backend, and full-frontend runs passed with exit code 0. No production defect was found: the behaviors probed (per-attempt re-alerting above threshold, window-expiry semantics, email normalization, session-cookie tampering rejection, `/auth/me` contract, partial-state seed idempotency) all matched the plan's documented design and the actual implementation on first run — no test needed to be adjusted after discovering unexpected behavior.

## 6. Status

**PASS**

All Development-owned test scenarios (TS-01–TS-12 plus the failed-login-alert and seed-idempotency behaviors named in the task) are now mapped to an actual, passing test, including the two closed gaps (`GET /auth/me` coverage, and boundary/window-expiry/case-normalization edge cases). TS-13–TS-16 remain correctly out of Development's/this agent's scope (QA-owned, browser/manual). The full backend (`pytest`) and frontend (`npm run test`) suites both pass with real, reported exit codes and counts.
