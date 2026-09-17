# Repository: agentic-ingredient-demand-forecasting-assist-agents

This repository is a **human-gated AI product discovery & planning system** built on Claude Code, per `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md`. It is domain-agnostic tooling; the demo domain used in `examples/` is an ingredient demand forecasting assistant, but the workflow itself applies to any product/problem statement.

## Governing principle

AI accelerates product discovery and SDLC planning. Humans remain the decision authority for requirements, architecture, estimates, risk acceptance, and publication. **When in doubt between more autonomy and a human checkpoint, choose the checkpoint.** Never treat "agent completed" as "human approved." Never publish to Confluence without the explicit gates in `.claude/skills/product-discovery/SKILL.md` §4 and §8.

## Where things live

- `.claude/agents/` — discovery/planning agents plus the development pipeline. `dev-orchestrator-agent` is the development entry point and coordinates validation, planning, tech-lead review, implementation, unit tests, independent review, verification, and the QA handoff. Each file is the authoritative input/output contract for that agent.
- `.claude/skills/product-discovery/SKILL.md` — the full orchestration procedure: dispatch order, gate behavior, PRD assembly, test strategy generation. Every command below delegates here (directly, or via one of the two skills below).
- `.claude/skills/validation-review/SKILL.md` — the consistency/completeness/feasibility/quality-security checklist, used standalone by `/review` and by `product-discovery` before Gate 4.
- `.claude/skills/confluence-publish/SKILL.md` — MCP verification, search-before-create, CREATE vs UPDATE, and the actual publish calls, used by `/publish` and by `product-discovery`'s Gate 5.
- `.claude/commands/` — `/product-plan`, `/orchestrate`, `/research`, `/features`, `/stories`, `/architecture`, `/uiux`, `/estimate`, `/risk`, `/test-strategy`, `/review`, `/status`, `/prd`, `/publish`, `/retry`, `/skip`.
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
