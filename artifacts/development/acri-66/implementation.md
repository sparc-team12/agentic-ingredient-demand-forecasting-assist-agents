# Implementation Report — ACRI-66 (Per-user login / auth gate)

## 1. Metadata

| Field | Value |
|---|---|
| Work item | `ACRI-66` (Story-Id `US-030`, epic `ACRI-65` "Authentication") |
| Plan checksum (tech-lead-review.json) | `sha256:e921a607cdfbe1da39afdc31461913c682fb5d4336a4357a9c387ca3b1959fe8` |
| Repository | `agentic-ingredient-demand-forecasting-assist-agents` |
| Branch | `devagent` (current branch at dispatch; no branch was created — working state already had this branch checked out, base is `main`) |
| Implementation round | 1 (initial implementation; no prior rework cycle) |
| Preconditions verified | `requirements-validation.json` (PASS, confidence 0.87), `tech-lead-review.json` (PASS, 1 MINOR + 2 SUGGESTIONs, no Critical/Major), `implementation-plan.md` (read in full) |

## 2. Files changed

All files match the plan's §13 in-scope list exactly, plus two adjacent files (documented under §7 Deviations below). Total: 39 plan files + 2 adjacent = 41 files touched.

### Backend — CREATE (16)
- `app/backend/db/models.py` — `User`, `UserSession`, `LoginAttempt` SQLAlchemy models, `Persona` enum
- `app/backend/db/seed.py` — `seed_demo_accounts(db)`, idempotent, env-configured
- `app/backend/schemas/__init__.py`, `app/backend/schemas/auth.py` — `LoginRequest`, `UserOut`, `ScreenPlaceholderResponse`
- `app/backend/services/auth_service.py` — hashing, session lifecycle, failed-login recording/alerting
- `app/backend/middleware/auth.py` — `get_current_user` dependency, cookie constants
- `app/backend/routes/auth.py` — `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
- `app/backend/routes/screens.py` — 4 protected stub routes
- `app/backend/scripts/__init__.py`, `app/backend/scripts/seed_demo_accounts.py` — standalone seed CLI
- `app/backend/tests/conftest.py` — isolated per-test SQLite DB, `TestClient` w/ `get_db` override, `seed_known_users` helper
- `app/backend/tests/test_auth_login.py`, `test_auth_logout.py`, `test_auth_session_required.py`, `test_failed_login_alerting.py`, `test_seed_demo_accounts.py`

### Backend — MODIFY (4, all plan-scoped)
- `app/backend/main.py` — CORS middleware, `lifespan` startup hook (schema create + seed), routers wired in. (Used FastAPI's `lifespan` context manager rather than the plan's literal `@app.on_event("startup")` phrasing — `on_event` is deprecated in the installed FastAPI 0.141.1/Starlette 1.6.0 and emits a `DeprecationWarning` on every test run; `lifespan` achieves the identical behavior the plan specifies with no functional difference. Not a scope/contract change.)
- `app/backend/.env.example` — added `SEED_*`, `SESSION_COOKIE_SECURE`, `FAILED_LOGIN_ALERT_*` vars with obviously-fake placeholder values (tech-lead MINOR finding applied — see §5)
- `app/backend/pyproject.toml` — `[tool.mypy] files` extended with `schemas`, `scripts`
- `app/README.md` — Scope note updated; "Seeding demo accounts" subsection added

### Frontend — CREATE (15)
- `app/frontend/src/lib/api-client.ts`, `lib/auth-context.tsx`, `lib/screens.ts`
- `app/frontend/src/hooks/use-auth.ts`
- `app/frontend/src/components/auth/login-form.tsx`, `login-form.test.tsx`, `require-auth.tsx`, `require-auth.test.tsx`
- `app/frontend/src/components/common/stub-screen.tsx`
- `app/frontend/src/routes/login.tsx`, `risk-dashboard.tsx`, `ingredient-detail.tsx`, `chat-agent.tsx`, `purchase-order-draft.tsx`
- `app/frontend/src/lib/api-client.test.ts`

### Frontend — MODIFY (4, all plan-scoped)
- `app/frontend/package.json` — added `react-router-dom@^7.18.4` (Assumption A7, tech-lead-confirmed via SUGGESTION note)
- `app/frontend/src/App.tsx` — routing: `/login` public, 4 gated routes wrapped in `RequireAuth`, `/` redirects by auth state
- `app/frontend/src/main.tsx` — wrapped `<App />` in `<BrowserRouter>` + `<AuthProvider>`
- `app/frontend/src/test/App.test.tsx` — updated bootstrap smoke test to assert redirect-to-login for an unauthenticated visitor (mocks `apiClient` rather than performing a real network call)

### DELETE
None (matches plan).

## 3. Acceptance criteria implemented

| AC | Implementation | Test coverage |
|---|---|---|
| AC1 (no auth → denied, redirect to login) | `middleware/auth.py::get_current_user` (401 on all 4 `/screens/*`); `RequireAuth` → `<Navigate to="/login">` | `test_auth_session_required.py` (401 cases), `require-auth.test.tsx`, `App.test.tsx` |
| AC2 (valid credentials → access for that session) | `POST /auth/login` verifies + creates session cookie; subsequent requests admitted | `test_auth_login.py` (both personas), `test_auth_session_required.py` (200 cases), `login-form.test.tsx` |
| AC3 (invalid credentials → error, no access) | Generic `401 {"detail": "Invalid email or password"}`, no cookie/session row created; `LoginForm` renders inline error | `test_auth_login.py` (wrong password, unknown email), `login-form.test.tsx` |
| AC4 (each persona has distinct credentials) | Per-row bcrypt verification; cross-credential login rejected | `test_auth_login.py::test_kitchen_managers_password_does_not_authenticate_as_fb_manager` (and reverse), `test_seed_demo_accounts.py` (distinct emails/hashes) |
| AC5 (both personas get identical access) | No persona branching in `routes/screens.py`; identical response shape | `test_auth_session_required.py::test_both_personas_get_a_byte_identical_response_shape` (all 4 screens, parametrized) |
| Failed-login alerting (authorized resolution) | WARN log at 5th failure in 15-min window, no lockout | `test_failed_login_alerting.py` (4 vs. 5 attempts, no-lockout confirmation) |
| Credential seeding (authorized resolution) | Idempotent `seed_demo_accounts`, standalone CLI, documented placeholders | `test_seed_demo_accounts.py` (idempotency, distinctness, no password-overwrite on rerun) |

## 4. Tests added/changed

**Backend (pytest, 40 tests, all passing):**
`conftest.py` fixtures — isolated temp-file SQLite DB per test, `TestClient` with `get_db` dependency override (not run as a context manager, so the app's real startup `lifespan` never fires against these per-test DBs — avoids any interference with the plan's own precaution against touching the real `app.db`), and `seed_known_users`/`seed_user` helpers. `test_auth_login.py` (8 cases), `test_auth_logout.py` (3), `test_auth_session_required.py` (20, parametrized over the 4 screens), `test_failed_login_alerting.py` (3), `test_seed_demo_accounts.py` (5), plus the pre-existing `test_health.py` (1, untouched/reused).

**Frontend (Vitest, 11 tests, all passing):**
`api-client.test.ts` (4 — credentials/headers, JSON body, `ApiError` with backend detail, non-JSON-body fallback), `require-auth.test.tsx` (3 — loading/redirect/renders-children), `login-form.test.tsx` (3 — success calls `login`, inline error on `ApiError`, generic error on non-`ApiError` failure), `App.test.tsx` (1, updated — asserts redirect to `/login` for an unauthenticated visitor).

## 5. Tech-lead MINOR finding applied

`app/backend/.env.example` now uses obviously-fake placeholders (`SEED_KITCHEN_MANAGER_PASSWORD=changeme-not-a-real-secret`, `SEED_FB_MANAGER_PASSWORD=changeme-also-not-a-real-secret`) with an inline comment warning against putting real-shaped credentials in this committed file. No real/production-shaped secret is committed anywhere.

## 6. Migrations/configuration/operational notes

- No migration tool exists (Assumption A9, unchanged from plan); `Base.metadata.create_all(engine)` runs in `main.py`'s `lifespan` startup hook, plus standalone via `python -m scripts.seed_demo_accounts`.
- New backend env vars (all in `.env.example`): `SEED_KITCHEN_MANAGER_EMAIL/PASSWORD`, `SEED_FB_MANAGER_EMAIL/PASSWORD`, `SESSION_COOKIE_SECURE` (default `false`), `FAILED_LOGIN_ALERT_THRESHOLD` (default `5`), `FAILED_LOGIN_ALERT_WINDOW_MINUTES` (default `15`).
- No new frontend env vars (reuses `VITE_API_URL`).
- Rollback: additive only — revert this story's file changes; delete the local `app.db` and re-run the seed CLI to reset local dev data. No irreversible side effects.

## 7. Deviations / adjacent files (with justification)

1. **`app/backend/requirements.txt`** (adjacent, not in plan's MODIFY list) — added an explicit `bcrypt==4.0.1` pin. **Why:** `passlib[bcrypt]==1.7.4` (already pinned, no new dependency) transitively pulled `bcrypt==5.0.0`, whose backend-detection self-test crashes (`ValueError: password cannot be longer than 72 bytes`, plus `AttributeError: module 'bcrypt' has no attribute '__about__'`) on every call to `hash_password`/`verify_password` — this is a real, upstream passlib/bcrypt incompatibility (passlib 1.7.4 predates bcrypt's 4.1 API changes), not something introduced by this story's code. Without this pin, **every login attempt would 500**. `bcrypt==4.0.1` is the newest release still compatible with `passlib==1.7.4`; verified working via `pip install`, then the full backend test suite and a manual `uvicorn` smoke test (see §8). This is a version-compatibility fix to an already-approved dependency, not a new dependency or a contract change.
2. **`app/backend/requirements-lock.txt`** (adjacent) — regenerated via `pip install`/`pip freeze` to reflect the `bcrypt==4.0.1` pin above. This is the mechanically-generated pip lock file (per `project-initialization.json`'s own note: "requirements-lock.txt (pip freeze output) is used as the pip lock mechanism"); regenerating it after a `requirements.txt` change is the documented, expected workflow, not a new deviation.
3. **`main.py` startup mechanism** — implemented via FastAPI's `lifespan` context manager instead of the plan's literal `@app.on_event("startup")` wording. Same behavior (schema create + seed on startup), avoids a `DeprecationWarning` from the installed FastAPI/Starlette versions. No contract/scope change; noted for transparency only, not treated as an adjacent-file deviation since `main.py` was already in the plan's MODIFY list.
4. **`app/frontend/src/lib/api-client.test.ts`** formatting — Prettier auto-reformatted this file (line-wrapping only) during `format:check` remediation; no semantic change.

No architecture-level deviation occurred; the one architecture change in play (`ARCH-016` → per-user login) was already resolved by `DEC-004` prior to this story.

## 8. Commands executed (real results)

**Backend** (from `app/backend`, `.venv` already present and activated via direct `.venv/Scripts/python.exe` invocation):

| Command | Result |
|---|---|
| `pip install "bcrypt==4.0.1"` | Installed cleanly (prebuilt wheel for Python 3.14) |
| `pip freeze > requirements-lock.txt` | Regenerated, 38 lines |
| `pytest -q` | **40 passed**, 2 warnings (pre-existing Starlette/anyio deprecation warnings, unrelated to this story), ~25s |
| `ruff check .` | **All checks passed** (after one `--fix` for 2 `UP037` redundant-quote findings in `db/models.py`, safe/mechanical) |
| `black --check .` | **All done, 24 files unchanged** (after one `black .` run reformatted 2 files: `services/auth_service.py`, `tests/test_seed_demo_accounts.py`) |
| `mypy .` | **Success: no issues found in 24 source files** |
| Manual smoke (`uvicorn main:app --port 8123`, then `curl /health`, `curl -X POST /auth/login` with the seeded demo kitchen-manager credentials, `curl /screens/risk-dashboard` with the returned cookie) | `/health` → 200; `/auth/login` → 200 + `Set-Cookie: session_token=...; HttpOnly; Path=/; SameSite=lax`; `/screens/risk-dashboard` → 200 with the documented response shape. Server stopped and the resulting local `app.db` (gitignored, `*.db`) removed afterward. |

**Frontend** (from `app/`):

| Command | Result |
|---|---|
| `npm install` | 4 packages added (`react-router-dom` + its transitive deps), 292 packages audited. `npm audit` reports 5 pre-existing vulnerabilities (3 moderate, 1 high, 1 critical) in the dependency tree — not newly introduced by `react-router-dom`; not remediated here (`npm audit fix --force` would apply unrelated breaking upgrades outside this story's scope) — flagged as a carried risk, not silently ignored. |
| `npm run lint --workspace frontend` | **Exit 0**, 1 warning (`react-refresh/only-export-components` in `lib/auth-context.tsx` — expected/accepted, since the plan bundles `AuthProvider` + `AuthContext` in one file; not an error) |
| `npm run typecheck --workspace frontend` | Clean, no output/errors |
| `npm run format:check --workspace frontend` | **All matched files use Prettier code style** (after one `prettier --write` on `api-client.test.ts`, whitespace-only) |
| `npm run test --workspace frontend` | **4 test files, 11 tests, all passed**, ~3s |
| `npm run build --workspace frontend` | `tsc -b && vite build` succeeded; `dist/` produced (186 kB JS / 61 kB gzip), gitignored |

## 9. Unresolved concerns / known QA considerations

- **Carried from tech-lead review** (unchanged, not this agent's to resolve): `SESSION_COOKIE_SECURE` defaults `false` pending the open AWS/TLS hosting decision (`ARCH-018`); no Alembic/migration tool yet; `config/project.yaml`'s HLD/LLD gate flags remain unreconciled with `DEC-005` (out of this agent's file scope); `dev-status.json` staleness is for the orchestrator to refresh.
- **New, discovered during implementation:** the `passlib[bcrypt]`/`bcrypt` version incompatibility (see §7.1) — flagging for awareness in case a future dependency bump re-introduces it; recommend keeping the `bcrypt==4.0.1` pin (or re-verifying compatibility) until `passlib` itself is upgraded/replaced.
- **npm audit** reports 5 pre-existing vulnerabilities unrelated to this story's new dependency; not remediated (out of scope) — flagged for a separate, dedicated dependency-hygiene pass.
- QA scenarios TS-13–TS-16 (browser/manual, out of Development's ownership per the plan) remain to be executed by QA: full-browser redirect/session-persistence check, fb-manager UX-parity spot-check, cookie `HttpOnly`/`SameSite` dev-tools inspection, and out-of-scope-item confirmation (no MFA/reset/idle-timeout).
- The login screen's copy/layout has no design source (plan Q2, already flagged) — authored minimally/functionally; a human should sanity-check copy before merge.

## 10. Status

**COMPLETED** — all plan-scoped files implemented, all specified tests added and passing, all plan-defined backend (`pytest`, `ruff`, `black`, `mypy`) and frontend (`lint`, `typecheck`, `format:check`, `test`, `build`) commands run with real, green results. This is local development-stage evidence only — it does not constitute code review or QA sign-off.
