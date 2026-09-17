---
name: product-discovery
description: Master orchestration procedure for the human-gated AI product discovery & planning workflow. Invoked by the /product-plan, /orchestrate, /research, /features, /stories, /architecture, /uiux, /estimate, /risk, /test-strategy, /prd, /review, /status, /publish, /retry, /skip, and /generate-architecture commands. Coordinates prd-agent and the specialist subagents in .claude/agents/ (including test-strategy-agent and the Architecture Suite specialists), maintains workflow/status.json and workflow/events.jsonl, enforces human approval gates, and delegates validation to the validation-review skill and Confluence publishing to the confluence-publish skill.
---

# Product Discovery & Planning — Orchestration Procedure

This skill is the control-plane logic for `orchestrator-agent` (see `.claude/agents/orchestrator-agent.md`) — the single canonical orchestrator for this repository. Every command in `.claude/commands/` delegates here with a `mode` and arguments. Follow this procedure exactly — do not skip gates, do not fabricate approvals, do not publish without explicit confirmation.

Governing principle (do not violate): **AI accelerates product discovery and SDLC planning; humans remain the decision authority for requirements, architecture, estimates, risk acceptance, and publication.** When in doubt between more autonomy and a human checkpoint, choose the checkpoint.

## 0. Files this skill owns

- `workflow/status.json` — single source of truth. This skill is the only writer. Read-modify-write atomically: read current content, compute the new object in full, write the whole file back (never hand-edit with partial patches that could race).
- `workflow/events.jsonl` — append-only audit log, one JSON object per line, newline-terminated.
- `workflow/decisions.md` — append-only human decision log, one `## DEC-XXX` section per decision.
- `workflow/metrics.json` — lightweight observability (timestamps, durations, status counts). Never invent token/cost numbers this environment does not expose.
- `config/project.yaml` — Confluence site/space/parent page, Jira project target, and workflow toggles. Read, don't silently rewrite; if the human changes it, respect the new values on next read.

Specialist input/output artifact contracts live in each `.claude/agents/*.md` file — this skill dispatches to them but does not duplicate their contracts here.

## 1. status.json schema

```json
{
  "schemaVersion": 1,
  "activeWorkflowId": "WF-2026-001",
  "projects": {
    "ingredient-demand-forecasting-assistant": {
      "name": "Ingredient Demand Forecasting Assistant",
      "slug": "ingredient-demand-forecasting-assistant",
      "confluenceFolderId": "...",
      "confluenceFolderUrl": "...",
      "jiraProjectKey": "...",
      "jiraProjectName": "...",
      "jiraProjectConfirmedAt": "ISO-8601",
      "createdAt": "ISO-8601",
      "workflowIds": ["WF-2026-001"]
    }
  },
  "workflows": {
    "WF-2026-001": {
      "workflowId": "WF-2026-001",
      "workflowName": "...",
      "projectSlug": "ingredient-demand-forecasting-assistant",
      "createdAt": "ISO-8601",
      "updatedAt": "ISO-8601",
      "overallStatus": "WAITING_FOR_HUMAN",
      "currentGate": "REQUIREMENTS_APPROVAL",
      "humanApproval": {
        "required": true,
        "status": "PENDING",
        "requestedAt": "ISO-8601",
        "approvedAt": null,
        "approvedBy": null,
        "decision": null
      },
      "agents": {
        "prd_agent": { "status": "COMPLETED", "startedAt": "...", "completedAt": "...", "task": "...", "output": "artifacts/prd/prd-<slug>.md", "summary": "...", "errors": [], "revisionCount": 0 },
        "research_requirements": { "status": "COMPLETED", "startedAt": "...", "completedAt": "...", "task": "...", "output": "artifacts/research/requirements-baseline.md", "summary": "dispatched by the orchestrator whenever prd_agent flagged a specific, scoped research gap mid-interview; result handed back to prd_agent — never re-run speculatively", "errors": [], "revisionCount": 0 },
        "feature_analyst": { "status": "NOT_STARTED" },
        "solution_architect": { "status": "NOT_STARTED" },
        "uiux_designer": { "status": "NOT_STARTED" },
        "user_story_analyst": { "status": "NOT_STARTED", "summary": "dispatched after feature_analyst, solution_architect, and uiux_designer all complete and clear Gate 2" },
        "estimation_cost": { "status": "NOT_STARTED", "summary": "dispatched after user_story_analyst clears Gate 3 — its input includes user-stories.md" },
        "risk_compliance": { "status": "NOT_STARTED", "summary": "dispatched after estimation_cost completes (its contract requires the estimate)" },
        "test_strategy": { "status": "NOT_STARTED", "summary": "dispatched last, after Gate 4 — by now feature spec, stories, architecture, UI/UX spec, and risk register all exist" }
      },
      "artifacts": [],
      "decisions": [],
      "openQuestions": [],
      "confluence": { "site": null, "space": null, "parentPageId": null, "pages": [] },
      "jira": { "site": null, "projectKey": null, "issues": [] },
      "events": []
    }
  }
}
```

Valid statuses (workflow-level and per-agent): `NOT_STARTED, QUEUED, RUNNING, WAITING_FOR_HUMAN, BLOCKED, NEEDS_REVISION, COMPLETED, FAILED, SKIPPED, APPROVED, PUBLISHED`.

`currentGate` also includes `PROJECT_IDENTIFICATION` (Gate 0b, before `REQUIREMENTS_APPROVAL`) — see §1a.

Workflow ID format: `WF-<current-year>-<3-digit-sequence>`, sequence scoped per year, computed from the highest existing sequence in `workflows` for that year (start at 001).

## 1a. Project registry

`projects` is a top-level map, siblings with `workflows`, keyed by a project slug (kebab-case of the project name). Every workflow's `projectSlug` points into it. Resolve/create an entry **before** minting a workflow ID (Gate 0b — see `orchestrator-agent.md`'s "Project identification and publish destinations"). Each entry has two independent halves, either of which can be present without the other:

**Confluence folder:**
- **New project:** ask the human for the folder name (never derive it), search-before-create under `confluence.parent_page` to rule out an accidental duplicate, create the Confluence folder page on confirmation, and set `confluenceFolderId`/`confluenceFolderUrl` on the entry.
- **Continuation:** look up by name/slug in `projects` first; if not found, search Confluence directly under `confluence.parent_page` before concluding no folder exists (one created outside this registry is still real) — if found this way, backfill the entry so future lookups don't repeat the search.
- Every Confluence publish in this workflow (§8) uses this project's `confluenceFolderId` as `ParentPage` — never `confluence.parent_page` directly, and never another project's folder.
- If `confluence.space`/`confluence.parent_page` are blank, skip this half entirely (same rule as every other Confluence step) and proceed without a project folder — publishing is simply unavailable until configured.

**Jira project (destination for user stories):**
- If `jira.enabled` is `false`, skip this half — story publication to Jira is unavailable until configured.
- **Continuation:** if `jiraProjectKey` is already recorded, don't trust it silently — re-verify it via `getVisibleJiraProjects` and require the human to explicitly re-confirm it (or name a different project) for this workflow before using it.
- **New (or unrecorded):** call `getVisibleJiraProjects`, offer `jira.project_key` from `config/project.yaml` as a suggested default if set, but require explicit human confirmation regardless — a configured value is a suggestion, never an approval. Record the confirmed `jiraProjectKey`/`jiraProjectName`/`jiraProjectConfirmedAt` on the entry.
- This confirmation is separate from, and precedes, the per-issue create/update confirmation in §8 — confirming the destination project is not the same decision as approving the specific issues going into it.

Every write to `status.json` also appends the corresponding line(s) to `workflow/events.jsonl`, e.g.:
```json
{"timestamp":"...","workflowId":"WF-2026-001","agent":"research_requirements","event":"STARTED","message":"..."}
{"timestamp":"...","workflowId":"WF-2026-001","event":"HUMAN_GATE","gate":"REQUIREMENTS_APPROVAL","status":"PENDING"}
```

Update `status.json` (and log an event) after: workflow creation, agent dispatch, agent start, agent completion, agent failure, human question, human response, gate approval, gate rejection, revision request, validation result, Confluence publication.

## 2. Dispatch order and parallelism

```
[GATE 0b: PROJECT_IDENTIFICATION]  <- Confluence: new project (ask folder name, create it) or
        |                             continuation (resolve from projects registry or Confluence
        |                             search); Jira: confirm the destination project with the human
        |                             (never trust a configured default silently) — §1a
        |
prd_agent (interviews the human; flags research needs to the orchestrator as gaps appear —
           never dispatches research_requirements itself; kept narrow/token-efficient)
        |
   orchestrator dispatches research_requirements per flagged need, loops result back to prd_agent
        |
   [GATE 1: REQUIREMENTS_APPROVAL]  <- presents prd_agent's Confirmed PRD
        |
   orchestrator publishes "PRD - <Project Name>" to Confluence, under this workflow's project
   folder (its normal publish point, not an "early/optional" extra — skipped only if
   confluence.space/parent_page are unconfigured; own CREATE-vs-UPDATE confirmation)
        |
   +--------+--------+
   |                 |
feature_analyst   solution_architect     <- both need only the approved PRD, run in parallel
   |
   +---> uiux_designer                   <- starts once feature_analyst completes (needs the feature breakdown)
        |
   [GATE 2: FEATURE_ARCHITECTURE_UIUX_REVIEW]  <- all three together
        |
   orchestrator offers to publish feature-specification.md / solution-architecture.md /
   ui-ux-specification.md to Confluence, each its own page, each its own confirmation
        |
user_story_analyst   <- given the approved PRD + feature spec + architecture + UI/UX spec
        |
   [GATE 3: USER_STORIES_REVIEW]  <- includes the proposed US-XXX -> Jira issue-type mapping
        |
   orchestrator publishes stories to JIRA (not Confluence) — search-before-create, own confirmation
        |
estimation_cost   <- given PRD + feature spec + architecture + UI/UX spec + user-stories.md
        |
risk_compliance   <- runs after estimation_cost (its contract requires the estimate)
        |
   [GATE 4: ESTIMATE_RISK_REVIEW]
        |
   orchestrator offers to publish estimation-cost-analysis.md / risk-register.md to Confluence,
   each its own page, each its own confirmation
        |
test_strategy   <- by now PRD + feature spec + stories + architecture + UI/UX spec + risk register all exist
        |
   [GATE 5: TEST_STRATEGY_REVIEW]
        |
   orchestrator offers to publish test-strategy.md to Confluence, its own confirmation
        |
   VALIDATION (consistency / completeness / feasibility / quality-security)
        |
   PRD ASSEMBLY + traceability matrix (now includes US-XXX ids and their Jira issue keys/URLs)
        |
   [GATE 6: FINAL_PRD_APPROVAL — requires literal "APPROVE_AND_PUBLISH"]
        |
   [GATE 7: CONFLUENCE_PUBLICATION — requires explicit per-page confirmation; updates the "PRD - <Project Name>"
   page in place to add Executive Summary/Traceability Matrix/Decision Log rather than creating a new page]
```

Dispatch each specialist by invoking its agent definition in `.claude/agents/` with only the artifact paths it needs (per its input contract, plus — for `user_story_analyst` only — the architecture and UI/UX documents as additional context per explicit product direction, without editing that agent's own file) — never the full conversation or unrelated artifacts. `feature_analyst` and `solution_architect` may run concurrently since neither depends on the other's output; do not run more agents concurrently than `config/project.yaml`'s `workflow.max_parallel_agents`. Every named gate above reviews a batch's *content*; each individual Confluence page or Jira issue write still requires its own explicit confirmation at write time — never treat gate approval alone as publish approval. Every Confluence page published anywhere in this diagram is titled `<Document Type> - <Project Name>` per the naming convention in `orchestrator-agent.md`, and lands under this workflow's project folder (§1a) — never a bare "PRD" folder shared across projects.

## 3. Modes (what each command passes in)

- **FULL** (`/product-plan <requirement>`): resolve the project and Confluence folder first (Gate 0b, §1a), create a new workflow recording `projectSlug`, dispatch `prd_agent` with the raw input as given (free-text conversation, ticket, or detailed brief — whatever shape it arrives in), let it interview the human and flag `research_requirements` needs to you as it hits gaps, stop at Gate 1 once `prd_agent` hands back a `Confirmed` PRD. On resume after approval, continue the full chain through Gate 7.
- **RESUME** (`/product-plan --resume <workflow-id>`): read `status.json` for that workflow, determine `currentGate`/`overallStatus`, and continue from exactly that point — never re-run a `COMPLETED` agent whose artifact still exists and is still the approved input for the next step.
- **ORCHESTRATE_ONLY** (`/orchestrate --only <agent1,agent2,...>` or `/product-plan --agents ...`): run exactly the named agents (in correct dependency order per §2), reusing existing upstream artifacts, still enforcing any gate that sits between the named agents and their inputs/outputs.
- **SINGLE_AGENT** (`/research <requirement>`, `/features <workflow-id>`, `/stories <workflow-id>`, `/architecture <workflow-id>`, `/uiux <workflow-id>`, `/estimate <workflow-id>`, `/risk <workflow-id>`, `/test-strategy <workflow-id>`): run one specialist directly.
  - `/research` with no existing workflow-id creates a new workflow.
  - All others require a `workflow-id` and must refuse to run if their required upstream artifact is missing, or exists but is not yet human-approved at the relevant gate — explain what's missing/unapproved instead of proceeding, per the dependency order in §2 (e.g. `/stories` requires Gate 2 `APPROVED`; `/estimate` requires Gate 3 `APPROVED` and reads `user-stories.md`; `/risk` requires `estimation-cost-analysis.md` to exist; `/test-strategy` requires Gate 4 `APPROVED` plus `user-stories.md`, since it reads the full set — PRD, feature spec, stories, architecture, UI/UX spec, and risk register).
- **REVIEW** (`/review <workflow-id>`): run the Validation procedure (§6) against whatever artifacts currently exist and report findings; does not advance any gate by itself.
- **STATUS** (`/status [workflow-id]`): print a concise human-readable rendering of `status.json` for the given workflow, or a list of all workflows if none given.
- **PRD** (`/prd <workflow-id>`): assemble the final PRD package (§7) — only valid once Gate 5 (Test Strategy Review) is `APPROVED`.
- **PUBLISH** (`/publish <workflow-id>`): run the Confluence publication procedure (§8) for the final package — only valid once Gate 6 has recorded `APPROVE_AND_PUBLISH`. (Individual-artifact Confluence publishes and the Jira story publish happen inline in the pipeline, right after Gates 1/2/4/5 — see §2 and §8.)
- **RETRY** (`/retry <workflow-id> <agent>`): reset that agent's status to `QUEUED`, increment `revisionCount`, re-dispatch it with the same inputs.
- **SKIP** (`/skip <workflow-id> <agent>`): mark `SKIPPED` only after explicit human confirmation; first explain which downstream agents/gates depend on this agent's output and what will be missing from the final PRD if skipped.
- **GENERATE_ARCHITECTURE** (`/generate-architecture [workflow-id]`): run the Architecture Suite workflow (§7b) end to end — resolve PRD, `ARCH-XXX` generation/approval, the three-document suite, validation, Architecture Suite Approval gate, publish. Independent of the discovery pipeline above; usable against a standalone Shape-B PRD project. The `workflow-id` argument is optional, only needed if this project also runs the discovery pipeline's multi-workflow tracking.

## 4. Human gates — exact behavior

At every gate: present what was produced, list unresolved questions/risks/contradictions, then stop and wait. Do not proceed on an assumed or implied approval.

- **Gate 0 — Intake**: after parsing the human's request, restate your understanding in a few sentences (problem, scope hints, any constraints/documents/Jira-Confluence references given) and ask for anything critical that's missing before dispatching `prd_agent`.
- **Gate 0b — Project Identification**: ask whether this is a new project or a continuation of an existing one, resolve/create the Confluence project folder per §1a, **and** confirm the Jira destination project stories will later be created in (never trusting `jira.project_key` silently, even when set) — record `projectSlug` on the workflow before minting the workflow ID and before dispatching `prd_agent`. Each half (Confluence/Jira) is skipped only if that system isn't configured at all.
- **Gate 1 — Requirements Approval**: present the `Confirmed` PRD `prd_agent` produced (its Requirements, Research Context, Assumptions, and Open Questions sections already carry the research findings and confidence notes). Require exactly one of `APPROVE`, `REQUEST_CHANGES`, `PROVIDE_CLARIFICATION`, `STOP`. On `REQUEST_CHANGES`/`PROVIDE_CLARIFICATION`, re-run `prd_agent` with the human's input (amendment flow) and increment `revisionCount`. On `STOP`, halt the workflow and set `overallStatus: BLOCKED`. On `APPROVE`, publish the PRD to Confluence (own CREATE-vs-UPDATE confirmation at write time — see §8) before dispatching `feature_analyst`/`solution_architect`.
- **Gate 2 — Feature/Architecture/UI-UX Review**: after `feature_analyst`, `solution_architect`, and `uiux_designer` all complete, present a concise cross-domain summary (major features, architecture summary, major UI/UX flows, dependencies, any contradictions found, open decisions). Require `APPROVE` / `APPROVE_WITH_CHANGES` (route back to the relevant specialist, re-present in full) / `STOP`. On approval, offer each document's Confluence publish individually before dispatching `user_story_analyst`.
- **Gate 3 — User Stories Review**: after `user_story_analyst` completes, present the drafted personas/journeys/stories, unmet feature traces, and the proposed `US-XXX` → Jira issue-type mapping. Require `APPROVE` / `APPROVE_WITH_CHANGES` / `STOP`. On approval, publish the stories to the Jira project already confirmed at Gate 0b (§8) before dispatching `estimation_cost` — the create/update list shown at write time re-displays that destination, it doesn't re-decide it.
- **Gate 4 — Estimate/Risk Review**: after `estimation_cost` then `risk_compliance` complete, present effort/timeline/cost ranges, major risks, security/compliance concerns, and high-impact assumptions. Require approval before dispatching `test_strategy`. On approval, offer each document's Confluence publish individually.
- **Gate 5 — Test Strategy Review**: after `test_strategy` completes, present the document. Require approval before PRD assembly. On approval, offer its Confluence publish.
- **Gate 6 — Final PRD Approval**: present the assembled PRD package and validation findings together. Require the literal string `APPROVE_AND_PUBLISH`. Any other response stops publication (it does not have to stop the workflow — the human may still want the assembled PRD without publishing).
- **Gate 7 — Confluence Publication**: before calling any write tool, show target site/space/parent page, the exact page titles to be created/updated, whether each is CREATE or UPDATE (per §8 existence check), and flag anything destructive (an UPDATE that would replace existing content). Require explicit confirmation. Never overwrite an existing page without it.

None of Gates 1–5 approving a batch's content is itself publish approval — each individual Confluence page or Jira issue write still needs its own explicit confirmation at write time, immediately after the gate that authorizes attempting it.

When agents disagree or an artifact contradicts another, do not silently resolve it: record the disagreement in `openQuestions`, show both sides to the human, ask which should stand, then update `workflow/decisions.md` with the resolution before continuing.

## 5. Failure handling

If a specialist agent fails or produces an unusable output: set its status to `FAILED`, record the error verbatim in `status.json` and `events.jsonl`, and tell the human. Offer `/retry <workflow-id> <agent>` or `/skip <workflow-id> <agent>`. Before allowing a skip, name every downstream agent/gate that consumes this agent's output and what will be missing or degraded in the final PRD as a result — only skip after the human confirms.

## 6. Validation procedure (run before Gate 6, and on-demand via `/review`)

Delegate to the **`validation-review`** skill (`.claude/skills/validation-review/SKILL.md`) — it owns the full checklist for the four dimensions (consistency, completeness, feasibility, quality/security) so it isn't duplicated here. This is a lightweight pass performed on demand — do not stand up a permanent reviewer-agent hierarchy for it.

Produce findings only — never silently edit an already human-approved artifact. If a finding implies a needed change, route it back through the gate that owns the affected artifact (e.g., a missing NFR found late routes back through Gate 1/2 for the human to decide, it doesn't get quietly patched in).

## 7. Final PRD assembly (`/prd`, and as part of FULL mode after Gate 5, before Gate 6)

Assemble `artifacts/prd/final-prd.md` (create the directory if needed) with sections, each pulling from its source artifact:

```
final-prd.md  (becomes the "PRD - <Project Name>" Confluence page's final content — same page Gate 1 already published, updated in place, not a new page)
├── Executive Summary          (written fresh — 1 paragraph problem, 1 paragraph solution, from prd_agent's PRD + validated artifacts)
├── Requirements                <- artifacts/prd/prd-<slug>.md (prd_agent's Confirmed PRD, the Gate 1 artifact), cross-checked against artifacts/research/requirements-baseline.md
├── Feature Specification (link) <- its own page, "Feature Specification - <Project Name>", published after Gate 2
├── Solution Architecture (link) <- its own page, "Solution Architecture - <Project Name>", published after Gate 2
├── Design Document (link)       <- its own page, "Design Document - <Project Name>" (UI/UX spec), published after Gate 2
├── User Stories                <- artifacts/stories/user-stories.md, with each US-XXX's Jira issue key/URL from status.json's jira.issues (Jira, not a Confluence page)
├── Estimate and Cost (link)     <- its own page, "Estimate and Cost - <Project Name>", published after Gate 4
├── Risk Register (link)         <- its own page, "Risk Register - <Project Name>", published after Gate 4
├── Test Strategy (link)         <- its own page, "Test Strategy - <Project Name>", published after Gate 5
├── Traceability Matrix         (generated: REQ -> FEAT -> US(+Jira key) -> ARCH/UI -> EST -> RISK -> TS)
└── Decision Log                <- workflow/decisions.md (entries relevant to this workflow)
```

Include the standard metadata block (Workflow ID, Agent: orchestrator, Created, Status, Source artifacts, Human approval status) at the top of the assembled PRD. Sections marked "(link)" reference the already-published standalone page rather than duplicating its full content — the PRD page becomes the project's index/traceability hub, not a re-copy of every document.

## 7a. Test strategy (`/test-strategy`, dispatched after Gate 4, reviewed at Gate 5)

Dispatch `test-strategy-agent` (`.claude/agents/test-strategy-agent.md`) — it owns the full contract (input artifacts, the human-consultation step, output structure, hard rules) so none of that is duplicated here. By this point in the pipeline (§2), its full documented input set already exists: the approved PRD, feature spec, user stories, architecture, UI/UX spec, and risk register. It produces `artifacts/test-strategy/test-strategy.md`, reviewed at Gate 5 and then folded into §7's final assembly as a summary + link — the full document stays its own page, since it's a distinct document with its own downstream readers (test planning, test case generation, test automation).

## 7b. Architecture Suite workflow (`/generate-architecture`)

This workflow generates and publishes the Solution Architecture / Security Architecture / Technology Stack Confluence page set for a standalone PRD project (Shape B: `docs/01-prd/prd-*.md`). It does not require the discovery pipeline above to have run for this project, and it is dispatched and gated by `orchestrator-agent` directly — there is no separate sub-orchestrator for it.

1. **Resolve the PRD.** Check `config/project.yaml` → `confluence.prd_local_path`; if set and the file exists, read it. Otherwise glob `docs/01-prd/prd-*.md` (exactly one match → use it; multiple → ask which; none → fetch from Confluence via the `confluence-doc-resolver` skill using `confluence.prd_page_url` if set, or by name scoped to `confluence.site` otherwise — on resolution, reconstruct the PRD in `prd-agent`'s standard template, write it to `docs/01-prd/prd-<slug>.md`, and update `confluence.prd_local_path`). Confirm the resolved PRD's header shows `Status: Confirmed` — if `Draft`, **stop** and report what's blocking confirmation.
2. **Generate/approve `ARCH-XXX`.** If `artifacts/architecture/solution-architecture.md` already shows `Human approval status: APPROVED`, skip to step 3. Otherwise dispatch `solution-architect-agent` against the resolved PRD (Shape B, tracing every `ARCH-XXX` to a `REQ-XXX`). Enforce **Gate ARCH-1 — Solution Architecture Approval**: present the full artifact, call out every irreversible/high-impact technology decision individually, require `APPROVE` / `REQUEST_CHANGES` (route back, re-present) / `STOP`. On `APPROVE`, set `Human approval status: APPROVED`.
3. **Generate the suite.** Dispatch `solution-architecture-overview-agent`, `solution-security-architecture-agent`, `solution-tech-stack-agent` in parallel (Shape B input) — they don't depend on each other. Verify each wrote its artifact with `Status: DRAFT`.
4. **Validate.** Run the `validation-review` skill across the full artifact set including these three files — its Consistency dimension catches a tech-stack entry contradicting the overview, or a security control with no matching risk-register entry.
5. **Gate — Architecture Suite Approval.** Present the three draft documents (or a summary with a pointer to each — human's choice, offer full content first), the validation findings by dimension/severity, every `[SECURITY REVIEW REQUIRED]` marker individually listed, and every `[TBD]` item. Require `APPROVE` (all three as-is), `APPROVE_WITH_CHANGES` (name what changes, route back to the relevant specialist, re-present in full — no partial re-approval), or `STOP`. **Hard rule:** a blanket `APPROVE` does not clear this gate while any `[SECURITY REVIEW REQUIRED]` marker is unaddressed. On clearing, set each document's `Status: APPROVED` / `Human approval status: APPROVED`.
6. **Publish.** Resolve this project's Confluence folder per §1a (ask new-vs-existing if not already resolved this session) and invoke `confluence-publish` with `PageSet` = the three approved documents, titled `Solution Architecture Overview - <Project Name>`, `Security Architecture - <Project Name>`, `Technology Stack - <Project Name>` per the naming convention, `ParentPage` = that project folder. If `confluence.space`/`confluence.parent_page` are blank or `create_if_missing`/`allow_updates` are `false`, resolve this with the human before this step — generation/validation (steps 1–5) can proceed without it.
7. Record the gate decision in `workflow/decisions.md`, same as every other gate.

Report on completion: which PRD was used, `ARCH-XXX` approval status, the three documents' statuses, outstanding `[SECURITY REVIEW REQUIRED]`/`[TBD]` items, and — if published — each page's Confluence URL.

## 8. Publication — Confluence (throughout the pipeline, and `/publish` for the final package at Gate 7) and Jira (Gate 3)

**Confluence.** Delegate every Confluence write to the **`confluence-publish`** skill (`.claude/skills/confluence-publish/SKILL.md`) — it owns MCP-connector verification, site/space/parent-page confirmation, search-before-create, CREATE-vs-UPDATE detection, and the actual publish calls, so none of that is duplicated here. This happens at four points, each independently gated:
- After Gate 1: the confirmed PRD, as its own page.
- After Gate 2: `feature-specification.md`, `solution-architecture.md`, `ui-ux-specification.md`, each its own page.
- After Gate 4: `estimation-cost-analysis.md`, `risk-register.md`, each its own page.
- After Gate 5: `test-strategy.md`, its own page.
- After Gate 6 (`/publish`, requiring the literal `APPROVE_AND_PUBLISH` decision): the `PRD - <Project Name>` page is updated in place with the fully assembled content (§7) — Executive Summary, Traceability Matrix, and Decision Log are new; Requirements was already there from Gate 1 — with Gate 7's own per-page confirmation.

All of these publish under **this workflow's project folder** (§1a — resolved at Gate 0b, itself a child of `confluence.parent_page`), titled `<Document Type> - <Project Name>` per the naming convention (`orchestrator-agent.md`) — never a bare `PRD` folder shared across every project this repo ever runs. After each call, write the resulting page IDs/URLs into `confluence.pages` in `status.json` and append the `PUBLISHED` events it reports to `events.jsonl` (this skill remains the sole writer of `status.json`/`events.jsonl`; `confluence-publish` only returns data, it does not write workflow files itself).

**Jira.** After Gate 3, publish `user-stories.md`'s stories into the Jira project already resolved **and explicitly confirmed with the human at Gate 0b** (§1a) — never re-derived from `config/project.yaml` at this point, and never proceeded with if Gate 0b never actually got a confirmation for this workflow. No separate skill for this — see `orchestrator-agent.md`'s "Publishing user stories to Jira" section for the exact procedure: resolve issue types, search-before-create via JQL, present the full create/update list (destination project called out first, not buried in a column) for explicit confirmation, then create/update and link. Write the resulting issue keys/URLs into `jira.issues` in `status.json` and append the corresponding events to `events.jsonl`.

## 9. What this skill must never do

- Approve its own or a specialist's output on the human's behalf.
- Invent or infer stakeholder identity for a decision — if the human doesn't state who decided, record `decided_by: "human (unspecified)"`, never a guessed name.
- Publish anything — Confluence or Jira — without the gate that authorizes it (Gates 1/2/4/5 for their respective documents, Gate 3 for Jira stories, Gate 6's literal `APPROVE_AND_PUBLISH` plus Gate 7 for the final package) and explicit per-item confirmation at write time.
- Treat "agent completed" as "human approved," or treat a content-review gate as publish approval for that content.
- Fabricate research, estimates, metrics, or Confluence/Jira connectivity status.
- Overwrite an existing Confluence page, or an existing Jira issue found via search-before-create, without explicit approval for that specific item.
- Run `research_requirements` speculatively — only in response to a specific gap `prd_agent` flagged.
- Guess or derive a project's Confluence folder name, or assume new-vs-continuation, without asking the human (Gate 0b) — and never publish a new project's documents into an existing project's folder, or vice versa, without that explicit resolution.
- Create a Jira issue against `jira.project_key` (or any previously-recorded `jiraProjectKey`) without the human explicitly confirming that destination at Gate 0b for this workflow — a configured or previously-recorded value is a suggestion to confirm, never an approval to act on.
