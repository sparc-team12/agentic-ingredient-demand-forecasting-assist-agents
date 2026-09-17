# agentic-ingredient-demand-forecasting-assist-agents

A human-in-the-loop AI product discovery and planning system, built on Claude Code. You give it a product idea, requirement, ticket, or business problem; a **Product Discovery & Planning Orchestrator** coordinates seven specialist subagents to produce a validated PRD package. Humans approve at defined gates throughout — this system does **not** autonomously build or ship a product; it accelerates discovery and planning while people stay accountable for requirements, architecture, estimates, risk acceptance, and publication.

## 1. What this system does

Given a statement like "Build an ingredient demand forecasting assistant for a multi-location kitchen operator," the orchestrator:

1. Runs research/requirements extraction, then **stops for human approval**.
2. Runs feature decomposition, user stories, solution architecture, and UI/UX in parallel, then **stops for human approval**.
3. Runs estimation/cost and risk/compliance, then **stops for human approval**.
4. Validates everything for consistency, completeness, feasibility, and quality/security.
5. Assembles a final PRD with a full traceability matrix, then **requires the literal `APPROVE_AND_PUBLISH`**.
6. Publishes to Confluence via the Atlassian MCP integration, **only after explicit per-page confirmation**.

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
          +-----------------+-----------------+
          |        |        |        |        |
          v        v        v        v        v
      Research  Feature  User     Solution  UI/UX
      & Req.    Analyst   Story    Architect Designer
      Agent     Agent     Agent    Agent     Agent
          |        |        |        |        |
          +--------+--------+--------+--------+
                            |
                            v
                  Estimation & Cost Agent
                            |
                            v
                     Risk & Compliance
                            |
                            v
              +-----------------------------+
              | ORCHESTRATOR VALIDATION      |
              | Consistency / Completeness / |
              | Feasibility / Quality-Sec.   |
              +-------------+---------------+
                            |
                            v
                    HUMAN APPROVAL
                            |
                            v
                       FINAL PRD
                            |
                            v
                     CONFLUENCE
```

Specialist agents are direct children of the orchestrator — there is no recursive agent tree. The orchestration procedure lives in `.claude/skills/product-discovery/SKILL.md`, which delegates the four-dimension validation checklist to `.claude/skills/validation-review/SKILL.md` and the Confluence publish mechanics to `.claude/skills/confluence-publish/SKILL.md`; every slash command is a thin dispatcher into whichever of the three actually owns the logic it needs.

## 3. Agent responsibilities

| Agent | File | Output |
|---|---|---|
| Product Discovery Orchestrator | `.claude/agents/product-discovery-orchestrator.md` | `workflow/status.json`, `workflow/events.jsonl`, gate management, PRD assembly, Confluence publish |
| Research & Requirements | `.claude/agents/research-requirements-agent.md` | `artifacts/research/requirements-baseline.md`, `artifacts/research/open-questions.md` |
| Feature Analyst | `.claude/agents/feature-analyst-agent.md` | `artifacts/features/feature-specification.md` (`FEAT-XXX`) |
| User Story Analyst | `.claude/agents/user-story-analyst-agent.md` | `artifacts/stories/user-stories.md` (`US-XXX`) |
| Solution Architect | `.claude/agents/solution-architect-agent.md` | `artifacts/architecture/solution-architecture.md` (`ARCH-XXX`) |
| UI/UX Designer | `.claude/agents/uiux-designer-agent.md` | `artifacts/design/ui-ux-specification.md` (`UI-XXX`) |
| Estimation & Cost | `.claude/agents/estimation-cost-agent.md` | `artifacts/estimation/estimation-cost-analysis.md` (`EST-XXX`) |
| Risk & Compliance | `.claude/agents/risk-compliance-agent.md` | `artifacts/risk/risk-register.md` (`RISK-XXX`) |

Each agent file states its input contract, output contract, allowed tools, and what it must **not** decide unilaterally.

## 4. Human-in-the-loop gates

| Gate | After | Requires |
|---|---|---|
| 0 — Intake | Parsing the request | Orchestrator confirms understanding; asks if critical info is missing |
| 1 — Requirements Approval | Research & Requirements | `APPROVE` / `REQUEST_CHANGES` / `PROVIDE_CLARIFICATION` / `STOP` |
| 2 — Solution Review | Features, Stories, Architecture, UI/UX | Approval before estimation/risk |
| 3 — Estimate/Risk Review | Estimation & Cost, Risk & Compliance | Approval before final PRD |
| 4 — Final PRD Approval | PRD assembly + validation | Literal `APPROVE_AND_PUBLISH` |
| 5 — Confluence Publication | Gate 4 | Explicit confirmation per page; existing pages are never silently overwritten |

## 5. Repository structure

```text
.claude/
  agents/            8 subagent definitions (orchestrator + 7 specialists)
  skills/
    product-discovery/SKILL.md   master orchestration procedure (dispatch order, gates)
    validation-review/SKILL.md   consistency/completeness/feasibility/quality-security checklist
    confluence-publish/SKILL.md  MCP verification, search-before-create, CREATE vs UPDATE, publish
  commands/          /product-plan, /orchestrate, /research, /features, /stories,
                      /architecture, /uiux, /estimate, /risk, /review, /status,
                      /prd, /publish, /retry, /skip
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
/product-plan <requirement>                 full gated workflow (new workflow)
/product-plan --resume <workflow-id>        resume from wherever it stopped
/product-plan --agents <a,b,c> <req>        targeted orchestration
/orchestrate --only <a,b,c> [workflow-id]   run only named agents
/research <requirement>                     research/requirements only -> Gate 1
/features <workflow-id>                     feature analyst only
/stories <workflow-id>                      user story analyst only
/architecture <workflow-id>                 solution architect only
/uiux <workflow-id>                         UI/UX designer only
/estimate <workflow-id>                     estimation & cost only
/risk <workflow-id>                         risk & compliance only -> Gate 3
/review <workflow-id>                       validation pass (consistency/completeness/feasibility/quality-security)
/prd <workflow-id>                          assemble final PRD + traceability -> Gate 4
/publish <workflow-id>                      Confluence publication -> Gate 5
/retry <workflow-id> <agent>                retry a failed agent
/skip <workflow-id> <agent>                 skip an agent (requires confirmation)
/status [workflow-id]                       show workflow state
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
3. Respond to Gate 1 (Requirements Approval) with APPROVE, REQUEST_CHANGES, PROVIDE_CLARIFICATION, or STOP.
4. Respond to Gate 2 (Solution Review) once features/stories/architecture/UI-UX are shown.
5. Respond to Gate 3 (Estimate/Risk Review).
6. Review the assembled PRD and traceability matrix at Gate 4; respond APPROVE_AND_PUBLISH to proceed, anything else to stop.
7. Confirm the exact Confluence page list at Gate 5 to publish.
8. Check /status <workflow-id> at any point to see where things stand.
```
