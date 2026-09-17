# Repository: agentic-ingredient-demand-forecasting-assist-agents

This repository is a **human-gated AI product discovery & planning system** built on Claude Code, per `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md`. It is domain-agnostic tooling; the demo domain used in `examples/` is an ingredient demand forecasting assistant, but the workflow itself applies to any product/problem statement.

## Governing principle

AI accelerates product discovery and SDLC planning. Humans remain the decision authority for requirements, architecture, estimates, risk acceptance, and publication. **When in doubt between more autonomy and a human checkpoint, choose the checkpoint.** Never treat "agent completed" as "human approved." Never publish to Confluence without the explicit gates in `.claude/skills/product-discovery/SKILL.md` §4 and §8.

## Where things live

- `.claude/agents/orchestrator-agent.md` — the single canonical orchestrator for this repository. It is the only agent that dispatches other specialist agents and the only agent with Confluence/Jira MCP access. No other agent file may contain logic that decides to invoke another agent — see its "Hard rules" and this file's "Known scope boundary" note below.
- `.claude/agents/` also holds `prd-agent` (entry point: interviews the human and produces the Confirmed PRD gated at Gate 1, dispatched by the orchestrator) + the specialist subagents for the discovery pipeline (research, features, stories, architecture, UI/UX, estimation, risk, test strategy) and the Architecture Suite workflow (solution-architecture-overview, solution-security-architecture, solution-tech-stack). Each file is the authoritative input/output contract for that agent, not a place to add dispatch decisions.
- `.claude/skills/product-discovery/SKILL.md` — the full orchestration procedure: dispatch order, gate behavior, PRD assembly, test strategy generation. Every command below delegates here (directly, or via one of the two skills below).
- `.claude/skills/validation-review/SKILL.md` — the consistency/completeness/feasibility/quality-security checklist, used standalone by `/review` and by `product-discovery` before Gate 6.
- `.claude/skills/confluence-publish/SKILL.md` — MCP verification, search-before-create, CREATE vs UPDATE, and the actual publish calls, used by `/publish` and by `product-discovery`'s Gate 5.
- `.claude/commands/` — `/product-plan`, `/orchestrate`, `/research`, `/features`, `/stories`, `/architecture`, `/uiux`, `/estimate`, `/risk`, `/test-strategy`, `/review`, `/status`, `/prd`, `/publish`, `/retry`, `/skip`.
- `workflow/status.json` — single source of truth for workflow state (only the orchestrator writes it).
- `workflow/events.jsonl` — append-only audit log.
- `workflow/decisions.md` — human decision log.
- `artifacts/` — specialist output, organized by domain (research/features/stories/architecture/design/estimation/risk/prd/test-strategy). Nothing here is pre-populated with fabricated content.
- `config/project.yaml` — Confluence target (site/space/parent page) and workflow toggles. No secrets belong here.
- `examples/ingredient-demand-forecasting.md` — demo input for `/product-plan`.
- `SETUP_DECISIONS.md` — decisions made while building this system itself (not workflow decisions — those go in `workflow/decisions.md`).

## Hard rules for anyone (human or agent) working in this repo

- Never fabricate research, estimates, metrics, approvals, or Confluence connectivity status.
- Never convert an assumption into a requirement without flagging it as an assumption.
- Every feature/story/architecture/UI/estimate/risk/test-strategy item gets a stable ID (`FEAT-`, `US-`, `ARCH-`, `UI-`, `EST-`, `RISK-`, `TS-`) and traces back to its source.
- Never overwrite an existing Confluence page without explicit human approval for that specific page.
- Do not commit API tokens, passwords, OAuth secrets, or personal credentials anywhere in this repo.
- Confluence access in this environment goes through the **claude.ai Atlassian Rovo** MCP connector tools (`mcp__claude_ai_Atlassian_Rovo__*`) — do not assume a different MCP server/tool name without checking what's actually configured.

## Known scope boundary — agents not yet wired into the orchestrator

`.claude/agents/` also contains two agent chains ported from other projects that are **not** wired into `orchestrator-agent` or `workflow/status.json`, and have no human-approval gates today. This is a known, intentional boundary — not an oversight — for the current consolidation pass:

- **Ported SDLC pipeline**: `docs-knowledge-agent` → `planning-sprint-agent` → `dev-tech-lead-agent` → `dev-developer-agent` / `dev-developer-artifact-agent` → `code-review-agent` / `code-review-independent-agent` → `test-unit-agent` / `test-verifier-agent` → `release-pr-agent` / `release-deploy-agent`.
- **Change-request pipeline**: `prd-change-request-agent` → `prd-change-request-validator-agent` → `solution-architecture-validator-agent` → `dev-developer-artifact-agent` → `code-review-independent-agent` → `test-verifier-agent`.

Do not invoke these expecting the Gate 0–5 protections that apply to the discovery pipeline and the Architecture Suite workflow — they currently run ungated, with no `workflow/status.json` tracking. Bringing them under `orchestrator-agent` as additional workflow types is a follow-up, not something this pass claims to have done.
