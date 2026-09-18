# Implementation Plan — ACRI-66 (Per-user login / auth gate)

## 1. Metadata

| Field | Value |
|---|---|
| Work item | `ACRI-66` (Story-Id `US-030`, epic `ACRI-65` "Authentication") |
| Title | Kitchen-manager / F&B-manager logs in with their own email+password before reaching any of the 4 gated screens |
| Status | **PENDING_TECH_LEAD** |
| Repository | `agentic-ingredient-demand-forecasting-assist-agents` |
| Artifact dir | `artifacts/development/acri-66/` |
| Sources | Jira `ACRI-66` (AC1–AC5, Out-of-Scope list, given verbatim in the planning task); `workflow/decisions.md` `DEC-004` (PRD superseded by Jira stories; per-user login supersedes `ARCH-016`) and `DEC-005` (HLD/LLD/architecture-validation gate bypass; resolved tech stack incl. session/hashing mechanism); `artifacts/development/acri-66/requirements-validation.json` (status `PASS`, confidence 0.87); `artifacts/architecture/solution-architecture.md` (`ARCH-002` React, `ARCH-012` SQLite, `ARCH-016` superseded for login model, `ARCH-018` AWS, `ARCH-020` logging); Confluence "Technology Stack" (id `5885657157`, Approved) and "Design Document" (id `5885722653`, Approved) per DEC-005; `artifacts/development/_scaffold/project-initialization.json` (status PASS) for actual repo state; task-prompt-authorized resolutions for failed-login alerting and credential seeding (treated as authorized decisions, labeled as assumptions below) |
| HLD/LLD/architecture-validation gate | **Explicitly bypassed per `DEC-005`.** No `high-level-design.md`, `low-level-design.md`, or `architecture-validation.json` exists or is used as input. Every design decision below that would normally cite an `LLD-` ID is instead labeled `[ASSUMPTION]` and traced to `ARCH-`/`DEC-`/AC IDs or to the task-prompt's explicit resolutions. `config/project.yaml`'s `development.require_approved_hld/require_approved_lld/require_architecture_validation` still read `true`; this is a known, previously-flagged discrepancy (see `project-initialization.json` warnings) that `DEC-005` overrides for this build — not silently ignored, not re-litigated here. |
| Stack (this story) | Frontend: React 18 + TypeScript + Vite 5, npm, Vitest + Testing Library (all already scaffolded). Backend: Python 3.12+ (venv verified on 3.14.5) + FastAPI 0.141.1 + SQLAlchemy 2.0.54 ORM over SQLite, `passlib[bcrypt]` for hashing, pytest (all already scaffolded). New dependency this story: `react-router-dom` (frontend) — see Assumption A7. |
| Base ref | Current `main` working tree at time of planning (git status: `app/` and `artifacts/development/acri-66/` untracked; no other pending changes touched by this plan) |

---

## 2. Requirement / acceptance-criterion traceability

| AC / behavior | Source | How this plan satisfies it |
|---|---|---|
| `ACRI-66-AC1` — no auth → any of the 4 screens denied, redirect to login | Jira AC1 | Backend: `GET /screens/*` (4 stub routes) return `401` with no valid session cookie (§6). Frontend: `RequireAuth` route guard redirects to `/login` for any of the 4 protected routes when `AuthProvider` state is `unauthenticated` (§5). |
| `ACRI-66-AC2` — valid email+password (either persona) → access granted for that session | Jira AC2 | `POST /auth/login` verifies against seeded `users` table, creates a `user_sessions` row + sets an httpOnly session cookie; `RequireAuth`/backend dependency then admits requests bearing that cookie to all 4 stub routes (§5, §6). |
| `ACRI-66-AC3` — invalid credentials → error shown, no screen reachable | Jira AC3 | `POST /auth/login` returns `401` with a generic error (`"Invalid email or password"`) and does **not** set a cookie or create a session row; `LoginForm` renders that error inline and does not navigate (§5, §6). |
| `ACRI-66-AC4` — each persona has its own distinct credential set | Jira AC4 | Seed script creates exactly two `users` rows (`kitchen_manager`, `fb_manager`) with independently generated bcrypt hashes over distinct passwords; login verification is per-row, so one persona's credentials never match the other's hash (§4, §6, TS-08/TS-09). |
| `ACRI-66-AC5` — both personas get identical access to all 4 screens | Jira AC5 | The auth dependency (`middleware/auth.py::get_current_user`) makes an authentication-only decision (valid session → 200) with no persona-based branching anywhere in `routes/screens.py`; response shape is identical for both personas (§6, TS-10). |
| Out of scope: MFA, self-service reset, idle-timeout, extra roles | Jira "Out of scope" | None of these are implemented. No MFA step, no "forgot password" endpoint/screen, no session TTL/expiry logic beyond explicit logout, exactly 2 personas hardcoded in the `Persona` enum (§4, §12). |
| Failed-login alerting resolution | Task prompt (authorized resolution, matches prior `failed_login_alerting_assumption` precedent in `dev-status.json`) | `services/auth_service.py::record_login_attempt` + `check_failed_login_alert` log a structured `WARN` via Python's `logging` module when the 5th failed attempt for the same email lands inside a rolling 15-minute window. No lockout is enforced (§6, §8, TS-11). |
| Credential seeding resolution | Task prompt (authorized resolution) | `db/seed.py::seed_demo_accounts` is idempotent, creates exactly the 2 documented demo accounts, invoked automatically at backend startup and via a standalone `scripts/seed_demo_accounts.py` CLI; credentials documented (non-production-real) in `.env.example`/README, not committed as a real secret (§4, §7, TS-09). |

---

## 3. Repository findings and commands discovered

Findings (from direct inspection, not assumed):

- `app/frontend` and `app/backend` are real, scaffolded, and pass their own smoke tests per `artifacts/development/_scaffold/project-initialization.json` (status `PASS`). This is **not** a greenfield target for `dev-scaffold-agent` — it is an existing, compatible, buildable scaffold; this plan builds directly on it.
- Backend: `app/backend/main.py` currently exposes only `GET /health`. `app/backend/db/session.py` already provides `engine`, `SessionLocal`, `Base` (`DeclarativeBase`), and a `get_db()` FastAPI dependency wired for SQLite (`DATABASE_URL`, default `sqlite:///./app.db`). No models exist yet. `routes/`, `services/`, `middleware/` packages exist as empty, documented placeholders — their doc-comments already anticipate this story (`middleware/__init__.py`: *"the per-user session-cookie mechanism (per DEC-005) is implemented here in a later development stage"*). No `schemas/` or `scripts/` package exists yet — both are new.
- Backend deps already include `passlib[bcrypt]==1.7.4` (per `requirements.txt`, added in scaffold anticipating this story) and `python-multipart`. No `email-validator`/`pydantic[email]` is installed — this plan avoids `EmailStr` to not introduce a new dependency (Assumption A_email).
- `pyproject.toml`'s `[tool.mypy] files` list enumerates packages explicitly (`main.py, db, routes, services, middleware, tests`) — must be extended for the new `schemas` and `scripts` packages or mypy will silently skip them.
- No migration tool (Alembic) is configured; `project-initialization.json`'s own "omissions" note already flagged this as a gap to close "before defining real tables" — this story is the first to define real tables. Plan uses `Base.metadata.create_all()` at startup as the interim mechanism (Assumption A9), consistent with the scaffold's current state, and does not silently introduce Alembic.
- Frontend: `App.tsx`/`main.tsx` are placeholder-only (no router, no providers). No routing library, state-management library, or HTTP-form library is installed — `tech-stack.md` §3 explicitly leaves state-management and build-tooling choices `[TBD]`, and names no routing library at all. `components/`, `routes/`, `hooks/`, `lib/` exist as empty directories with README placeholders describing exactly this intended structure (e.g. `lib/README.md`: *"Utilities and API client configuration (e.g. the shared HTTP client for the FastAPI backend)"*).
- The unrelated `c:\Users\aakash.ck\Downloads\CLAUDE.md` (Zustand/TanStack Query/shadcn/ui/React Router/RHF conventions for a "solar panel inspection" Vite app) does **not** govern this repository. `project-initialization.json`'s own "omissions" section already explicitly disregarded it for this repo ("these appear only in an unrelated CLAUDE.md file for a different project... disregarded as out of scope"). This plan follows the same treatment and instead follows this repo's own scaffolded conventions (`.claude/CLAUDE.md`, the actual `app/frontend/src/*` folder READMEs).
- CI (`.github/workflows/ci.yml`) runs, per workspace: frontend `npm install`, `lint`, `typecheck`, `test`, `build` (from `app/`); backend `pip install -r requirements-dev.txt`, `ruff check .`, `black --check .`, `pytest` (from `app/backend/`). `mypy` is not run in CI but is an available local command per `README.md`.
- Git status confirms only `app/` and `artifacts/development/acri-66/` are untracked/new; no conflicting in-flight edits overlap this story's intended files.

Exact commands this plan will rely on for verification (§10), all discovered from `app/README.md` and `.github/workflows/ci.yml`, none invented:

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
| 1 | `app/backend/db/models.py` | SQLAlchemy ORM models: `User` (id, email unique, password_hash, persona, created_at), `UserSession` (token PK, user_id FK, created_at), `LoginAttempt` (id, email, success, created_at) |
| 2 | `app/backend/db/seed.py` | `seed_demo_accounts(db)` — idempotent creation of exactly the 2 demo accounts (kitchen-manager, fb-manager) from env-configured (documented, non-real) credentials |
| 3 | `app/backend/schemas/__init__.py` | New package marker for Pydantic request/response schemas |
| 4 | `app/backend/schemas/auth.py` | `LoginRequest`, `UserOut`, `ScreenPlaceholderResponse` Pydantic models |
| 5 | `app/backend/services/auth_service.py` | Password hashing/verification (passlib bcrypt), session create/lookup/delete, failed-login attempt recording + rolling-window WARN alert |
| 6 | `app/backend/middleware/auth.py` | `get_current_user` FastAPI dependency (reads `session_token` cookie, validates against `user_sessions`, raises `401`); cookie constants/helpers |
| 7 | `app/backend/routes/auth.py` | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` |
| 8 | `app/backend/routes/screens.py` | 4 stub protected routes: `GET /screens/risk-dashboard`, `/ingredient-detail`, `/chat-agent`, `/purchase-order-draft` |
| 9 | `app/backend/scripts/__init__.py` | Package marker so the seed script is runnable as `python -m scripts.seed_demo_accounts` |
| 10 | `app/backend/scripts/seed_demo_accounts.py` | Standalone CLI: creates schema (`Base.metadata.create_all`) + calls `seed_demo_accounts` |
| 11 | `app/backend/tests/conftest.py` | pytest fixtures: isolated temp-file/in-memory test DB, `TestClient`, helper to seed known test users |
| 12 | `app/backend/tests/test_auth_login.py` | AC2/AC3/AC4 login behavior |
| 13 | `app/backend/tests/test_auth_logout.py` | Logout invalidates session |
| 14 | `app/backend/tests/test_auth_session_required.py` | AC1/AC5 — all 4 stub routes: 401 unauthenticated, 200 identical shape for both personas |
| 15 | `app/backend/tests/test_failed_login_alerting.py` | 5-in-15-min WARN alert behavior |
| 16 | `app/backend/tests/test_seed_demo_accounts.py` | Seed idempotency + exactly-2-distinct-accounts (AC4) |
| 17 | `app/frontend/src/lib/api-client.ts` | Thin fetch wrapper (base URL from `VITE_API_URL`, `credentials: 'include'`, JSON handling, typed `ApiError`) |
| 18 | `app/frontend/src/lib/auth-context.tsx` | `AuthProvider` + `AuthContext` — session bootstrap via `GET /auth/me`, `login()`, `logout()`, `status` state |
| 19 | `app/frontend/src/lib/screens.ts` | Static metadata for the 4 gated screens (id, path, label, backend stub path) |
| 20 | `app/frontend/src/hooks/use-auth.ts` | `useAuth()` hook consuming `AuthContext` |
| 21 | `app/frontend/src/components/auth/login-form.tsx` | Controlled email/password form, calls `useAuth().login`, renders inline error on failure |
| 22 | `app/frontend/src/components/auth/require-auth.tsx` | Route guard: renders children when authenticated, `<Navigate to="/login" />` otherwise, loading state while session bootstrap is in flight |
| 23 | `app/frontend/src/components/common/stub-screen.tsx` | Shared placeholder-screen component: fetches its backend stub endpoint on mount, renders the returned message + a logout button |
| 24 | `app/frontend/src/routes/login.tsx` | `/login` page, renders `LoginForm` |
| 25 | `app/frontend/src/routes/risk-dashboard.tsx` | `/risk-dashboard` stub page (uses `stub-screen`) |
| 26 | `app/frontend/src/routes/ingredient-detail.tsx` | `/ingredient-detail` stub page |
| 27 | `app/frontend/src/routes/chat-agent.tsx` | `/chat-agent` stub page |
| 28 | `app/frontend/src/routes/purchase-order-draft.tsx` | `/purchase-order-draft` stub page |
| 29 | `app/frontend/src/components/auth/require-auth.test.tsx` | AC1: redirects unauthenticated; renders children when authenticated |
| 30 | `app/frontend/src/components/auth/login-form.test.tsx` | AC2/AC3: success path calls login and errors surface inline |
| 31 | `app/frontend/src/lib/api-client.test.ts` | Request/error-handling behavior of the fetch wrapper |

### MODIFY

| # | File | Change |
|---|---|---|
| 1 | `app/backend/main.py` | Add `CORSMiddleware` (origin = `FRONTEND_ORIGIN`, `allow_credentials=True`); add startup hook calling `Base.metadata.create_all(engine)` + `seed_demo_accounts`; `include_router` for `auth` and `screens` routers |
| 2 | `app/backend/.env.example` | Add `SEED_KITCHEN_MANAGER_EMAIL`, `SEED_KITCHEN_MANAGER_PASSWORD`, `SEED_FB_MANAGER_EMAIL`, `SEED_FB_MANAGER_PASSWORD` (documented demo values, clearly marked non-production), `SESSION_COOKIE_SECURE`, `FAILED_LOGIN_ALERT_THRESHOLD`, `FAILED_LOGIN_ALERT_WINDOW_MINUTES` |
| 3 | `app/backend/pyproject.toml` | Extend `[tool.mypy] files` to include `schemas` and `scripts`; extend `[tool.pytest.ini_options]` only if needed (no change expected — `testpaths = ["tests"]` already covers new test files) |
| 4 | `app/README.md` | Update "Scope note" (login is no longer unimplemented); add a "Seeding demo accounts" subsection documenting the CLI script and the two demo personas |
| 5 | `app/frontend/package.json` | Add `react-router-dom` dependency (Assumption A7) |
| 6 | `app/frontend/src/App.tsx` | Add `<Routes>`: `/login` public; `/risk-dashboard`, `/ingredient-detail`, `/chat-agent`, `/purchase-order-draft` each wrapped in `RequireAuth`; `/` redirects based on auth state |
| 7 | `app/frontend/src/main.tsx` | Wrap `<App />` in `<BrowserRouter>` and `<AuthProvider>` |
| 8 | `app/frontend/src/test/App.test.tsx` | Update bootstrap smoke test: render `App` inside a test router + `AuthProvider` (mocked unauthenticated) and assert it redirects to/renders the login screen, since the prior "static placeholder text" assertion no longer holds once routing exists |

### DELETE

None.

### REUSE (unmodified, load-bearing for this story)

`app/backend/db/session.py` (engine/`Base`/`get_db`), `app/backend/requirements.txt` (passlib/bcrypt already pinned), `app/backend/requirements-dev.txt`, `app/backend/.gitignore`, `app/backend/tests/test_health.py`, `app/backend/routes/__init__.py`, `app/backend/services/__init__.py`, `app/backend/middleware/__init__.py`, `app/frontend/vite.config.ts`, `app/frontend/vitest.config.ts`, `app/frontend/tsconfig.json`, `app/frontend/tsconfig.node.json`, `app/frontend/eslint.config.js`, `app/frontend/.prettierrc.json`, `app/frontend/.env.example`, `app/frontend/src/styles.css`, `app/frontend/src/vite-env.d.ts`, `app/frontend/src/test/setup.ts`, `app/package.json`, `.github/workflows/ci.yml`.

---

## 5. Execution and data flow

**Login (AC2/AC3):**
`LoginForm` (route `/login`) → `useAuth().login(email, password)` → `apiClient.post('/auth/login', {email, password})` (`credentials: 'include'`) → FastAPI `routes/auth.py::login` → `services/auth_service.py::verify_credentials` (lowercases email, looks up `User`, `passlib` bcrypt verify) → on success: `create_session` inserts a `UserSession` row (opaque `secrets.token_urlsafe(32)` token) and the response sets `Set-Cookie: session_token=...; HttpOnly; SameSite=Lax` → `record_login_attempt(success=True)` logged → `AuthProvider` stores `{email, persona}` in React state, `status = 'authenticated'`, caller navigates to `/risk-dashboard`. On failure: `record_login_attempt(success=False)` → `check_failed_login_alert` (rolling 15-min count) → `401 {"detail": "Invalid email or password"}`, no cookie set → `LoginForm` renders the error inline, no navigation.

**Session bootstrap on page load:** `AuthProvider` mount → `GET /auth/me` (cookie sent automatically by the browser if present) → `middleware/auth.py::get_current_user` validates the cookie against `user_sessions` → 200 sets `status='authenticated'`; 401 sets `status='unauthenticated'`.

**Protected screen access (AC1/AC5):** Navigating to `/risk-dashboard` (etc.) → React Router renders `RequireAuth` → if `status==='loading'` shows a loading placeholder; if `'unauthenticated'` renders `<Navigate to="/login" />`; if `'authenticated'` renders the route's `stub-screen` → `stub-screen` calls `GET /screens/risk-dashboard` (cookie sent automatically) → `middleware/auth.py::get_current_user` (same dependency as `/auth/me`) → `routes/screens.py` handler returns `{screen, message, user:{email, persona}}` with no persona-conditional logic (AC5) → rendered to the manager.

**Logout:** `stub-screen`'s logout button → `useAuth().logout()` → `POST /auth/logout` → backend deletes the `UserSession` row for that cookie (if present) and clears the cookie → frontend resets state to `'unauthenticated'` and navigates to `/login`.

**Seeding:** On backend process startup, `main.py`'s startup hook calls `Base.metadata.create_all(engine)` then `seed_demo_accounts(db)`, which is a no-op if the two documented accounts already exist (idempotent, checked by email). The same logic is exposed standalone via `python -m scripts.seed_demo_accounts` for explicit/manual invocation (e.g., CI, fresh environment setup) without starting the full ASGI app.

---

## 6. Contracts, validation, error handling, and security

### Backend API contracts

| Endpoint | Auth required | Request | 200 Response | Error responses |
|---|---|---|---|---|
| `POST /auth/login` | No | `{email: str, password: str}` (both required, non-empty; basic `"@"`-presence check on email — see Assumption A_email) | `{email, persona}` + `Set-Cookie: session_token` | `401 {"detail": "Invalid email or password"}` (unknown email OR wrong password — identical message, no enumeration); `422` on missing/empty fields (Pydantic) |
| `POST /auth/logout` | No (idempotent — safe to call with or without a valid/any cookie) | none | `{"status": "ok"}` + cookie cleared | none (always 200) |
| `GET /auth/me` | Yes | none | `{email, persona}` | `401 {"detail": "Not authenticated"}` |
| `GET /screens/risk-dashboard` | Yes | none | `{screen: "risk-dashboard", message: "Authenticated placeholder — business logic not yet implemented", user: {email, persona}}` | `401 {"detail": "Not authenticated"}` |
| `GET /screens/ingredient-detail` | Yes | none | same shape, `screen: "ingredient-detail"` | `401` (same) |
| `GET /screens/chat-agent` | Yes | none | same shape, `screen: "chat-agent"` | `401` (same) |
| `GET /screens/purchase-order-draft` | Yes | none | same shape, `screen: "purchase-order-draft"` | `401` (same) |

### Persistence (SQLite, via SQLAlchemy — `ARCH-012`)

- `users`: `id INTEGER PK`, `email TEXT UNIQUE NOT NULL` (stored lowercased), `password_hash TEXT NOT NULL`, `persona TEXT NOT NULL CHECK IN ('kitchen_manager','fb_manager')`, `created_at DATETIME NOT NULL DEFAULT now`.
- `user_sessions`: `token TEXT PK` (opaque, 256-bit, `secrets.token_urlsafe(32)`), `user_id INTEGER NOT NULL REFERENCES users(id)`, `created_at DATETIME NOT NULL DEFAULT now`.
- `login_attempts`: `id INTEGER PK`, `email TEXT NOT NULL`, `success BOOLEAN NOT NULL`, `created_at DATETIME NOT NULL DEFAULT now` — doubles as the ARCH-020-required login-attempt audit log and the data source for the rolling-window alert check.

### AuthN/AuthZ

- Authentication: email + password against `users.password_hash` (`passlib` bcrypt, `CryptContext(schemes=["bcrypt"], deprecated="auto")`).
- Authorization: binary (authenticated vs. not) only — per `ARCH-001`/AC5, there is no per-persona restriction anywhere in this story's routes. `persona` is carried for display/traceability only, never for an access decision.
- Session: opaque server-side token in an `httpOnly`, `SameSite=Lax` cookie named `session_token`; `Secure` flag controlled by `SESSION_COOKIE_SECURE` env var (Assumption A12). No expiry/max-age is set on the cookie or the `user_sessions` row (Assumption A11 — matches the explicit "no session idle-timeout" out-of-scope item); session ends only on explicit logout or DB/browser-state loss.
- CORS: `CORSMiddleware` restricted to `FRONTEND_ORIGIN`, `allow_credentials=True` (required for the cookie to be sent cross-origin during local dev where frontend :5173 and backend :8000 are different origins).

### Error handling

- Invalid login → generic `401`, no user/credential enumeration (Assumption A10).
- Missing/invalid session on any protected route → generic `401 {"detail": "Not authenticated"}`.
- Malformed login body → FastAPI/Pydantic `422` (framework default).
- Failed-login alerting: on every failed attempt, count failed `login_attempts` for that email in the trailing 15 minutes (`FAILED_LOGIN_ALERT_WINDOW_MINUTES`, default 15); at count ≥ 5 (`FAILED_LOGIN_ALERT_THRESHOLD`, default 5) log one structured `WARN` (`logger.warning("failed_login_alert", extra={"email":…, "attempt_count":…, "window_minutes":…})`) — **no lockout, no blocked response**, per the authorized resolution.

### Idempotency/concurrency

- `seed_demo_accounts` idempotent by email lookup-then-create.
- SQLite single-writer model (already the architecture's accepted posture, `ARCH-012`) is sufficient at this usage volume; no additional locking introduced.
- Login is not idempotent by nature (each successful login creates a new session row) — standard, not flagged as a defect.

---

## 7. Data migration and backward compatibility

Greenfield tables (`users`, `user_sessions`, `login_attempts`) — no pre-existing data to migrate. Schema is created via `Base.metadata.create_all(engine)` at backend startup (Assumption A9: no Alembic/migration tool exists yet in this scaffold; this is the same interim posture the scaffold's own `project-initialization.json` already anticipated, "a future stage should add one before defining real tables" — this story is that future stage's first real table, and formal migration tooling is flagged here as a recommendation, not silently added as a new, undiscussed dependency). No backward-compatibility concern: this is the first version of these tables and there is no prior schema to remain compatible with.

---

## 8. Observability / configuration

- Every login attempt (success and failure) is persisted to `login_attempts` and logged (`logger.info` on success, `logger.info` on an individual failure, `logger.warning` structured alert at the 5-in-15-min threshold) — satisfies `ARCH-020`'s "every login attempt... is logged."
- Every logout is logged at `info` level.
- New environment variables (all documented in `app/backend/.env.example` and `app/README.md`):
  - `SEED_KITCHEN_MANAGER_EMAIL` / `SEED_KITCHEN_MANAGER_PASSWORD` — demo-only, non-production-real credentials for the kitchen-manager persona.
  - `SEED_FB_MANAGER_EMAIL` / `SEED_FB_MANAGER_PASSWORD` — demo-only, non-production-real credentials for the fb-manager persona.
  - `SESSION_COOKIE_SECURE` (default `false`) — must be set `true` once the still-open AWS/TLS hosting topology (`ARCH-018` open item) is resolved.
  - `FAILED_LOGIN_ALERT_THRESHOLD` (default `5`), `FAILED_LOGIN_ALERT_WINDOW_MINUTES` (default `15`) — configurable rather than hardcoded, consistent with this repo's general preference (`ARCH-013`) for named configuration over magic numbers, though this specific pair is this story's own addition, not an existing `ARCH-013` item.
- Frontend: no new env vars — reuses existing `VITE_API_URL`.

---

## 9. Test scenarios

| ID | Level | AC / concern | Expected result | Owner |
|---|---|---|---|---|
| TS-01 | Backend unit | AC1 | Each of the 4 `/screens/*` endpoints returns `401` with no session cookie | Development |
| TS-02 | Frontend component | AC1 | `RequireAuth` renders `<Navigate to="/login">` when auth status is `unauthenticated` | Development |
| TS-03 | Backend unit | AC2 | Valid kitchen-manager login returns `200` + sets cookie; a follow-up request with that cookie to a stub screen returns `200` | Development |
| TS-04 | Backend unit | AC2 | Same as TS-03 for fb-manager credentials | Development |
| TS-05 | Frontend component | AC2 | `LoginForm`, given mocked successful `apiClient.login`, calls it with entered values and triggers the success callback | Development |
| TS-06 | Backend unit | AC3 | Login with wrong password, and separately with an unknown email, both return `401` with the generic message; no session row is created either time | Development |
| TS-07 | Frontend component | AC3 | `LoginForm`, given a mocked `401` from `apiClient.login`, displays the inline error and does not navigate | Development |
| TS-08 | Backend unit | AC4 | Kitchen-manager's password does not authenticate as fb-manager (and vice versa) — cross-credential attempt returns `401` | Development |
| TS-09 | Backend unit | AC4 / seeding | `seed_demo_accounts` run twice produces exactly 2 users total (no duplicates, no error); the two accounts have distinct emails and distinct password hashes | Development |
| TS-10 | Backend unit | AC5 | Authenticated kitchen-manager and authenticated fb-manager each receive `200` with byte-identical response *shape* (same keys) from all 4 stub endpoints — no field is present for one persona and missing for the other | Development |
| TS-11 | Backend unit | Failed-login alerting (resolution) | 5 failed attempts for the same email inside 15 minutes emit exactly one `WARNING`-level log record (asserted via `caplog`); 4 attempts emit none | Development |
| TS-12 | Backend unit | Logout | After `POST /auth/logout`, the previously-valid session cookie no longer authenticates (`401` on a subsequent stub call) | Development |
| TS-13 | e2e / browser | AC1 + AC2 | In a real browser: visiting a protected URL directly with no prior session redirects to `/login`; logging in through the UI grants navigation to all 4 stub screens without further redirects; the session persists across client-side navigation between them | QA |
| TS-14 | e2e / manual | AC5 (UX parity) | Confirm fb-manager sees no visually restricted/aggregate-only variant of any of the 4 (stub, for now) screens; re-verify once each screen's real business logic lands in its own story | QA |
| TS-15 | Manual / security | Non-functional | Inspect the session cookie in browser dev tools: confirm `HttpOnly` and `SameSite=Lax` flags are set and the cookie is not readable via `document.cookie` | QA |
| TS-16 | Manual | Out-of-scope confirmation | Confirm no MFA step, no self-service "forgot password" link, and no idle-timeout/forced-logout behavior appear anywhere in the login flow (documented out-of-scope, not a defect) | QA |

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
# then, from another shell:
curl -i http://127.0.0.1:8000/health
curl -i -c cookies.txt -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d "{\"email\":\"<seeded kitchen-manager email>\",\"password\":\"<seeded password>\"}"
curl -i -b cookies.txt http://127.0.0.1:8000/screens/risk-dashboard
```

All commands above are taken verbatim from `app/README.md` and `.github/workflows/ci.yml`; none are invented for this story. CI (`.github/workflows/ci.yml`) already runs the frontend and backend blocks above (minus `format:check`/`mypy`, which remain available local-only commands per `README.md`) on every push/PR to `main` and needs no modification for this story to be covered.

---

## 11. Rollback/recovery

- All changes in this story are additive (new files, two new tables, one new frontend dependency, small modifications to `main.py`/`App.tsx`/`main.tsx`/`package.json`/`pyproject.toml`/`.env.example`/`README.md`). No existing endpoint, table, or component is altered destructively.
- Code rollback: revert the commit(s) introducing this story's files; `main.py`/`App.tsx`/`main.tsx`/`package.json`/`pyproject.toml`/`.env.example`/`README.md` revert cleanly to their current scaffold state via the same commit revert.
- Data rollback: the two new tables (`users`, `user_sessions`, `login_attempts`) hold no pre-existing production data (greenfield, POC, local SQLite file). Recovery = delete the local `app.db` file (dev) or drop the three tables, then re-run `python -m scripts.seed_demo_accounts` to re-seed. No data-migration-down path is needed since nothing pre-existed.
- No irreversible external side effects: no email sent, no third-party account created, no production secret provisioned (seed credentials are documented POC placeholders, not real secrets).

---

## 12. Risks, assumptions, deviations, and open questions

**Explicit assumptions (all labeled per the HLD/LLD bypass, none silently invented):**

- **A1** — This plan is grounded directly in Jira `ACRI-66` + `DEC-004`/`DEC-005` + `solution-architecture.md` + the approved Confluence Tech Stack/Design Document pages, per the explicitly authorized HLD/LLD/architecture-validation bypass. Not a deviation — an authorized substitution of sources.
- **A2** — Per-user login (2 distinct personas) supersedes `ARCH-016`'s single-shared-login model, per `DEC-004`. Explicit, already-recorded, not re-litigated here.
- **A3** — Session mechanism: opaque 256-bit token, `httpOnly`/`SameSite=Lax` cookie, `user_sessions` SQLite table — directly per `DEC-005`.
- **A4** — Password hashing: `passlib[bcrypt]`, already an approved/installed dependency per `DEC-005`.
- **A5** — Failed-login alerting: 5 attempts/15-minute rolling window → single `WARNING` log entry, no lockout — per this task's authorized resolution (mirrors the prior `failed_login_alerting_assumption` precedent).
- **A6** — Credential seeding: idempotent backend seed script/fixture, exactly 2 demo accounts, documented non-production-real credentials — per this task's authorized resolution.
- **A7** — Routing library: `react-router-dom` added as a new frontend dependency. `tech-stack.md` names no routing library at all (only React itself is decided); this is the standard, minimal, actively-maintained routing library for a React SPA and is required for AC1's "redirect to login" behavior and the requested route-guard wrapper to exist at all. Treated as a reversible, low-risk additive dependency, not an irreversible architecture choice — flagged for tech-lead confirmation rather than silently assumed permanent.
- **A8** — Client-side session state: React Context (`AuthProvider`), not a dedicated state-management library. `tech-stack.md` §3 leaves "state management library" `[TBD — confirm with stakeholder]`; Context is the zero-new-dependency option appropriate to this story's narrow scope (one boolean-ish auth status + one small user object). Note: the unrelated `c:\Users\aakash.ck\Downloads\CLAUDE.md` file (Zustand/TanStack Query/shadcn/ui conventions) belongs to a different project and does not apply here — already disregarded once by `dev-scaffold-agent`; restated here so it is not mistaken for an overlooked convention on this story.
- **A9** — No Alembic/migration tool is introduced; schema is created via `Base.metadata.create_all()` at startup, consistent with the scaffold's current state. Recommend adopting a migration tool before the next story that changes this schema.
- **A10** — Login error responses are deliberately generic ("Invalid email or password") to avoid user/credential enumeration — a security-conscious default not mandated verbatim by any AC.
- **A11** — Session cookie/row carries no expiry — matches the explicit "no session idle-timeout" out-of-scope item; session ends only via explicit logout or client/browser state loss.
- **A12** — `SESSION_COOKIE_SECURE` defaults to `false` for local dev; must be flipped to `true` once the still-open AWS/TLS hosting topology (`ARCH-018` open item) is decided. This plan does not decide that topology.
- **A_email** — Login request validates email only as a required, non-empty string containing `"@"` (not full RFC 5322/`EmailStr` validation), to avoid adding the `email-validator` dependency for a POC-scale, seed-only user set.
- **A13** — `config/project.yaml`'s `development.require_approved_hld/require_approved_lld/require_architecture_validation` still read `true`. This plan does not modify `config/project.yaml` (out of this agent's scope); the discrepancy with `DEC-005`'s bypass is flagged here consistent with `project-initialization.json`'s own prior warning about the same gap, not newly discovered.

**Open questions (non-blocking — forwarded to tech-lead review, none require an architecture decision to proceed):**

- **Q1** — Test isolation strategy: `tests/conftest.py` will use a dedicated test database (temp-file or in-memory SQLite via dependency override), not the developer's local `app.db`. Tech lead should confirm this is the expected approach for this repo's test conventions (no prior precedent exists yet, since this is the first story with persistence).
- **Q2** — The login screen has no wireframe/spec anywhere (per `requirements-validation.json`'s own warning — the Confluence Design Document predates auth). This plan authors minimal, functional copy/layout for the login form; a human/tech-lead should sanity-check the copy before merge, since no design source exists to trace it to.
- **Q3** — Whether `SESSION_COOKIE_SECURE` should already default to `true` in this environment (e.g., if local HTTPS dev tooling exists) — currently defaults `false`; confirm acceptable for this POC stage.

**Deviations from approved architecture requiring a route back to architecture approval:** none identified. The one architecture-level change in play (`ARCH-016` single-shared-login → per-user login) is already resolved by `DEC-004`, not newly introduced by this plan.

**BLOCKED status:** **No.** No material open question above requires an architecture decision this plan is not authorized to make; all design choices are either directly sourced from `DEC-004`/`DEC-005`/`ARCH-` elements or are explicitly labeled, low-risk, reversible assumptions per this task's authorization to proceed without HLD/LLD.

---

## 13. Plan checksum

**In-scope file list (CREATE + MODIFY, sorted):**

```
app/README.md
app/backend/.env.example
app/backend/db/models.py
app/backend/db/seed.py
app/backend/main.py
app/backend/middleware/auth.py
app/backend/pyproject.toml
app/backend/routes/auth.py
app/backend/routes/screens.py
app/backend/schemas/__init__.py
app/backend/schemas/auth.py
app/backend/scripts/__init__.py
app/backend/scripts/seed_demo_accounts.py
app/backend/services/auth_service.py
app/backend/tests/conftest.py
app/backend/tests/test_auth_login.py
app/backend/tests/test_auth_logout.py
app/backend/tests/test_auth_session_required.py
app/backend/tests/test_failed_login_alerting.py
app/backend/tests/test_seed_demo_accounts.py
app/frontend/package.json
app/frontend/src/App.tsx
app/frontend/src/components/auth/login-form.test.tsx
app/frontend/src/components/auth/login-form.tsx
app/frontend/src/components/auth/require-auth.test.tsx
app/frontend/src/components/auth/require-auth.tsx
app/frontend/src/components/common/stub-screen.tsx
app/frontend/src/hooks/use-auth.ts
app/frontend/src/lib/api-client.test.ts
app/frontend/src/lib/api-client.ts
app/frontend/src/lib/auth-context.tsx
app/frontend/src/lib/screens.ts
app/frontend/src/main.tsx
app/frontend/src/routes/chat-agent.tsx
app/frontend/src/routes/ingredient-detail.tsx
app/frontend/src/routes/login.tsx
app/frontend/src/routes/purchase-order-draft.tsx
app/frontend/src/routes/risk-dashboard.tsx
app/frontend/src/test/App.test.tsx
```

**Counts:**

| Category | Count |
|---|---|
| CREATE | 31 |
| MODIFY | 8 |
| DELETE | 0 |
| REUSE (unmodified, referenced) | 19 |
| **Total in-scope (CREATE+MODIFY)** | **39** |
