# QA Handoff — ACRI-66 (Per-user login / auth gate)

## 1. Work item, source artifacts, repository, branch/ref, working-tree state

| Field | Value |
|---|---|
| Work item | `ACRI-66` (Story-Id `US-030`, epic `ACRI-65` "Authentication"), Jira project `ACRI` |
| Title | Kitchen-manager / F&B-manager logs in with their own email+password before reaching any of the 4 gated screens |
| Repository | `agentic-ingredient-demand-forecasting-assist-agents` |
| Branch | `devagent` (current branch at implementation dispatch; not created new — was already checked out); base `main` |
| Working-tree state | `app/` and `artifacts/development/acri-66/` are new/untracked (no prior commit exists for this feature). No conflicting in-flight edits overlap this story's files. Unrelated modified files exist on this branch (`.claude/CLAUDE.md`, orchestrator/agent docs, `README.md`, `artifacts/README.md`, `config/project.yaml`, `docs/01-prd/...`, `workflow/decisions.md`) — these belong to the discovery/architecture-pipeline consolidation work, not to this story; QA should not expect them to relate to the login feature. |
| Plan checksum | `sha256:e921a607cdfbe1da39afdc31461913c682fb5d4336a4357a9c387ca3b1959fe8` — matching across `implementation-plan.md`, `tech-lead-review.json`, `code-review.json`, `development-verification.json`, and cited by `implementation.md`/`unit-test-report.md` |
| Gate statuses (all PASS, same work item, same plan checksum) | `requirements-validation.json` PASS (confidence 0.87) · `tech-lead-review.json` PASS (round 1) · `unit-test-report.md` PASS · `code-review.json` PASS (round 1) · `development-verification.json` PASS |

**Traceability in place of HLD/LLD** (explicitly bypassed per human-directed override — see `workflow/decisions.md`):
- `DEC-004` — PRD superseded by Jira `ACRI` user stories as the requirements source; resolves the login model to **per-user** login (superseding `ARCH-016`'s single-shared-login), grounded in Jira `ACRI-66` (Story-Id `US-030`).
- `DEC-005` — explicit human bypass of the HLD/LLD/architecture-validation development gate; resolves the IAM protocol (passlib[bcrypt] hashing, opaque server-side session token, httpOnly/`SameSite=Lax` cookie, SQLite `user_sessions` table) and other tech-stack `[TBD]` items directly, grounded in the approved Confluence "Technology Stack" page (id `5885657157`) and "Design Document" page (id `5885722653`).
- `ARCH-` ids traced by the plan: `ARCH-001` (authZ model — binary, no persona restriction), `ARCH-012` (SQLite persistence), `ARCH-013` (named configuration over magic numbers), `ARCH-016` (superseded per DEC-004), `ARCH-018` (AWS/TLS hosting — still open, affects `SESSION_COOKIE_SECURE`), `ARCH-020` (login-attempt logging requirement).

QA should treat Jira `ACRI-66`'s AC1–AC5 + Out-of-Scope list, plus `DEC-004`/`DEC-005`, as the controlling spec for this story — not `solution-architecture.md#ARCH-016` (superseded) and not the Confluence Design Document (predates auth, has no login-screen spec).

---

## 2. User-visible change summary and out-of-scope items

**What changed (user-visible):**
- Visiting any of the 4 app screens — risk dashboard, ingredient detail, Chat Agent, purchase-order draft — with no prior login now redirects to a `/login` screen instead of showing content.
- A new login screen accepts email + password. Two demo personas exist: **kitchen-manager** and **fb-manager**, each with their own distinct, independently seeded credentials (values documented as placeholders in `app/backend/.env.example`, not real secrets — see §5).
- Successful login with either persona's own credentials grants that browser session access to all 4 screens (currently stub/placeholder content — no business logic for those screens is part of this story).
- Wrong password or unknown email shows an inline, generic error ("Invalid email or password") and does not grant access.
- One persona's credentials never authenticate as the other persona.
- Both personas, once logged in, see byte-identical access/response shape across all 4 screens — no restricted or aggregate-only view for either.
- A logout action ends the session.

**Explicitly out of scope (per Jira ACRI-66 and this plan — not defects if absent):**
- Multi-factor authentication (MFA).
- Self-service "forgot password" / password reset flow.
- Session idle-timeout or forced logout on inactivity (session persists until explicit logout or browser/DB state loss — no expiry is set).
- Any additional roles/personas beyond kitchen-manager and fb-manager.
- Login lockout / rate-limiting after repeated failed attempts (failed logins are logged with a WARN-level alert at 5-in-15-minutes; no account lockout or blocked response is implemented — an accepted resolution, tracked as an open policy question, not a gap in this build).
- Real business logic behind the 4 screens (they remain placeholder/stub content; this story is auth-only).
- Any visual/UX design source for the login screen itself — no wireframe existed prior to this story; layout/copy was authored fresh by Development (see §8).

---

## 3. Acceptance-criterion matrix

| AC | Criterion (paraphrased) | Dev evidence | Status | Remaining QA validation |
|---|---|---|---|---|
| **ACRI-66-AC1** | No auth → any of the 4 screens denied, redirected to login | Backend: `middleware/auth.py::get_current_user` returns 401 with no/invalid session cookie on all 4 `/screens/*` routes — verified via `test_auth_session_required.py` (parametrized, 4/4 no-cookie + 4/4 garbage-cookie). Frontend: `RequireAuth` renders `<Navigate to="/login" replace />` when unauthenticated — verified via `require-auth.test.tsx`, `App.test.tsx`. Independently re-run by both `code-review.json` and `development-verification.json`. | **PASS (dev-verified)** | TS-13: real-browser direct-URL visit with no session redirects to `/login`; session persists across client-side navigation. Not exercisable via pytest/Vitest alone. |
| **ACRI-66-AC2** | Valid email+password (either persona) → access granted for that session | `POST /auth/login` sets httpOnly session cookie on success; subsequent `/screens/*` requests with that cookie return 200 for both personas — `test_auth_login.py`, `test_auth_session_required.py` (200 cases). `login-form.tsx` calls `useAuth().login` and navigates to `/risk-dashboard` on success — `login-form.test.tsx`. | **PASS (dev-verified)** | TS-13: full UI login flow in a real browser grants navigation to all 4 stub screens with no further redirects. |
| **ACRI-66-AC3** | Invalid credentials → error shown, no screen reachable | `routes/auth.py::login` returns generic `401 {"detail": "Invalid email or password"}` for both unknown-email and wrong-password, no cookie/session row created — `test_auth_login.py`. `LoginForm` renders inline `role=alert` error, no navigation — `login-form.test.tsx`. | **PASS (dev-verified)** | TS-15 (security/manual): confirm `HttpOnly` + `SameSite=Lax` cookie flags via browser dev tools and that the cookie is not readable via `document.cookie` — not exercisable via pytest/Vitest. |
| **ACRI-66-AC4** | Each persona has its own distinct credential set; one never authenticates as the other | Per-row bcrypt verification in `verify_credentials`; cross-credential login rejected both directions — `test_auth_login.py`. Seed script creates exactly 2 accounts with independently generated hashes — `test_seed_demo_accounts.py` (6 cases, incl. partial-state idempotency added at unit-test stage). | **PASS (dev-verified)** | None outstanding — fully covered by automated tests; QA may spot-check manually as part of general login testing. |
| **ACRI-66-AC5** | Both personas get identical access to all 4 screens (no restricted/aggregate-only view) | `routes/screens.py` has no persona-conditional branching; identical response shape for both personas via a shared helper — `test_both_personas_get_a_byte_identical_response_shape` (4 screens, parametrized). | **PASS (dev-verified)** | TS-14 (manual/UX): confirm fb-manager sees no visually restricted/aggregate-only variant of any of the 4 (stub) screens in an actual browser render; re-verify once real business logic lands in a future story. |

All 5 ACs: **PASS at the code/automated-test level** per `code-review.json` and `development-verification.json`. QA's remaining work is real-browser/manual validation (TS-13–TS-16, detailed in §7), not re-litigating the automated-test result.

---

## 4. Changed components/files and risk hotspots

**Backend — new (16):** `db/models.py` (User/UserSession/LoginAttempt models, Persona enum), `db/seed.py`, `schemas/__init__.py`, `schemas/auth.py`, `services/auth_service.py`, `middleware/auth.py`, `routes/auth.py`, `routes/screens.py`, `scripts/__init__.py`, `scripts/seed_demo_accounts.py`, `tests/conftest.py`, `tests/test_auth_login.py`, `tests/test_auth_logout.py`, `tests/test_auth_me.py` (added at unit-test stage), `tests/test_auth_session_required.py`, `tests/test_failed_login_alerting.py`, `tests/test_seed_demo_accounts.py`.

**Backend — modified (4 plan-scoped + 2 adjacent/justified):** `main.py` (CORS, `lifespan` startup hook for schema-create + seed, routers wired in), `.env.example` (new seed/session/alert env vars, placeholder values), `pyproject.toml` (mypy file list extended), `README.md`. Adjacent: `requirements.txt` (`bcrypt==4.0.1` explicit pin — see risk hotspot below), `requirements-lock.txt` (regenerated).

**Frontend — new (15):** `lib/api-client.ts`, `lib/auth-context.tsx`, `lib/screens.ts`, `hooks/use-auth.ts`, `components/auth/login-form.tsx` (+ test), `components/auth/require-auth.tsx` (+ test), `components/common/stub-screen.tsx`, `routes/login.tsx`, `routes/risk-dashboard.tsx`, `routes/ingredient-detail.tsx`, `routes/chat-agent.tsx`, `routes/purchase-order-draft.tsx`, `lib/api-client.test.ts`.

**Frontend — modified (4):** `package.json` (new dependency `react-router-dom@^7.18.4`), `App.tsx` (routing/guards), `main.tsx` (`BrowserRouter` + `AuthProvider` wiring), `test/App.test.tsx` (updated bootstrap smoke test).

**Risk hotspots for QA to weight testing effort toward:**
1. **`services/auth_service.py::verify_credentials`** — CR-001 (MINOR, not blocking): unknown-email path skips the bcrypt call while wrong-password path performs one, creating a timing side-channel that could theoretically distinguish "unknown email" from "wrong password" despite an identical 401 message/body. Low practical risk at 2-account POC scale; not something QA can meaningfully black-box test, flagged for awareness only.
2. **`requirements.txt` — `bcrypt==4.0.1` pin** — a real upstream `passlib==1.7.4`/`bcrypt>=4.1` incompatibility was discovered and fixed during implementation (without the pin, every login attempt 500'd). QA should confirm the backend environment actually installs this pinned version (not a newer bcrypt) before testing — a fresh `pip install` without lockfile discipline could silently reintroduce the 500.
3. **Session cookie security posture** — `SESSION_COOKIE_SECURE` defaults `false` pending the still-open AWS/TLS hosting decision (`ARCH-018`). Acceptable for local/POC test environments; QA should not flag this as a defect in this environment, but should confirm it is revisited before any TLS-fronted deployment.
4. **No migration tooling** — schema is created via `Base.metadata.create_all()` at startup, not via Alembic. Not user-visible, but relevant if QA needs to reset/re-seed data (see §6).
5. **Login screen visual design** — authored fresh with no prior wireframe/spec (Confluence Design Document predates auth). QA's UX review of copy/layout (§7) is a first-time design sanity check, not a regression check.

---

## 5. Environment setup, flags, config, seed/test data, accounts, mocks

**Repository layout:** `app/frontend` (React 18 + TS + Vite 5) and `app/backend` (Python 3.12+/FastAPI 0.141.1 + SQLAlchemy 2.0.54 over SQLite).

**Backend setup:**
```
cd app/backend
python -m venv .venv && .venv\Scripts\activate     # or use existing .venv
pip install -r requirements-dev.txt                 # installs the bcrypt==4.0.1-pinned requirements.txt too
uvicorn main:app --reload --port 8000
```
On startup, the backend automatically creates the `users`/`user_sessions`/`login_attempts` tables (`Base.metadata.create_all`) and idempotently seeds the 2 demo accounts from env vars (no-op if they already exist).

**Frontend setup:**
```
cd app
npm install
npm run dev --workspace frontend      # or the workspace's documented dev command; reads VITE_API_URL
```

**Environment variables (all in `app/backend/.env.example`, placeholders only — do not use these values beyond local/POC testing):**
| Var | Purpose | Default / placeholder |
|---|---|---|
| `SEED_KITCHEN_MANAGER_EMAIL` | Demo kitchen-manager login email | `kitchen.manager@example.com` |
| `SEED_KITCHEN_MANAGER_PASSWORD` | Demo kitchen-manager login password | `changeme-not-a-real-secret` (placeholder — replace locally per README/runbook, never commit a real value) |
| `SEED_FB_MANAGER_EMAIL` | Demo fb-manager login email | `fb.manager@example.com` |
| `SEED_FB_MANAGER_PASSWORD` | Demo fb-manager login password | `changeme-also-not-a-real-secret` (placeholder) |
| `SESSION_COOKIE_SECURE` | Whether the session cookie requires HTTPS | `false` (local dev; must become `true` once TLS hosting is decided, `ARCH-018`) |
| `FAILED_LOGIN_ALERT_THRESHOLD` | Failed attempts before WARN alert | `5` |
| `FAILED_LOGIN_ALERT_WINDOW_MINUTES` | Rolling window for the above | `15` |
| Frontend `VITE_API_URL` | Backend base URL | reused, unchanged from scaffold |

**Test/seed accounts (2 fixed personas, no self-registration in v1):**
- `kitchen-manager` — email/password per `SEED_KITCHEN_MANAGER_*` above.
- `fb-manager` — email/password per `SEED_FB_MANAGER_*` above.
Both are provisioned automatically on backend startup, or explicitly via `python -m scripts.seed_demo_accounts` (standalone CLI, idempotent — safe to re-run).

**Mocks/sandboxes:** None required. No third-party/external service integration in this story (no email delivery, no SSO/IdP, no MFA provider). CORS is configured for `FRONTEND_ORIGIN` with `allow_credentials=True` for local cross-origin (`:5173` ↔ `:8000`) cookie flow — QA running frontend and backend on different local ports should confirm this is already satisfied by the default dev configuration and does not need extra setup.

**Accounts/roles for QA:** Only the 2 seeded personas above exist; there is no admin/support account and no way to create additional accounts through the UI in this story (out of scope).

---

## 6. Migration/apply and rollback notes

- **Apply:** Fully automatic — starting the backend process runs `Base.metadata.create_all(engine)` then the idempotent seed step. No manual migration command is required. The same schema-create + seed logic is also available standalone via `python -m scripts.seed_demo_accounts` (e.g., to seed without booting the full ASGI app).
- **No migration tool (Alembic) exists yet** — this is the first story to define real tables, using `create_all()` as an interim mechanism (a carried, disclosed risk, not a defect). QA does not need to run any migration step.
- **Data reset (for QA re-testing from a clean state):** delete the local, gitignored `app.db` SQLite file, then either restart the backend or re-run `python -m scripts.seed_demo_accounts` to recreate the schema and the 2 demo accounts.
- **Rollback:** All changes are additive (new files/tables/one new frontend dependency; small, non-destructive modifications to `main.py`/`App.tsx`/`main.tsx`/`package.json`/`pyproject.toml`/`.env.example`/`README.md`). Reverting this story's commit(s) cleanly restores the prior scaffold state. No irreversible side effects exist (no email sent, no third-party account created, no production secret provisioned — seed credentials are documented POC placeholders).

---

## 7. Required QA scenarios (P0/P1/P2)

**P0 — must pass before this story can be considered QA-validated:**
1. **TS-13 (integration/e2e, AC1+AC2):** In a real browser, visit a protected URL (e.g. `/risk-dashboard`) directly with no prior session → confirm redirect to `/login`. Then log in through the UI with each persona's credentials → confirm navigation to all 4 gated screens (risk dashboard, ingredient detail, Chat Agent, purchase-order draft) with no further redirects, and that the session persists across client-side navigation between them (no re-prompt).
2. **AC3 manual confirmation:** Submit a wrong password and, separately, an unknown email at the login screen → confirm a visible inline error and that no screen becomes reachable (attempt direct navigation to a protected URL afterward too).
3. **AC4 manual confirmation:** Confirm kitchen-manager's credentials do not log in as fb-manager and vice versa.
4. **Logout:** Confirm the logout action ends the session and a subsequent direct visit to any gated screen redirects back to `/login`.

**P1 — should pass, important for release confidence:**
5. **TS-14 (manual, AC5 UX parity):** Confirm fb-manager sees no visually restricted or aggregate-only variant of any of the 4 (currently stub) screens compared to kitchen-manager. Note: re-verify this again once each screen's real business logic lands in its own future story — this pass only validates the auth-gating layer, not eventual per-screen content.
6. **TS-15 (security/manual, non-functional):** Using browser dev tools, inspect the session cookie and confirm `HttpOnly` and `SameSite=Lax` flags are set, and that the cookie is not readable via `document.cookie`.
7. **Cross-browser cookie behavior:** Repeat the login/redirect/session-persistence flow in at least one Chromium-based browser and one non-Chromium browser, since automated tests (pytest `TestClient` / Vitest) do not exercise real browser cookie-jar semantics.
8. **Environment/dependency sanity:** Confirm a fresh backend environment install actually resolves `bcrypt==4.0.1` (per `requirements.txt`/`requirements-lock.txt`) — a login attempt against an unpinned/newer bcrypt would 500 (a real defect class discovered and fixed during development; worth one confirmation pass).

**P2 — good to check, lower risk / cosmetic / accessibility:**
9. **TS-16 (manual, out-of-scope confirmation):** Confirm no MFA step, no self-service "forgot password" link, and no idle-timeout/forced-logout behavior appears anywhere in the login flow (expected absence, not a defect).
10. **Visual/UX review of the login screen:** copy and layout have no prior design source (flagged by Development as authored fresh) — a human sanity check of wording/placement/field-validation UX is appropriate here, not a regression check.
11. **Accessibility spot-check on the login form:** keyboard-only submission, visible focus states, and that the error message is exposed to assistive tech (implemented as `role="alert"` per dev evidence — confirm with a screen reader or accessibility tooling if available).
12. **Malformed-input handling:** submitting an empty email/password (or a value without `@`) should surface a client-side/`422`-derived validation message rather than a raw server error — informal confirmation, not a formal AC.

---

## 8. Known limitations, carried findings, unresolved non-blocking risks

- **CR-001 (MINOR, code-review, not blocking):** `verify_credentials` has a timing-based side channel between "unknown email" (no bcrypt call) and "wrong password" (bcrypt call performed) despite an identical 401 message. Low practical risk at this POC's fixed 2-account scale; recommended hardening (dummy-hash verify on the unknown-email path) tracked as a future story. Not testable meaningfully by manual/black-box QA.
- **CR-002 (SUGGESTION):** `bcrypt==4.0.1` pin is a few minor versions behind current bcrypt releases; tracked for a future `passlib`/`bcrypt` upgrade path once passlib itself supports newer bcrypt.
- **CR-003 (SUGGESTION):** `npm audit --workspace frontend` reports 5 pre-existing vulnerabilities (3 moderate, 1 high, 1 critical) in the vite/vitest/esbuild dev-tooling dependency chain — dev-only, not shipped to the production bundle, pre-dating this story. This story's only new dependency (`react-router-dom`) is clean. Not a functional QA concern but disclosed for completeness.
- **Failed-login handling is WARN-log-only** — no lockout or rate-limiting is implemented for repeated failed attempts (an accepted, authorized resolution for v1, not a gap introduced by this story). QA should not file this as a defect; it is explicitly out of scope for this build (though flagged upstream as an open policy question for a future story).
- **`SESSION_COOKIE_SECURE` defaults `false`** pending the still-open AWS/TLS hosting topology (`ARCH-018`). Correct for local/POC test environments; must be revisited before any TLS-fronted deployment.
- **No migration tooling (Alembic) yet** — `Base.metadata.create_all()` is used as an interim mechanism; recommended before the next schema-changing story, not a defect in this one.
- **`config/project.yaml`'s `development.require_approved_hld/require_approved_lld/require_architecture_validation`** flags still read `true`, unreconciled with `DEC-005`'s bypass. Out of this story's file scope; noted so QA/future automation isn't misled by that config file in isolation.
- **`artifacts/development/acri-66/dev-status.json` is stale** — still shows `status: RUNNING` / `current_stage: project_initialization` and a superseded Node.js/Express `backend_framework_assumption`, despite every subsequent gate artifact (tech-lead-review, code-review, unit-test-report, development-verification, this handoff) recording PASS/COMPLETED against the actual FastAPI implementation. This is a known orchestrator-bookkeeping gap, re-confirmed at every prior stage — not a functional defect, and QA should disregard that file's stage/status fields as authoritative for this story's actual state (the artifacts listed in §1 are authoritative).
- **No initial-credential provisioning mechanism beyond the seed script** exists (no self-registration, no admin UI) — acceptable for this POC's 2 fixed personas; flagged for awareness if the persona set ever grows.
- **Login screen has no prior design/wireframe source** — layout and copy were authored fresh during implementation; treat any UX feedback here as first-pass design input, not a regression.

---

## 9. Development verification commands and results

**Backend** (from `app/backend`, `.venv` active):
| Command | Result |
|---|---|
| `pytest -q` | 52 passed (40 pre-existing/initial + 12 added at unit-test stage), 0 failed, 2 pre-existing unrelated deprecation warnings (Starlette/anyio), exit 0, ~34–35s |
| `ruff check .` | All checks passed |
| `black --check .` | All done, 25 files unchanged |
| `mypy .` | Success: no issues found in 25 source files |

**Frontend** (from `app`):
| Command | Result |
|---|---|
| `npm run test --workspace frontend` | 4 test files, 11 tests, all passed, exit 0, ~2.6–3.3s |
| `npm run lint --workspace frontend` | 0 errors, 1 pre-existing accepted warning (`react-refresh/only-export-components` in `lib/auth-context.tsx`) |
| `npm run typecheck --workspace frontend` | Clean, no errors |
| `npm run format:check --workspace frontend` | All matched files use Prettier code style |
| `npm run build --workspace frontend` | `tsc -b && vite build` succeeded; `dist/` produced (186.03 kB JS / 60.91 kB gzip) |
| `npm audit --workspace frontend` | 5 vulnerabilities (3 moderate, 1 high, 1 critical), all pre-existing in the vite/vitest/esbuild dev-tooling chain; `react-router-dom` (new dependency) clean |

**Manual smoke test** (development-stage, non-QA): `uvicorn main:app` → `curl /health` (200) → `curl -X POST /auth/login` with seeded kitchen-manager credentials (200 + `Set-Cookie: session_token=...; HttpOnly; Path=/; SameSite=lax`) → `curl /screens/risk-dashboard` with that cookie (200, documented response shape). Server stopped and local `app.db` cleaned up afterward.

All results above were independently re-run and confirmed matching at both `code-review.json` (round 1) and `development-verification.json` stages — no discrepancy between claimed and re-run counts at any stage.

---

## 10. QA entry/exit expectations and defect-report fields

**Entry criteria for QA (all met):**
- All 5 preconditions (`requirements-validation.json`, `tech-lead-review.json`, `unit-test-report.md`, `code-review.json`, `development-verification.json`) show `PASS` under the same plan checksum `sha256:e921a607cdfbe1da39afdc31461913c682fb5d4336a4357a9c387ca3b1959fe8`, for this work item (`ACRI-66`) only.
- `implementation-plan.md` and `implementation.md` are present and consistent with the above.
- Environment setup (§5) is reproducible from the checked-in scaffold with no undocumented dependencies.

**Exit criteria for QA (recommended, for QA's own workflow):**
- All P0 scenarios in §7 pass.
- All P1 scenarios in §7 pass, or any failure is triaged and either fixed or explicitly accepted as a known limitation with sign-off.
- P2 scenarios are executed on a best-effort basis; failures are logged but do not block sign-off by themselves.
- Any newly discovered defect is filed using the fields below and linked back to `ACRI-66`.

**Reproducible defect-report fields (recommended template):**
- **Work item:** ACRI-66 (Story-Id US-030)
- **AC / scenario ID affected:** e.g. `ACRI-66-AC3` or `TS-14`
- **Persona used:** kitchen-manager / fb-manager
- **Browser/OS:** (name, version)
- **Steps to reproduce:** exact URL(s), input values (redact real credentials if changed from seed defaults), click sequence
- **Expected result:** (cite the specific AC wording from §3)
- **Actual result:** (screenshot/console/network trace if available; note any HTTP status/response body seen in dev tools)
- **Session/cookie state at time of failure:** logged in / logged out / cookie present-but-invalid (check via dev tools per TS-15's method)
- **Backend log line(s) if accessible:** (e.g. any `failed_login_alert` WARN entry, matching timestamp)
- **Severity/priority suggestion:** referencing the P0/P1/P2 scenario it violates
- **Related known limitation?:** cross-check against §8 before filing as new

## Post-handoff annotation (2026-09-18)

A cross-cutting visual-design pass, done while implementing `ACRI-61` per direct human instruction ("continue building UI"), added CSS/className-only styling to four files this story owns: `routes/login.tsx`, `components/auth/login-form.tsx`, `components/common/stub-screen.tsx`, and `App.tsx` (now wrapped in a new shared `components/common/app-shell.tsx` top-bar/nav component providing sign-in-aware navigation across all 5 screens). No DOM structure, text content, role/label attributes, or business logic changed in any of these files — this story's own tests (`login-form.test.tsx`, `require-auth.test.tsx`, `App.test.tsx`) were re-run afterward and still pass, independently re-verified at `ACRI-61`'s code-review stage (`artifacts/development/acri-61/code-review.json`). This does not reopen this work item's `READY_FOR_QA` status. QA should expect the login screen and the 4 stub screens to now appear inside a styled top navigation bar, rather than as bare unstyled HTML — this is cosmetic only and does not change any of the AC1–AC5 behavior already validated above.

Development status: READY_FOR_QA
