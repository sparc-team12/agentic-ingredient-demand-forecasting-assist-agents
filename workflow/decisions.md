# Decision Log

Records every material human decision made during a product discovery workflow — one `## DEC-XXX` entry per decision, IDs sequential across all workflows. Written by the orchestrator only after a human has actually made the decision at a gate; never fabricated, never attributed to an unnamed person.

Entry format:

```markdown
## DEC-XXX — <short title>

Decision:
<what was decided>

Decided by:
<human stakeholder name/role as given, or "human (unspecified)" if not stated>

Reason:
<why>

Alternatives considered:
<if any>

Impact:
<what downstream artifacts/agents are affected>

Related:
<artifact IDs, e.g. ARCH-003, FEAT-007, RISK-004>
```

## DEC-001 — Solution Architecture (overview) approved at Architecture Suite Approval gate

Decision:
`artifacts/architecture/solution-architecture-overview.md` is APPROVED as submitted. This document carries no open `[SECURITY REVIEW REQUIRED]` markers. Its open `[TBD]` items — backend API framework/language, state-management library, build tooling, and the AWS compute service/topology (all inherited, unresolved-upstream items from `artifacts/architecture/solution-architecture.md`), the absent `docs/04-design/` wireframes/process-flow page, and the carried-forward ARCH-016-vs-PRD "no login" Non-Goal discrepancy — are accepted as known open items to be resolved in a later stage, not as blockers to publishing this narrative/stakeholder-facing document now.

Decided by:
human (unspecified name; account sparc.team12@experionglobal.com), via blanket "APPROVE" message during the `solution-architecture-publish-resume-agent` run on 2026-09-17.

Reason:
No open security-review marker exists on this document; remaining items are pre-existing `[TBD]` scoping gaps already disclosed in the document's own Gaps section and inherited from the approved `solution-architecture.md` engineering artifact (Gate ARCH-1 Round 2). The human's blanket APPROVE is sufficient to clear a document with no unaddressed `[SECURITY REVIEW REQUIRED]` marker.

Alternatives considered:
None offered by the human; no `APPROVE_WITH_CHANGES` or `STOP` was given for this document.

Impact:
`solution-architecture-overview.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. Document is now eligible for publication to Confluence via `.claude/skills/confluence-publish/SKILL.md`.

Related:
solution-architecture-overview.md (Agent: solution_architecture_overview)

## DEC-002 — Technology Stack approved at Architecture Suite Approval gate

Decision:
`artifacts/architecture/tech-stack.md` is APPROVED as submitted. This document carries no `[SECURITY REVIEW REQUIRED]` markers. Its open `[TBD]` items (frontend framework version/state-management/build tooling; backend API framework/language and runtime choices; API protocol; IAM session/token protocol and identity provider; observability/logging service; entire Security Tooling table; CI/CD tooling; entire Infrastructure-as-Code table; issue tracker/team-communication tooling) are accepted as known open items inherited from unresolved upstream architecture decisions (`solution-architecture.md`, ARCH-002/ARCH-018), not as blockers to publishing this document now.

Decided by:
human (unspecified name; account sparc.team12@experionglobal.com), via blanket "APPROVE" message during the `solution-architecture-publish-resume-agent` run on 2026-09-17.

Reason:
No open security-review marker exists on this document; remaining items are pre-existing `[TBD]` technology-choice gaps already disclosed in the document's own Summary section. The human's blanket APPROVE is sufficient to clear a document with no unaddressed `[SECURITY REVIEW REQUIRED]` marker.

Alternatives considered:
None offered by the human; no `APPROVE_WITH_CHANGES` or `STOP` was given for this document.

Impact:
`tech-stack.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. Document is now eligible for publication to Confluence via `.claude/skills/confluence-publish/SKILL.md`.

Related:
tech-stack.md (Agent: solution_tech_stack)

## DEC-003 — Security Architecture approved at Architecture Suite Approval gate (itemized clearing of MFA marker and two deferred items)

Decision:
`artifacts/architecture/security-architecture.md` is APPROVED. Unlike DEC-001/DEC-002, this was **not** a blanket approval — each of the three outstanding items was individually answered:

1. **§3 MFA marker (`[SECURITY REVIEW REQUIRED]`):** No MFA is required. Simple email + password login is accepted as sufficient for v1. This gap is accepted, not mitigated further.
2. **§3 marker 2 — ARCH-016 login vs. PRD "no login" Non-Goal:** Login remains required (ARCH-016 confirmed, not walked back). Formally recorded here as a deferral: the human will amend the PRD separately, in a future, dedicated PRD-amendment run, to reconcile the "no login" Non-Goal with the now-confirmed login requirement. Approval of this document is explicitly **not** blocked on that PRD amendment landing first.
3. **§11 marker 6 — login-email vs. "no personal/customer/payment data" Non-Goal:** Accepted as-is. The human does not consider a login email address to constitute a conflict with the PRD's Non-Goal requiring further mitigation; no additional PII control is required beyond what the document already describes.

The one item from DEC-001/DEC-002 that does not apply here: this document also carries several `[TBD]` items (session/token mechanism specifics, password-hashing library/version, AWS security-group configuration, failed-login alert threshold, and the full list of infrastructure/tooling gaps already disclosed in the document's own Summary section) — these remain open technical `[TBD]`s, not `[SECURITY REVIEW REQUIRED]` markers, and are accepted as known open items carried into a later engineering stage, consistent with the treatment given to the same category of items in DEC-001 and DEC-002.

Decided by:
sparc.team12@experionglobal.com, communicated to the coordinating orchestrator in the main session and relayed to this agent on 2026-09-17, itemized per the three specific outstanding markers (not a blanket approval).

Reason:
Per this agent's hard rule, a blanket approval cannot clear a document with an unaddressed `[SECURITY REVIEW REQUIRED]` marker — each open marker requires its own explicit answer. All three outstanding items (the MFA marker and the two "acknowledged and deferred" items previously recorded only as in-document narrative, not as a recorded gate decision) have now been individually answered by the human, satisfying that requirement.

Alternatives considered:
None offered; no `APPROVE_WITH_CHANGES` or `STOP` was given for this document.

Impact:
`security-architecture.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. Document is now eligible for publication to Confluence via `.claude/skills/confluence-publish/SKILL.md`, pending a fresh search-before-create check and a separate Gate 5 human confirmation before any `createConfluencePage` call. Note: the document's own body content (§3, §11, and the "Summary of `[SECURITY REVIEW REQUIRED]` markers" section) still narrates the MFA item as "carried forward... still open" and the two deferred items as unresolved narrative — this agent does not rewrite that body content (out of scope per this agent's hard rules; only the metadata block was updated). A future pass by `solution-security-architecture-agent` should reconcile the body narrative with this DEC-003 record.

Related:
security-architecture.md (Agent: solution_security_architecture)

## DEC-004 — PRD superseded by Jira user stories as requirements source; login model resolved to per-user

Decision:
During `/generate-architecture`, `solution-lld-agent` reported `BLOCKED_FOR_DEVELOPMENT`: the approved architecture suite (`solution-architecture.md`, `security-architecture.md`, `tech-stack.md`, `high-level-design.md`) was built against PRD v1.1, while the PRD currently in the repo (`docs/01-prd/prd-ingredient-demand-forecasting.md`) is v1.6 — six revisions ahead, including a direct contradiction: approved `ARCH-016` mandates a single shared login, while PRD v1.6's `REQ-043`/`REQ-044` require per-user login. `REQ-037`–`REQ-044` (Data Setup screens, Auth) also had zero architecture/HLD coverage.

Presented with this conflict, the human directed: **do not refer to the PRD; only refer to the Jira user stories** (project `ACRI`, 30 stories, `ACRI-36`–`ACRI-66`) as the requirements source going forward for architecture/HLD/LLD and development. This resolves the login conflict in favor of **per-user login**, matching Jira story `ACRI-66` (Story-Id US-030, "[Auth] Kitchen manager or F&B manager logs in with their own credentials before reaching any screen") — `ARCH-016`'s single-shared-login decision is superseded for this build. Data Setup coverage is grounded in `ACRI-59`–`ACRI-63` (epic `ACRI-35`), and Auth in `ACRI-65`/`ACRI-66` (epic `ACRI-65`).

Decided by:
sparc.team12@experionglobal.com, given directly to the orchestrating session on 2026-09-18, in response to the LLD blocker above.

Reason:
The Jira user stories are the actual, current, operative scope for development (confirmed live via Jira MCP, all under project ACRI with `order-XXX` build-sequence labels); the PRD in the repo has drifted through six unreconciled revisions and is no longer being treated as the controlling document for this build. Continuing to gate development on full PRD reconciliation would block all 29+ stories indefinitely over a documentation-sync issue the human has explicitly chosen not to spend further cycles on for this POC.

Alternatives considered:
Full architecture-suite revision cycle against PRD v1.6 (re-running `solution-architect-agent` end to end) — offered to the human as the "Recommended" option; the human chose the override instead.

Impact:
`solution-architecture.md` (`ARCH-016`), `security-architecture.md`, `tech-stack.md`, `high-level-design.md`, and `low-level-design.md` are being amended to add Data Setup/Auth coverage grounded in the Jira stories and to reflect per-user login. The PRD (`docs/01-prd/`) is no longer treated as an input to this workflow from this point forward. Any future reconciliation between the PRD and the Jira stories remains open and unassigned.

Related:
ARCH-016, ACRI-66, ACRI-35, low-level-design.md (Agent: solution_lld)

## DEC-005 — Explicit bypass of the HLD/LLD/architecture-validation development gate; remaining tech-stack [TBD] items resolved for scaffold

Decision:
The human directed: bypass the Architecture/HLD/LLD Approval gate entirely for development of the `ACRI` Jira stories, and build the application directly from (a) the approved Confluence "Technology Stack" page (id `5885657157`, Status: APPROVED) and (b) the approved Confluence "Design Document - Agentic Ingredient Demand Forecasting Assistant" page (id `5885722653`, Status: Approved), grounded in the Jira user stories per DEC-004. This supersedes `.claude/agents/dev-orchestrator-agent.md`'s entry-contract requirement for an approved `high-level-design.md`, `low-level-design.md`, and `architecture-validation.json` — those are not being produced/approved for this build. This is the same category of override already recorded informally in `artifacts/development/acri-66/dev-status.json`'s `hld_lld_gate` field for that one story; this decision extends the same override to every `ACRI` story going forward and records it centrally.

The approved Technology Stack document leaves several implementation-level choices `[TBD — confirm with stakeholder]` that block `dev-scaffold-agent` from producing a valid manifest (its hard rule: stop with `BLOCKED_STACK_DECISION` rather than silently pick a popular tool). Since the human has directed proceeding without further architecture engagement, these are resolved here as build decisions for this development effort, consistent with the precedent already set independently in `artifacts/development/acri-66/dev-status.json`:

- Frontend build tooling: **Vite** (React + TypeScript, matching the already-approved React choice).
- Backend framework/language: **Python + FastAPI** (per explicit human direction, given directly to the orchestrating session on 2026-09-18: "do the backend using fastapi" — overrides this decision's earlier Node.js/Express draft, which was never scaffolded).
- API protocol: **REST/JSON over HTTP** (FastAPI's native style, with Pydantic request/response schemas).
- Persistence driver: **SQLAlchemy ORM over SQLite** (standard FastAPI pairing; matches the already-approved SQLite storage decision).
- AuthN/session mechanism: **per-user email+password login** (per DEC-004/ACRI-66 — supersedes `ARCH-016`'s shared-login model), `passlib[bcrypt]` password hashing, opaque server-side session token (256-bit, crypto-random) in an httpOnly, sameSite=lax cookie, backed by a `sessions` table in SQLite. No MFA, no self-service password reset, no session idle-timeout (per ACRI-66 AC/out-of-scope).
- Test tooling: **Vitest** (frontend), **pytest** (backend).
- Package management: **npm** (frontend), **pip + requirements.txt** (backend, kept simple for a POC rather than introducing Poetry/uv).
- Repository layout: `app/frontend` (React/Vite/TS) and `app/backend` (Python/FastAPI), single repo.
- CI: minimal GitHub Actions workflow (lint, typecheck, test, build for frontend; lint, test for backend) — GitHub already evidenced as this repo's host.

These are documented as this build's resolution of open `[TBD]` items, not as a re-approval of the Technology Stack document itself (that document remains APPROVED as originally written; these are additive implementation choices made under this override, same treatment as ACRI-66's own `backend_framework_assumption`/`session_mechanism_assumption` fields).

Decided by:
sparc.team12@experionglobal.com, given directly to the orchestrating session on 2026-09-18 ("bypass this and create this app using the stack mentioned and ui").

Reason:
The human wants working software built now rather than spending further cycles on a formal HLD/LLD/validation cycle for a POC; the Technology Stack and Design Document are both already human-approved on Confluence and give sufficient grounding for a reasonable, consistent implementation, with only genuinely-undecided tooling choices (not product/security decisions) resolved here.

Alternatives considered:
Completing the Architecture Suite/HLD/LLD workflow first (offered as "Recommended" at two separate points in this session); the human chose the bypass both times.

Impact:
`dev-orchestrator-agent`'s entry-contract gate is not enforced for this workflow going forward. Every `ACRI` story's `dev-status.json` must record this override in its `sources`/`hld_lld_gate` field, same as `ACRI-66`, so this is never silently mistaken for a normal gated build. `dev-scaffold-agent` is dispatched with the technology resolutions above supplied explicitly (not invented by that agent itself).

Related:
ACRI-66, DEC-004, tech-stack.md, Design Document (Confluence 5885722653)

## DEC-006 — Chat Agent backed by a real hosted LLM API (Google Gemini), not the self-hosted Gemma 4B named in architecture

Decision:
`solution-architecture.md` (`ARCH-015`) approved a self-hosted, open-source Gemma 4B model specifically to keep the Chat Agent's LLM call inside the AWS boundary with zero third-party network dependency (`ARCH-017`), addressing a data-confidentiality concern about supplier cost data leaving the application. Self-hosting an actual Gemma model is not feasible in this development environment (no GPU/model-serving infrastructure). The human directed calling a real hosted LLM API instead. Initially recorded as the Anthropic Claude API (this DEC-006 entry, originally); superseded the same day by explicit human direction to use the **Google Gemini API** instead ("let's place gemini api and use any llm").

Model: `gemini-2.5-flash` (fast/cheap tier, matching the "a few seconds" response-time requirement — `ACRI-45` AC4, `ACRI-49` AC2), via the `google-genai` Python SDK. Grounding rule (`ARCH-009`'s "narrate only computed figures" requirement, and Jira `ACRI-45` AC3/"never independently estimated") is unchanged by the provider swap: the LLM is used ONLY for (a) extracting structured intent/parameters from free text and (b) phrasing a response from figures already computed by the deterministic engine (`ARCH-004`) — it is never given latitude to compute or invent a number itself. The API key is read from an environment variable (`GEMINI_API_KEY`), never hardcoded or committed — the human adds it directly to `app/backend/.env` themselves, not via chat. Automated tests mock the API call and never hit the real network.

Decided by:
sparc.team12@experionglobal.com, given directly to the orchestrating session on 2026-09-18. First asked how to implement Chat Agent NL understanding without a feasible self-hosted model (chose "call a real hosted LLM API" over rule-based parsing); provider then specified as Gemini in a follow-up message the same day, superseding the Claude API choice recorded earlier in this same entry.

Reason:
A real LLM API call is the most direct way to get working NL parsing/phrasing without standing up model-serving infrastructure this POC environment doesn't have. Gemini was named directly by the human as the preferred provider.

Alternatives considered:
Rule-based/keyword-pattern parsing (offered as "Recommended" — zero external dependency, trivially satisfies the "never invent figures" rule) — not chosen. Anthropic Claude API — the human's initial choice, superseded by the Gemini direction before any Claude-specific code was written.

Impact:
`ARCH-015`/`ARCH-017`'s self-hosted/zero-third-party posture is superseded for the Chat Agent specifically (not for any other component) — this is a real external network dependency, contradicting `ARCH-017`'s "zero external, third-party network dependencies" statement for this one feature. `security-architecture.md`'s data-confidentiality rationale for self-hosting no longer holds for whatever is sent to the LLM — the app must not send supplier cost/pricing data to it, only the already-computed, already-displayed figures needed for narration (dish names, dates, quantities, INR amounts already shown on-screen) — same class of data the manager already sees, nothing additional. Requires `GEMINI_API_KEY` to be configured wherever this app runs; documented in `.env.example` as a required variable with no default/fake value (unlike the demo login credentials).

Related:
ARCH-009, ARCH-015, ARCH-017, ACRI-45, ACRI-49
