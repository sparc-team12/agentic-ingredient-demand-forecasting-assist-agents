---
name: product-discovery
description: Master orchestration procedure for the human-gated AI product discovery & planning workflow. Invoked by the /product-plan, /orchestrate, /research, /features, /stories, /architecture, /uiux, /estimate, /risk, /test-strategy, /prd, /review, /status, /publish, /retry, and /skip commands. Coordinates prd-agent and the specialist subagents in .claude/agents/ (including test-strategy-agent), maintains workflow/status.json and workflow/events.jsonl, enforces human approval gates, and delegates validation to the validation-review skill and Confluence publishing to the confluence-publish skill.
---

# Product Discovery & Planning — Orchestration Procedure

This skill is the control-plane logic for `product-discovery-orchestrator` (see `.claude/agents/product-discovery-orchestrator.md`). Every command in `.claude/commands/` delegates here with a `mode` and arguments. Follow this procedure exactly — do not skip gates, do not fabricate approvals, do not publish without explicit confirmation.

Governing principle (do not violate): **AI accelerates product discovery and SDLC planning; humans remain the decision authority for requirements, architecture, estimates, risk acceptance, and publication.** When in doubt between more autonomy and a human checkpoint, choose the checkpoint.

## 0. Files this skill owns

- `workflow/status.json` — single source of truth. This skill is the only writer. Read-modify-write atomically: read current content, compute the new object in full, write the whole file back (never hand-edit with partial patches that could race).
- `workflow/events.jsonl` — append-only audit log, one JSON object per line, newline-terminated.
- `workflow/decisions.md` — append-only human decision log, one `## DEC-XXX` section per decision.
- `workflow/metrics.json` — lightweight observability (timestamps, durations, status counts). Never invent token/cost numbers this environment does not expose.
- `config/project.yaml` — Confluence site/space/parent page and workflow toggles. Read, don't silently rewrite; if the human changes it, respect the new values on next read.

Specialist input/output artifact contracts live in each `.claude/agents/*.md` file — this skill dispatches to them but does not duplicate their contracts here.

## 1. status.json schema

```json
{
  "schemaVersion": 1,
  "activeWorkflowId": "WF-2026-001",
  "workflows": {
    "WF-2026-001": {
      "workflowId": "WF-2026-001",
      "workflowName": "...",
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
        "research_requirements": { "status": "COMPLETED", "startedAt": "...", "completedAt": "...", "task": "...", "output": "artifacts/research/requirements-baseline.md", "summary": "dispatched by prd_agent, not directly by the orchestrator, whenever it flagged a research gap", "errors": [], "revisionCount": 0 },
        "feature_analyst": { "status": "NOT_STARTED" },
        "user_story_analyst": { "status": "NOT_STARTED" },
        "solution_architect": { "status": "NOT_STARTED" },
        "uiux_designer": { "status": "NOT_STARTED" },
        "estimation_cost": { "status": "NOT_STARTED" },
        "risk_compliance": { "status": "NOT_STARTED" },
        "test_strategy": { "status": "NOT_STARTED" }
      },
      "artifacts": [],
      "decisions": [],
      "openQuestions": [],
      "confluence": { "site": null, "space": null, "parentPageId": null, "pages": [] },
      "events": []
    }
  }
}
```

Valid statuses (workflow-level and per-agent): `NOT_STARTED, QUEUED, RUNNING, WAITING_FOR_HUMAN, BLOCKED, NEEDS_REVISION, COMPLETED, FAILED, SKIPPED, APPROVED, PUBLISHED`.

Workflow ID format: `WF-<current-year>-<3-digit-sequence>`, sequence scoped per year, computed from the highest existing sequence in `workflows` for that year (start at 001).

Every write to `status.json` also appends the corresponding line(s) to `workflow/events.jsonl`, e.g.:
```json
{"timestamp":"...","workflowId":"WF-2026-001","agent":"research_requirements","event":"STARTED","message":"..."}
{"timestamp":"...","workflowId":"WF-2026-001","event":"HUMAN_GATE","gate":"REQUIREMENTS_APPROVAL","status":"PENDING"}
```

Update `status.json` (and log an event) after: workflow creation, agent dispatch, agent start, agent completion, agent failure, human question, human response, gate approval, gate rejection, revision request, validation result, Confluence publication.

## 2. Dispatch order and parallelism

```
prd_agent (interviews the human; dispatches research_requirements itself as gaps appear)
        |
   [GATE 1: REQUIREMENTS_APPROVAL]  <- presents prd_agent's Confirmed PRD
        |
feature_analyst
        |
   +----+----+----------------+
   |         |                |
user_story  solution_architect  uiux_designer      <- run in parallel (independent inputs)
   +----+----+----------------+
        |
   [GATE 2: SOLUTION_REVIEW]
        |
estimation_cost
        |
risk_compliance
        |
   [GATE 3: ESTIMATE_RISK_REVIEW]
        |
   VALIDATION (consistency / completeness / feasibility / quality-security)
        |
   +----+----+
   |         |
   PRD ASSEMBLY   test_strategy    <- run in parallel (independent — both read the same approved artifacts)
   + traceability
   matrix
   +----+----+
        |
   [GATE 4: FINAL_PRD_APPROVAL — presents both the PRD package and the test strategy; requires literal "APPROVE_AND_PUBLISH"]
        |
   [GATE 5: CONFLUENCE_PUBLICATION — requires explicit per-page confirmation]
```

Dispatch each specialist by invoking its agent definition in `.claude/agents/` with only the artifact paths it needs (per its input contract) — never the full conversation or unrelated artifacts. `user_story_analyst`, `solution_architect`, and `uiux_designer` may run concurrently since none of them write to another's output; do not run more agents concurrently than `config/project.yaml`'s `workflow.max_parallel_agents`.

## 3. Modes (what each command passes in)

- **FULL** (`/product-plan <requirement>`): create a new workflow, dispatch `prd_agent` with the raw input as given (free-text conversation, ticket, or detailed brief — whatever shape it arrives in), let it interview the human and call `research_requirements` itself as it hits gaps, stop at Gate 1 once `prd_agent` hands back a `Confirmed` PRD. On resume after approval, continue the full chain through Gate 5.
- **RESUME** (`/product-plan --resume <workflow-id>`): read `status.json` for that workflow, determine `currentGate`/`overallStatus`, and continue from exactly that point — never re-run a `COMPLETED` agent whose artifact still exists and is still the approved input for the next step.
- **ORCHESTRATE_ONLY** (`/orchestrate --only <agent1,agent2,...>` or `/product-plan --agents ...`): run exactly the named agents (in correct dependency order), reusing existing upstream artifacts, still enforcing any gate that sits between the named agents and their inputs/outputs.
- **SINGLE_AGENT** (`/research <requirement>`, `/features <workflow-id>`, `/stories <workflow-id>`, `/architecture <workflow-id>`, `/uiux <workflow-id>`, `/estimate <workflow-id>`, `/risk <workflow-id>`, `/test-strategy <workflow-id>`): run one specialist directly.
  - `/research` with no existing workflow-id creates a new workflow.
  - All others require a `workflow-id` and must refuse to run if their required upstream artifact is missing, or exists but is not yet human-approved at the relevant gate — explain what's missing/unapproved instead of proceeding. `/test-strategy` specifically requires Gate 3 `APPROVED` (it reads the risk register, not just the estimate).
- **REVIEW** (`/review <workflow-id>`): run the Validation procedure (§6) against whatever artifacts currently exist and report findings; does not advance any gate by itself.
- **STATUS** (`/status [workflow-id]`): print a concise human-readable rendering of `status.json` for the given workflow, or a list of all workflows if none given.
- **PRD** (`/prd <workflow-id>`): assemble the final PRD package (§7) — only valid once Gate 3 is APPROVED.
- **PUBLISH** (`/publish <workflow-id>`): run the Confluence publication procedure (§8) — only valid once Gate 4 has recorded `APPROVE_AND_PUBLISH`.
- **RETRY** (`/retry <workflow-id> <agent>`): reset that agent's status to `QUEUED`, increment `revisionCount`, re-dispatch it with the same inputs.
- **SKIP** (`/skip <workflow-id> <agent>`): mark `SKIPPED` only after explicit human confirmation; first explain which downstream agents/gates depend on this agent's output and what will be missing from the final PRD if skipped.

## 4. Human gates — exact behavior

At every gate: present what was produced, list unresolved questions/risks/contradictions, then stop and wait. Do not proceed on an assumed or implied approval.

- **Gate 0 — Intake**: after parsing the human's request, restate your understanding in a few sentences (problem, scope hints, any constraints/documents/Jira-Confluence references given) and ask for anything critical that's missing before dispatching `prd_agent`.
- **Gate 1 — Requirements Approval**: present the `Confirmed` PRD `prd_agent` produced (its Requirements, Research Context, Assumptions, and Open Questions sections already carry the research findings and confidence notes). Require exactly one of `APPROVE`, `REQUEST_CHANGES`, `PROVIDE_CLARIFICATION`, `STOP`. On `REQUEST_CHANGES`/`PROVIDE_CLARIFICATION`, re-run `prd_agent` with the human's input (amendment flow) and increment `revisionCount`. On `STOP`, halt the workflow and set `overallStatus: BLOCKED`.
- **Gate 2 — Solution Review**: after `feature_analyst`, `user_story_analyst`, `solution_architect`, `uiux_designer` complete, present a concise cross-domain summary (major features, key stories, architecture summary, major UI/UX flows, dependencies, any contradictions found, open decisions). Require approval before dispatching `estimation_cost`.
- **Gate 3 — Estimate/Risk Review**: present effort/timeline/cost ranges, major risks, security/compliance concerns, and high-impact assumptions. Require approval before PRD assembly and `test_strategy`.
- **Gate 4 — Final PRD Approval**: present the assembled PRD package, the test strategy document, and validation findings together. Require the literal string `APPROVE_AND_PUBLISH`. Any other response stops publication (it does not have to stop the workflow — the human may still want the PRD and test strategy without publishing).
- **Gate 5 — Confluence Publication**: before calling any write tool, show target site/space/parent page, the exact page titles to be created/updated, whether each is CREATE or UPDATE (per §8 existence check), and flag anything destructive (an UPDATE that would replace existing content). Require explicit confirmation. Never overwrite an existing page without it.

When agents disagree or an artifact contradicts another, do not silently resolve it: record the disagreement in `openQuestions`, show both sides to the human, ask which should stand, then update `workflow/decisions.md` with the resolution before continuing.

## 5. Failure handling

If a specialist agent fails or produces an unusable output: set its status to `FAILED`, record the error verbatim in `status.json` and `events.jsonl`, and tell the human. Offer `/retry <workflow-id> <agent>` or `/skip <workflow-id> <agent>`. Before allowing a skip, name every downstream agent/gate that consumes this agent's output and what will be missing or degraded in the final PRD as a result — only skip after the human confirms.

## 6. Validation procedure (run before Gate 4, and on-demand via `/review`)

Delegate to the **`validation-review`** skill (`.claude/skills/validation-review/SKILL.md`) — it owns the full checklist for the four dimensions (consistency, completeness, feasibility, quality/security) so it isn't duplicated here. This is a lightweight pass performed on demand — do not stand up a permanent reviewer-agent hierarchy for it.

Produce findings only — never silently edit an already human-approved artifact. If a finding implies a needed change, route it back through the gate that owns the affected artifact (e.g., a missing NFR found late routes back through Gate 1/2 for the human to decide, it doesn't get quietly patched in).

## 7. Final PRD assembly (`/prd`, and as part of FULL mode before Gate 4)

Assemble `artifacts/prd/final-prd.md` (create the directory if needed) with sections, each pulling from its source artifact:

```
PRD parent page
├── Executive Summary          (written fresh — 1 paragraph problem, 1 paragraph solution, from prd_agent's PRD + validated artifacts)
├── Requirements                <- artifacts/prd/prd-<slug>.md (prd_agent's Confirmed PRD, the Gate 1 artifact), cross-checked against artifacts/research/requirements-baseline.md
├── Feature Specification       <- artifacts/features/feature-specification.md
├── User Stories                <- artifacts/stories/user-stories.md
├── Solution Architecture       <- artifacts/architecture/solution-architecture.md
├── UI/UX Specification         <- artifacts/design/ui-ux-specification.md
├── Estimation & Cost           <- artifacts/estimation/estimation-cost-analysis.md
├── Risk Register               <- artifacts/risk/risk-register.md
├── Traceability Matrix         (generated: REQ -> FEAT -> US/UI -> ARCH -> EST -> RISK, per §8 of the setup spec)
└── Decision Log                <- workflow/decisions.md (entries relevant to this workflow)
```

Include the standard metadata block (Workflow ID, Agent: orchestrator, Created, Status, Source artifacts, Human approval status) at the top of the assembled PRD.

## 7a. Test strategy (`/test-strategy`, and as part of FULL mode alongside §7, before Gate 4)

Dispatch `test-strategy-agent` (`.claude/agents/test-strategy-agent.md`) — it owns the full contract (input artifacts, the human-consultation step, output structure, hard rules) so none of that is duplicated here. It runs independently of §7's PRD assembly (both read the same Gate-3-approved artifacts; neither writes the other's output), producing `artifacts/test-strategy/test-strategy.md`. Present it at Gate 4 alongside the assembled PRD package — it is not folded into `final-prd.md` itself, since it's a distinct document with its own downstream readers (test planning, test case generation, test automation).

## 8. Confluence publication (`/publish`, Gate 5)

Delegate to the **`confluence-publish`** skill (`.claude/skills/confluence-publish/SKILL.md`) — it owns MCP-connector verification, site/space/parent-page confirmation, search-before-create, CREATE-vs-UPDATE detection, and the actual publish calls, so none of that is duplicated here. Before invoking it, confirm Gate 4 recorded the literal `APPROVE_AND_PUBLISH` decision for this workflow. After it returns, write the resulting page IDs/URLs into `confluence.pages` in `status.json` and append the `PUBLISHED` events it reports to `events.jsonl` (this skill remains the sole writer of `status.json`/`events.jsonl`; `confluence-publish` only returns data, it does not write workflow files itself). The published package nests under a `PRD` child page under the project's main Confluence page — the same folder `prd_agent` already publishes its own confirmed draft into, so both live in one place. If Gate 4 approved the test strategy alongside the PRD, offer to publish it too, as its own page under the same `PRD` folder (sibling to the PRD package, not merged into it) — same search-before-create, CREATE-vs-UPDATE, and explicit-confirmation rules apply.

## 9. What this skill must never do

- Approve its own or a specialist's output on the human's behalf.
- Invent or infer stakeholder identity for a decision — if the human doesn't state who decided, record `decided_by: "human (unspecified)"`, never a guessed name.
- Publish without the literal `APPROVE_AND_PUBLISH` at Gate 4 and explicit per-page confirmation at Gate 5.
- Treat "agent completed" as "human approved."
- Fabricate research, estimates, metrics, or Confluence connectivity status.
- Overwrite an existing Confluence page without explicit approval for that specific page.
