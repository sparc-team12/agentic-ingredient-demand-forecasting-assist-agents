# Repository: agentic-ingredient-demand-forecasting-assist-agents

This repository is a **human-gated AI product discovery & planning system** built on Claude Code, per `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md`. It is domain-agnostic tooling; the demo domain used in `examples/` is an ingredient demand forecasting assistant, but the workflow itself applies to any product/problem statement.

## Governing principle

AI accelerates product discovery and SDLC planning. Humans remain the decision authority for requirements, architecture, estimates, risk acceptance, and publication. **When in doubt between more autonomy and a human checkpoint, choose the checkpoint.** Never treat "agent completed" as "human approved." Never publish to Confluence without the explicit gates in `.claude/skills/product-discovery/SKILL.md` §4 and §8.

## Where things live

- `.claude/agents/orchestrator-agent.md` — the canonical orchestrator for the **discovery pipeline and the Architecture Suite/HLD/LLD workflow**. It is the only agent that dispatches those specialists and the only agent in this repository with Confluence/Jira MCP access. No agent file it dispatches may contain logic that decides to invoke another agent — see its "Hard rules" and this file's "Known scope boundary" note below.
- `.claude/agents/` also holds `prd-agent` (entry point: interviews the human and produces the Confirmed PRD gated at Gate 1, dispatched by `orchestrator-agent`) + the specialist subagents for the discovery pipeline (research, features, stories, architecture, UI/UX, estimation, risk, test strategy) + the Architecture Suite/HLD/LLD specialists (`solution-architecture-overview-agent`, `solution-security-architecture-agent`, `solution-tech-stack-agent`, `solution-hld-agent`, `solution-lld-agent`, `solution-architecture-validator-agent`), reached via `/generate-architecture`.
- `.claude/agents/dev-orchestrator-agent.md` — a second, independently-gated orchestrator for development, reached via `/develop`: requirements validation → planning → tech-lead review → implementation → unit tests → code review → verification → QA handoff, tracked in its own `<artifact_dir>/dev-status.json` (not `workflow/status.json`). See "Known scope boundary" below for how these two orchestrators relate.
- `.claude/skills/product-discovery/SKILL.md` — the full orchestration procedure: dispatch order, gate behavior, PRD assembly, test strategy generation, and the Architecture Suite/HLD/LLD workflow (§7b). Every command below delegates here (directly, or via one of the two skills below).
- `.claude/skills/validation-review/SKILL.md` — the consistency/completeness/feasibility/quality-security checklist, used standalone by `/review` and by `product-discovery` before Gate 6.
- `.claude/skills/confluence-publish/SKILL.md` — MCP verification, search-before-create, CREATE vs UPDATE, and the actual publish calls, used by `/publish` and by `product-discovery`'s Gate 5.
- `.claude/commands/` — discovery pipeline: `/product-plan`, `/orchestrate`, `/research`, `/features`, `/stories`, `/architecture`, `/uiux`, `/estimate`, `/risk`, `/test-strategy`, `/review`, `/status`, `/prd`, `/publish`, `/retry`, `/skip`. Architecture Suite/HLD/LLD (same orchestrator): `/generate-architecture`. Development (separate orchestrator): `/develop`.
- `workflow/status.json` — single source of truth for workflow state (only the orchestrator writes it).
- `workflow/events.jsonl` — append-only audit log.
- `workflow/decisions.md` — human decision log.
- `artifacts/` — specialist output, organized by domain (research/features/stories/architecture/design/estimation/risk/prd/test-strategy). Nothing here is pre-populated with fabricated content.
- `artifacts/development/<work-item-id>/` — per-work-item development evidence. `/develop` owns the sequence and stops at `READY_FOR_QA`; it does not create a PR or deploy.
- `artifacts/architecture/high-level-design.md` and `low-level-design.md` — approved HLD/LLD bridge between solution architecture and development; `architecture-validation.json` must declare the current pair development-ready.
- `config/project.yaml` — Confluence target (site/space/parent page) and workflow toggles. No secrets belong here.
- `examples/ingredient-demand-forecasting.md` — demo input for `/product-plan`.
- `SETUP_DECISIONS.md` — decisions made while building this system itself (not workflow decisions — those go in `workflow/decisions.md`).

## Hard rules for anyone (human or agent) working in this repo

- Never fabricate research, estimates, metrics, approvals, or Confluence connectivity status.
- Never convert an assumption into a requirement without flagging it as an assumption.
- Every feature/story/architecture/design/UI/estimate/risk/test-strategy item gets a stable ID (`FEAT-`, `US-`, `ARCH-`, `HLD-`, `LLD-`, `UI-`, `EST-`, `RISK-`, `TS-`) and traces back to its source.
- Never overwrite an existing Confluence page without explicit human approval for that specific page.
- Do not commit API tokens, passwords, OAuth secrets, or personal credentials anywhere in this repo.
- Development must use the canonical `.claude/agents/dev-orchestrator-agent.md` workflow. Do not mix its per-work-item artifacts with the retired root-level numbered artifact convention.
- Development must not start from solution architecture alone. Approved HLD, approved LLD, and matching architecture validation are hard prerequisites.
- A development stage may advance only on an explicit `PASS` artifact for the same work item and plan checksum. `COMPLETED` is not synonymous with reviewed or QA-ready.
- `READY_FOR_QA` is the terminal development state. QA/e2e, PR, release, and deployment require their own explicit workflow and evidence.
- Confluence access in this environment goes through the **claude.ai Atlassian Rovo** MCP connector tools (`mcp__claude_ai_Atlassian_Rovo__*`) — do not assume a different MCP server/tool name without checking what's actually configured.

## Known scope boundary — two orchestrators, not one, and why

This repository currently has **two** independently-gated orchestrators, not the single one earlier consolidation passes aimed for — `orchestrator-agent` (discovery pipeline **and** the Architecture Suite/HLD/LLD workflow, per explicit direction to fold that bridge in) and `dev-orchestrator-agent` (development, through `READY_FOR_QA`). Folding `dev-orchestrator-agent` in too was explicitly deferred, not forgotten — development is a distinct, larger surface, and the call was to consolidate the architecture bridge first and revisit development separately. Until that's revisited:

- Each orchestrator gates its own pipeline fully (real human-approval gates, real state tracking) — `orchestrator-agent` uses `workflow/status.json`; `dev-orchestrator-agent` uses its own `<artifact_dir>/dev-status.json`. Neither reads or writes the other's state; `orchestrator-agent` only hands off approved architecture/HLD/LLD paths to `dev-orchestrator-agent` (see its "Development handoff" section), it does not dispatch it.
- The **change-request pipeline** — `prd-change-request-agent` → `prd-change-request-validator-agent` → `solution-architecture-validator-agent` → `dev-developer-artifact-agent` → `code-review-independent-agent` → `test-verifier-agent` — remains the older, ungated, unwired chain (no real state tracking, no human-approval gate) it always was; it is not part of `dev-orchestrator-agent`'s real pipeline.
- **Release/deploy** (`release-pr-agent`, `release-deploy-agent`) remain out of scope for both orchestrators — `dev-orchestrator-agent` stops at `READY_FOR_QA` by design; QA/e2e, PR, release, and deployment need their own explicit workflow and evidence.

Do not assume either of these two items is wired into `orchestrator-agent` or `workflow/status.json` just because a nearby, better-developed pipeline now is.
