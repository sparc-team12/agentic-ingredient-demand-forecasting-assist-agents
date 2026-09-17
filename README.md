# agentic-ingredient-demand-forecasting-assist-agents

A human-in-the-loop product discovery, planning, and development-agent system built on Claude Code. The discovery orchestrator produces approved requirements, architecture, and test strategy; the separate development orchestrator can then implement one approved work item through independent verification and a structured QA handoff. It never treats development completion as QA approval and does not autonomously release or deploy.

## 1. What this system does

Given a statement like "Build an ingredient demand forecasting assistant for a multi-location kitchen operator," the orchestrator:

1. Dispatches **prd-agent** with the raw input — it interviews the human conversationally, dispatching the research agent itself as it hits gaps, and produces a Confirmed PRD, then **stops for human approval (Gate 1)**.
2. Runs feature decomposition, user stories, solution architecture, and UI/UX in parallel, then **stops for human approval**.
3. Runs estimation/cost and risk/compliance, then **stops for human approval**.
4. Validates everything for consistency, completeness, feasibility, and quality/security.
5. In parallel, assembles a final PRD with a full traceability matrix **and** dispatches **test-strategy-agent** (consuming the PRD, features, stories, architecture, UI/UX, and risk register, plus direct human input on QA tooling/environment/compliance context) to produce a test strategy document — the guideline later test planning, test case generation, and test automation work will use. Both are presented together, then **require the literal `APPROVE_AND_PUBLISH`**.
6. Publishes to Confluence via the Atlassian MCP integration, **only after explicit per-page confirmation** — the PRD and test strategy each land as their own page under a `PRD` folder in the project's Confluence space.

## 2. Architecture

```text
                           HUMAN
                             |
                             v
              +-----------------------------+
              | PRODUCT DISCOVERY &          |
              | PLANNING ORCHESTRATOR        |
              | Plans / delegates / tracks   |
              | validates / gates / publishes|
              +-------------+---------------+
                            |
                            v
                       PRD AGENT  <--- interviews human, dispatches
                            |           Research & Requirements Agent
                            |           itself as gaps appear
                      [GATE 1: Confirmed PRD]
                            |
          +-----------------+-----------------+
          |        |        |        |        |
          v        v        v        v        v
      (PRD)     Feature  User     Solution  UI/UX
      artifact   Analyst   Story    Architect Designer
                 Agent     Agent    Agent     Agent
          |        |        |        |        |
          +--------+--------+--------+--------+
                            |
                            v
                  Estimation & Cost Agent
                            |
                            v
                     Risk & Compliance
                            |
                      [GATE 3: Estimate/Risk approved]
                            |
                            v
              +-----------------------------+
              | ORCHESTRATOR VALIDATION      |
              | Consistency / Completeness / |
              | Feasibility / Quality-Sec.   |
              +-------------+---------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
        PRD ASSEMBLY              TEST STRATEGY AGENT
        + traceability             (PRD + features + stories +
                                     architecture + UI/UX + risk
                                     + direct human QA input)
              |                           |
              +-------------+-------------+
                            |
                            v
                    HUMAN APPROVAL
                  (Gate 4: PRD + test strategy)
                            |
                            v
              FINAL PRD  +  TEST STRATEGY
                            |
                            v
                CONFLUENCE (PRD folder, one page each)
```

Specialist agents are direct children of the orchestrator — there is no recursive agent tree. The orchestration procedure lives in `.claude/skills/product-discovery/SKILL.md`, which delegates the four-dimension validation checklist to `.claude/skills/validation-review/SKILL.md` and the Confluence publish mechanics to `.claude/skills/confluence-publish/SKILL.md`; every slash command is a thin dispatcher into whichever of the three actually owns the logic it needs.

## 3. Agent responsibilities

| Agent | File | Output |
|---|---|---|
| Product Discovery Orchestrator | `.claude/agents/product-discovery-orchestrator.md` | `workflow/status.json`, `workflow/events.jsonl`, gate management, PRD assembly, Confluence publish |
| **PRD Agent (entry point)** | `.claude/agents/prd-agent.md` | `artifacts/prd/prd-<slug>.md` (`REQ-XXX`) — interviews the human, dispatches Research & Requirements itself as needed |
| Research & Requirements | `.claude/agents/research-requirements-agent.md` | `artifacts/research/requirements-baseline.md`, `artifacts/research/open-questions.md` |
| Feature Analyst | `.claude/agents/feature-analyst-agent.md` | `artifacts/features/feature-specification.md` (`FEAT-XXX`) |
| User Story Analyst | `.claude/agents/user-story-analyst-agent.md` | `artifacts/stories/user-stories.md` (`US-XXX`) |
| Solution Architect | `.claude/agents/solution-architect-agent.md` | `artifacts/architecture/solution-architecture.md` (`ARCH-XXX`) |
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
| 1 — Requirements Approval | PRD Agent (interview + research as needed) | `APPROVE` / `REQUEST_CHANGES` / `PROVIDE_CLARIFICATION` / `STOP` on the Confirmed PRD |
| 2 — Solution Review | Features, Stories, Architecture, UI/UX | Approval before estimation/risk |
| 3 — Estimate/Risk Review | Estimation & Cost, Risk & Compliance | Approval before final PRD / test strategy |
| 4 — Final PRD Approval | PRD assembly + Test Strategy + validation | Literal `APPROVE_AND_PUBLISH` on both documents together |
| 5 — Confluence Publication | Gate 4 | Explicit confirmation per page; existing pages are never silently overwritten |

## 5. Repository structure

```text
.claude/
  agents/            discovery/planning agents plus the development-to-QA pipeline
  skills/
    product-discovery/SKILL.md   master orchestration procedure (dispatch order, gates)
    validation-review/SKILL.md   consistency/completeness/feasibility/quality-security checklist
    confluence-publish/SKILL.md  MCP verification, search-before-create, CREATE vs UPDATE, publish
  commands/          /product-plan, /orchestrate, /develop, /research, /features, /stories,
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
/features <workflow-id>                     feature analyst only
/stories <workflow-id>                      user story analyst only
/architecture <workflow-id>                 solution architect only
/uiux <workflow-id>                         UI/UX designer only
/estimate <workflow-id>                     estimation & cost only
/risk <workflow-id>                         risk & compliance only -> Gate 3
/test-strategy <workflow-id>                test strategy only (requires Gate 3 approved)
/review <workflow-id>                       validation pass (consistency/completeness/feasibility/quality-security)
/prd <workflow-id>                          assemble final PRD + traceability -> Gate 4
/publish <workflow-id>                      Confluence publication -> Gate 5
/retry <workflow-id> <agent>                retry a failed agent
/skip <workflow-id> <agent>                 skip an agent (requires confirmation)
/status [workflow-id]                       show workflow state
/develop <id> <requirement-path> ...        implement one approved work item through READY_FOR_QA
```

## 9. Example workflow

See `examples/ingredient-demand-forecasting.md` for a demo product statement and a step-by-step walkthrough (`/product-plan examples/ingredient-demand-forecasting.md` through to `/publish`).

## 10. Status tracking

`workflow/status.json` is a registry of every workflow run in this repo (see `.claude/skills/product-discovery/SKILL.md` §1 for the exact schema), keyed by a `WF-<year>-<seq>` workflow ID. The orchestrator is the only writer and uses atomic read-modify-write so status can't be corrupted by concurrent activity. `workflow/events.jsonl` mirrors every state transition as an independent, append-only audit trail.

## 11. Confluence publishing

Publication only happens through `/publish`, which delegates to `.claude/skills/confluence-publish/SKILL.md`, only after Gate 4's literal `APPROVE_AND_PUBLISH`, and only after Gate 5's explicit per-page confirmation. That skill always searches for an existing page before creating one, shows CREATE vs. UPDATE for every page up front, and refuses to overwrite an existing page without approval for that specific page. Published page IDs/URLs are recorded in `workflow/status.json`.

## 12. Security considerations

- Least-privilege tools per agent — see each agent file's `tools:` frontmatter. Specialists get `Read/Grep/Glob/Write` (plus `WebSearch`/`WebFetch` for research); only the orchestrator touches workflow state, and only `/publish` touches Confluence.
- No credentials, tokens, or secrets are stored in this repo; `config/project.yaml` holds only non-secret configuration (site/space/page names, toggles).
- Legal/compliance claims are never asserted without evidence — the Risk & Compliance agent marks items `Requires legal/security review: yes` instead.

## 13. Known limitations

See `SETUP_DECISIONS.md` for the full list, notably:
- No workflow has been run end-to-end yet — the system is built and Confluence connectivity is verified, but no requirements/estimates/risks have been generated or human-reviewed.
- Confluence `space`/`parent_page` are not yet configured — required before the first `/publish`.
- Token/cost metrics aren't exposed to agents in this environment, so `workflow/metrics.json` tracks only timestamps/durations/status counts.
- Whether this session's tooling supports an orchestrator subagent invoking other subagents directly hasn't been exercised yet — see the environment note in `.claude/agents/product-discovery-orchestrator.md`.

## 14. Demo instructions

```text
1. Start Claude Code in this repository.
2. Run: /product-plan examples/ingredient-demand-forecasting.md
3. Answer prd-agent's interview questions (it may pause mid-interview to run research on a gap it can't resolve from your answers alone).
4. Respond to Gate 1 (Requirements Approval) with APPROVE, REQUEST_CHANGES, PROVIDE_CLARIFICATION, or STOP once prd-agent hands back a Confirmed PRD.
5. Respond to Gate 2 (Solution Review) once features/stories/architecture/UI-UX are shown.
6. Respond to Gate 3 (Estimate/Risk Review). test-strategy-agent may ask about existing QA tooling/environments/compliance obligations once this is approved.
7. Review the assembled PRD, test strategy, and traceability matrix at Gate 4; respond APPROVE_AND_PUBLISH to proceed, anything else to stop.
8. Confirm the exact Confluence page list at Gate 5 to publish (PRD and test strategy each land under the project's PRD folder).
9. Check /status <workflow-id> at any point to see where things stand.
```

## 15. Development to QA workflow

Run `/develop <work-item-id> <approved-requirement-path> --architecture <approved-architecture-path> [--repo <path>] [--test-strategy <path>]` after product and architecture approval.

The development orchestrator runs this deterministic sequence:

```text
Requirements validation
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
