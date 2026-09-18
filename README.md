# agentic-ingredient-demand-forecasting-assist-agents

A human-in-the-loop product discovery, architecture, and development-agent system built on Claude Code. The architecture suite converts approved solution architecture into reviewed HLD and implementation-ready LLD; only then may the development orchestrator implement a work item through independent verification and a structured QA handoff. It never treats development completion as QA approval and does not autonomously release or deploy.

## 1. What this system does

Given a statement like "Build an ingredient demand forecasting assistant for a multi-location kitchen operator," the orchestrator:

0. First asks whether this is a **new project or a continuation of one already tracked here (Gate 0b)**, then resolves or creates that project's Confluence folder — every document this workflow ever publishes lands there, never in a shared catch-all folder.
1. Dispatches **prd-agent** with the raw input — it interviews the human conversationally, flagging narrow, specific research gaps back to the orchestrator (which dispatches the research agent sparingly, to keep token spend down) rather than dispatching it itself, and produces a Confirmed PRD, then **stops for human approval (Gate 1)**. On approval, the orchestrator publishes the PRD to Confluence — its normal publish point, not a deferred extra.
2. Runs **feature-analyst-agent** and **solution-architect-agent** in parallel off the approved PRD, then **uiux-designer-agent** once the feature breakdown exists, then **stops for human approval (Gate 2)**, then offers each document's Confluence publish individually.
3. Runs **user-story-analyst-agent** against the approved PRD, feature spec, architecture, and UI/UX spec, then **stops for human approval (Gate 3)** — which also confirms each story's proposed Jira issue type — then publishes the stories to **Jira**, not Confluence.
4. Runs **estimation-cost-agent** (now informed by the user stories too) and then **risk-compliance-agent**, then **stops for human approval (Gate 4)**, then offers each document's Confluence publish individually.
5. Runs **test-strategy-agent** last — by now the PRD, feature spec, stories, architecture, UI/UX spec, and risk register all exist, exactly what it needs — consulting the human directly on QA tooling/environment/compliance context, then **stops for human approval (Gate 5)**, then offers its Confluence publish.
6. Validates everything for consistency, completeness, feasibility, and quality/security, then assembles a final PRD with a full traceability matrix (including each story's Jira link) and **requires the literal `APPROVE_AND_PUBLISH` (Gate 6)**.
7. Publishes the final package to Confluence via the Atlassian MCP integration, **only after explicit per-page confirmation (Gate 7)** — every document lands under this project's own Confluence folder (resolved at step 0), titled `<Document Type> - <Project Name>` (e.g. `PRD - <name>`, `Design Document - <name>`, `Estimate and Cost - <name>`); every individual publish along the way (steps 1–5) gets the same per-item confirmation, never a silent write.

## 2. Architecture

```text
                           HUMAN
                             |
                             v
              +-----------------------------+
              | ORCHESTRATOR AGENT            |
              | Plans / delegates / tracks    |
              | validates / gates / publishes |
              | (sole Confluence/Jira access) |
              +-------------+---------------+
                            |
                            v
        [GATE 0b: Confluence folder (new: name it / continuation: resolve it) +
                  Jira destination confirmed with human (default offered, never assumed)]
                            |
                            v
                       PRD AGENT  <--- flags research needs;
                            |           orchestrator dispatches
                            |           Research & Requirements Agent
                      [GATE 1: Confirmed PRD]
                            |
                    orchestrator publishes PRD to Confluence
                            |
                +-----------+-----------+
                |                       |
                v                       v
          Feature Analyst        Solution Architect
                |
                v
          UI/UX Designer   (starts once Feature Analyst finishes)
                |
                v
      [GATE 2: Feature/Architecture/UI-UX approved]
                |
       publish each individually to Confluence
                |
                v
        User Story Analyst  (PRD + feature + architecture + UI/UX)
                |
      [GATE 3: User Stories approved + Jira issue-type mapping]
                |
        publish stories to JIRA (not Confluence)
                |
                v
       Estimation & Cost Agent  (now includes user stories)
                |
                v
         Risk & Compliance Agent
                |
      [GATE 4: Estimate/Risk approved]
                |
       publish each individually to Confluence
                |
                v
          Test Strategy Agent   (PRD + features + stories +
                |                 architecture + UI/UX + risk
                |                 + direct human QA input)
      [GATE 5: Test Strategy approved]
                |
        publish to Confluence
                |
                v
              +-----------------------------+
              | ORCHESTRATOR VALIDATION      |
              | Consistency / Completeness / |
              | Feasibility / Quality-Sec.   |
              +-------------+---------------+
                            |
                            v
                     PRD ASSEMBLY
                  + traceability matrix
                (incl. Jira story links)
                            |
                            v
                    HUMAN APPROVAL
              (Gate 6: literal APPROVE_AND_PUBLISH)
                            |
                            v
                      FINAL PRD PACKAGE
                            |
                [GATE 7: per-page confirmation]
                            v
        CONFLUENCE (this project's folder, "<Document Type> - <Project Name>" per page)
```

Specialist agents are direct children of the orchestrator — there is no recursive agent tree. The orchestration procedure lives in `.claude/skills/product-discovery/SKILL.md`, which delegates the four-dimension validation checklist to `.claude/skills/validation-review/SKILL.md` and the Confluence publish mechanics to `.claude/skills/confluence-publish/SKILL.md`; every slash command is a thin dispatcher into whichever of the three actually owns the logic it needs.

## 3. Agent responsibilities

| Agent | File | Output |
|---|---|---|
| Orchestrator Agent (the single canonical orchestrator) | `.claude/agents/orchestrator-agent.md` | `workflow/status.json`, `workflow/events.jsonl`, gate management, PRD assembly, Confluence publish, Architecture Suite workflow — sole holder of Confluence/Jira MCP access |
| **PRD Agent (entry point)** | `.claude/agents/prd-agent.md` | `artifacts/prd/prd-<slug>.md` (`REQ-XXX`) — interviews the human, flags Research & Requirements needs to the orchestrator (never dispatches it itself) |
| Research & Requirements | `.claude/agents/research-requirements-agent.md` | `artifacts/research/requirements-baseline.md`, `artifacts/research/open-questions.md` |
| Feature Analyst | `.claude/agents/feature-analyst-agent.md` | `artifacts/features/feature-specification.md` (`FEAT-XXX`) |
| User Story Analyst | `.claude/agents/user-story-analyst-agent.md` | `artifacts/stories/user-stories.md` (`US-XXX`) |
| Solution Architect | `.claude/agents/solution-architect-agent.md` | `artifacts/architecture/solution-architecture.md` (`ARCH-XXX`) |
| HLD Architect | `.claude/agents/solution-hld-agent.md` | `artifacts/architecture/high-level-design.md` (`HLD-XXX`) |
| LLD Architect | `.claude/agents/solution-lld-agent.md` | `artifacts/architecture/low-level-design.md` (`LLD-XXX`) |
| Architecture Validator | `.claude/agents/solution-architecture-validator-agent.md` | `artifacts/architecture/architecture-validation.json` and development-readiness gate |
| Project Initializer | `.claude/agents/dev-scaffold-agent.md` | Tech-stack-driven manifests, source/test layout, configuration, CI, build verification, and `project-initialization.json` |
| UI/UX Designer | `.claude/agents/uiux-designer-agent.md` | `artifacts/design/ui-ux-specification.md` (`UI-XXX`) |
| Estimation & Cost | `.claude/agents/estimation-cost-agent.md` | `artifacts/estimation/estimation-cost-analysis.md` (`EST-XXX`) |
| Risk & Compliance | `.claude/agents/risk-compliance-agent.md` | `artifacts/risk/risk-register.md` (`RISK-XXX`) |
| Test Strategy | `.claude/agents/test-strategy-agent.md` | `artifacts/test-strategy/test-strategy.md` (`TS-XXX`) — guideline for test planning, test case generation, and test automation |
| Development Orchestrator | `.claude/agents/dev-orchestrator-agent.md` | Per-work-item stage control and `dev-status.json`; terminal state `READY_FOR_QA` |
| Development specialists | `.claude/agents/dev-*.md`, `planning-sprint-agent.md`, `test-unit-agent.md`, `code-review-agent.md`, `test-verifier-agent.md` | Plan, implementation, tests, reviews, verification, and `qa-handoff.md` under `artifacts/development/<work-item-id>/` |
| QA E2E | `.claude/agents/test-e2e-agent.md` | Post-handoff `qa-e2e-report.md` against an approved non-production environment |

Each agent file states its input contract, output contract, allowed tools, and what it must **not** decide unilaterally.

## 4. Human-in-the-loop gates

| Gate | After | Requires |
|---|---|---|
| 0 — Intake | Parsing the request | Orchestrator confirms understanding; asks if critical info is missing |
| 0b — Project Identification | Gate 0 | Confluence: new project (name the folder) or continuation (resolve the existing one); Jira: explicitly confirm the destination project for user stories (a configured default is offered, never trusted silently) — all before the workflow ID is even minted |
| 1 — Requirements Approval | PRD Agent (interview + research as needed) | `APPROVE` / `REQUEST_CHANGES` / `PROVIDE_CLARIFICATION` / `STOP` on the Confirmed PRD; approval also authorizes publishing it to Confluence (own per-page confirmation) |
| 2 — Feature/Architecture/UI-UX Review | Feature Analyst, Solution Architect, UI/UX Designer | Approval before user stories; authorizes publishing each document individually |
| 3 — User Stories Review | User Story Analyst | Approval of stories **and** their proposed Jira issue-type mapping before publishing to Jira |
| 4 — Estimate/Risk Review | Estimation & Cost, Risk & Compliance | Approval before test strategy; authorizes publishing each document individually |
| 5 — Test Strategy Review | Test Strategy Agent | Approval before final PRD assembly; authorizes publishing it |
| 6 — Final PRD Approval | PRD assembly + validation | Literal `APPROVE_AND_PUBLISH` |
| 7 — Confluence Publication | Gate 6 | Explicit confirmation per page for the final package; existing pages/issues are never silently overwritten |

No gate above is itself publish approval — every individual Confluence page or Jira issue still gets its own explicit confirmation at write time.

## 5. Repository structure

```text
.claude/
  agents/            discovery/planning agents plus the development-to-QA pipeline
  skills/
    product-discovery/SKILL.md   master orchestration procedure (dispatch order, gates)
    validation-review/SKILL.md   consistency/completeness/feasibility/quality-security checklist
    confluence-publish/SKILL.md  MCP verification, search-before-create, CREATE vs UPDATE, publish
  commands/          /product-plan, /orchestrate, /init-project, /develop, /research, /features, /stories,
                      /architecture, /uiux, /estimate, /risk, /test-strategy, /review,
                      /status, /prd, /publish, /retry, /skip
  CLAUDE.md          repo-level operating rules for Claude Code
artifacts/           specialist output (created on demand, never pre-populated)
workflow/
  status.json        single source of truth (orchestrator is the only writer)
  events.jsonl       append-only audit log
  decisions.md        human decision log
  metrics.json       timestamps/durations/status counts (no invented token/cost figures)
config/project.yaml  Confluence target + workflow toggles (no secrets)
examples/            demo input for /product-plan
SETUP_DECISIONS.md   decisions made while building this system itself
```

## 6. Claude Code setup

This is a standard Claude Code project — open the repository root in Claude Code (CLI, desktop, or IDE extension) and the agents/skills/commands under `.claude/` are picked up automatically. No build step is required.

## 7. Atlassian MCP setup

Confluence publication uses whichever Atlassian MCP integration is actually configured in your environment — do not assume a tool name or schema without checking.

- **If you're on the claude.ai Atlassian Rovo connector** (as verified in this environment on 2026-09-17, account `sparc.team12@experionglobal.com`, site `https://experionglobal.atlassian.net`): it's already authenticated; nothing further to install. Publication uses the `mcp__claude_ai_Atlassian_Rovo__*` tools (search, create, update, get spaces/pages).
- **If you're on the Claude Code CLI without Atlassian configured**, add it and authenticate:
  ```bash
  claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
  ```
  then run `/mcp` and complete authentication.

Either way, before the first real publish, set `confluence.space` and `confluence.parent_page` in `config/project.yaml` — these are intentionally left blank and Gate 5 will ask if they're missing.

## 8. Available commands

```text
/product-plan <requirement>                 full gated workflow (new workflow, dispatches prd-agent first)
/product-plan --resume <workflow-id>        resume from wherever it stopped
/product-plan --agents <a,b,c> <req>        targeted orchestration
/orchestrate --only <a,b,c> [workflow-id]   run only named agents
/research <requirement>                     ad hoc research pass (normally run by prd-agent itself, not standalone)
/features <workflow-id>                     feature analyst only (requires Gate 1 approved)
/stories <workflow-id>                      user story analyst only -> Gate 3 (requires Gate 2 approved)
/architecture <workflow-id>                 solution architect only (requires Gate 1 approved)
/generate-architecture [id] --repo <path>   separate workflow, same orchestrator: architecture suite, HLD,
                                             LLD, independent validation, and approval (its own gate,
                                             independent of Gates 1-7 above), then development handoff
/uiux <workflow-id>                         UI/UX designer only (requires feature spec to exist)
/estimate <workflow-id>                     estimation & cost only (requires Gate 3 approved)
/risk <workflow-id>                         risk & compliance only -> Gate 4
/test-strategy <workflow-id>                test strategy only (requires Gate 4 approved)
/review <workflow-id>                       validation pass (consistency/completeness/feasibility/quality-security)
/prd <workflow-id>                          assemble final PRD + traceability -> Gate 6 (requires Gate 5 approved)
/publish <workflow-id>                      Confluence publication of the final package -> Gate 7
/retry <workflow-id> <agent>                retry a failed agent
/skip <workflow-id> <agent>                 skip an agent (requires confirmation)
/status [workflow-id]                       show workflow state
/develop <id> <requirement-path> ...        implement one approved work item through READY_FOR_QA
/init-project <id> --target <path>          initialize/verify boilerplate from approved stack, HLD, and LLD
```

Individual-document Confluence publishes (PRD, feature/architecture/UI-UX, estimation/risk, test strategy) and the Jira story publish happen inline in the full pipeline right after their gate — there's no separate slash command for each; see `.claude/agents/orchestrator-agent.md`.

## 9. Example workflow

See `examples/ingredient-demand-forecasting.md` for a demo product statement and a step-by-step walkthrough (`/product-plan examples/ingredient-demand-forecasting.md` through to `/publish`).

## 10. Status tracking

`workflow/status.json` is a registry of every workflow run in this repo (see `.claude/skills/product-discovery/SKILL.md` §1 for the exact schema), keyed by a `WF-<year>-<seq>` workflow ID. It also holds a top-level `projects` registry (§1a) mapping each tracked project to its Confluence folder, so a later workflow for the same project reuses that folder instead of creating a new one. The orchestrator is the only writer and uses atomic read-modify-write so status can't be corrupted by concurrent activity. `workflow/events.jsonl` mirrors every state transition as an independent, append-only audit trail.

## 11. Project destinations: Confluence folder and Jira project

Before anything else runs (**Gate 0b**), the orchestrator resolves and confirms where this workflow's output goes — both halves independently, since a project might have one configured without the other:

**Confluence folder** — is this a **new project** or a **continuation of an existing one already tracked here**?
- **New:** it asks the human for the Confluence folder name (never guesses or derives one), checks Confluence doesn't already have a same-titled folder, creates it under `confluence.parent_page`, and records it in `projects`.
- **Continuation:** it resolves the project's existing folder from `projects`, or by searching Confluence directly if it's not yet registered.

**Jira project** (destination for user stories) — where should they be created?
- The orchestrator calls `getVisibleJiraProjects` and, if `jira.project_key` is set in `config/project.yaml`, offers it as a suggested default — but **always requires the human to explicitly confirm it or name a different project**, every time this hasn't already been confirmed for this project. A configured or previously-recorded value is never treated as approval on its own.
- The confirmed project (key + name) is recorded in `projects`, and re-verified (not silently reused) on a later continuation workflow.
- This is a separate decision from the per-story create/update confirmation at Gate 3 — confirming *where* stories go isn't the same as approving *which* stories go there.

Every document this workflow publishes lands in the resolved Confluence folder, titled `<Document Type> - <Project Name>` — e.g. `PRD - <name>`, `Feature Specification - <name>`, `Solution Architecture - <name>`, `Design Document - <name>` (UI/UX spec), `Estimate and Cost - <name>`, `Risk Register - <name>`, `Test Strategy - <name>`. Titles are stable across versions (the version lives in the page body, not the title) and consistent across every workflow run for that project, which is what makes search-before-create meaningful over the project's lifetime.

## 12. Confluence and Jira publishing

Confluence publishing happens at multiple points — the PRD (after Gate 1), feature/architecture/UI-UX (after Gate 2), estimation/risk (after Gate 4), test strategy (after Gate 5), and the final package (`/publish`, after Gate 6's literal `APPROVE_AND_PUBLISH`, with Gate 7's own per-page confirmation) — all delegating to `.claude/skills/confluence-publish/SKILL.md`, and all landing under the project folder resolved at Gate 0b (§11). That skill always searches for an existing page before creating one, shows CREATE vs. UPDATE for every page up front, and refuses to overwrite an existing page without approval for that specific page.

User stories publish to **Jira**, not Confluence, after Gate 3 — the orchestrator handles this directly (no separate skill), targeting the project already confirmed with the human at Gate 0b (never re-derived from config at this point), searching by JQL before creating, and presenting the exact create/update list — destination project called out first, then each story's title/proposed issue type — for explicit confirmation before writing.

Published Confluence page IDs/URLs and Jira issue keys/URLs are recorded in `workflow/status.json` (`confluence.pages` and `jira.issues` respectively).

## 13. Security considerations

- Least-privilege tools per agent — see each agent file's `tools:` frontmatter. Specialists get `Read/Grep/Glob/Write` (plus `WebSearch`/`WebFetch` for research); only `orchestrator-agent` touches workflow state and Confluence/Jira.
- No credentials, tokens, or secrets are stored in this repo; `config/project.yaml` holds only non-secret configuration (site/space/page names, Jira project key, toggles).
- Legal/compliance claims are never asserted without evidence — the Risk & Compliance agent marks items `Requires legal/security review: yes` instead.

## 14. Known limitations

See `SETUP_DECISIONS.md` for the full list, notably:
- No workflow has been run end-to-end yet — the system is built and Confluence connectivity is verified, but no requirements/estimates/risks have been generated or human-reviewed.
- Confluence `space`/`parent_page` are not yet configured, and no project has a Confluence folder created/registered yet — required before the first Gate 0b can actually publish anything.
- Token/cost metrics aren't exposed to agents in this environment, so `workflow/metrics.json` tracks only timestamps/durations/status counts.
- Whether this session's tooling supports an orchestrator subagent invoking other subagents directly hasn't been exercised yet — see the environment note in `.claude/agents/orchestrator-agent.md`.
- The Architecture Suite workflow and a ported SDLC/change-request agent set exist under `.claude/agents/` but only the Architecture Suite is wired into the orchestrator so far — see `.claude/CLAUDE.md`'s "Known scope boundary" section for what's intentionally not yet gated.

## 15. Demo instructions

```text
1. Start Claude Code in this repository.
2. Run: /product-plan examples/ingredient-demand-forecasting.md
3. Respond to Gate 0b (Project Identification): say whether this is a new project or a continuation, and — if new — name the Confluence folder (the orchestrator never guesses this); also confirm which Jira project user stories should be created in (a configured default, if any, is offered but never assumed).
4. Answer prd-agent's interview questions (it may pause mid-interview while the orchestrator runs a narrowly-scoped research dispatch on a gap it can't resolve from your answers alone).
5. Respond to Gate 1 (Requirements Approval) with APPROVE, REQUEST_CHANGES, PROVIDE_CLARIFICATION, or STOP once prd-agent hands back a Confirmed PRD — approval also publishes `PRD - <Project Name>` to Confluence, in your project's folder (its own confirmation).
6. Respond to Gate 2 (Feature/Architecture/UI-UX Review) once those three documents are shown; each can be published to Confluence individually, in the same project folder.
7. Respond to Gate 3 (User Stories Review), including confirming the proposed Jira issue-type mapping — approval publishes the stories to Jira.
8. Respond to Gate 4 (Estimate/Risk Review); each document can be published to Confluence individually.
9. Respond to Gate 5 (Test Strategy Review). test-strategy-agent may ask about existing QA tooling/environments/compliance obligations before this.
10. Review the assembled PRD and traceability matrix at Gate 6; respond APPROVE_AND_PUBLISH to proceed, anything else to stop.
11. Confirm the exact Confluence page list at Gate 7 — this updates `PRD - <Project Name>` in place rather than creating a new page.
12. Check /status <workflow-id> at any point to see where things stand.
```

## 15. Development to QA workflow

First run `/generate-architecture [workflow-id] --repo <target-repository>` to produce and approve the HLD and LLD. For a new project, `/init-project <project-id> --target <path>` can initialize the boilerplate explicitly; `/develop` also invokes the same initializer automatically when it detects an empty target. Development refuses to start unless solution architecture, HLD, and LLD are approved and `architecture-validation.json` says `PASS` and `development_ready: true`.

The development orchestrator runs this deterministic sequence:

```text
Project initialization/verification
  (approved stack + HLD + LLD required; safely skipped for an existing compatible repository)
  -> requirements validation
  -> repository-aware implementation plan
  -> independent tech-lead review
  -> implementation + focused tests
  -> unit/component test closure
  -> independent code review (with bounded rework loop)
  -> clean-room verification
  -> QA handoff
  -> READY_FOR_QA (stop)
```

Evidence is stored under `artifacts/development/<work-item-id>/`. The QA handoff includes acceptance-criterion traceability, changed components, environment/migration notes, verification results, risks, and prioritized QA scenarios. QA can then invoke `test-e2e-agent` against an explicitly approved non-production environment. PR creation, release, and deployment remain separate, explicitly authorized stages.
