# Repository: agentic-ingredient-demand-forecasting-assist-agents

This repository is a **human-gated AI product discovery, architecture, and development system** built on Claude Code. It is domain-agnostic tooling; the demo domain is an ingredient demand forecasting assistant.

## Governing principle

AI accelerates discovery, architecture, and development. Humans remain the decision authority for requirements, architecture, estimates, risk acceptance, publication, and release. Never treat “agent completed” as “human approved,” and never publish without the gates in `.claude/skills/product-discovery/SKILL.md`.

## Where things live

- `.claude/agents/orchestrator-agent.md` — canonical orchestrator for the discovery pipeline and Architecture Suite/HLD/LLD workflow. It is the only agent in those workflows with Confluence/Jira write access.
- `.claude/agents/` — discovery specialists plus Architecture Suite/HLD/LLD specialists (`solution-architecture-overview-agent`, `solution-security-architecture-agent`, `solution-tech-stack-agent`, `solution-hld-agent`, `solution-lld-agent`, `solution-architecture-validator-agent`).
- `.claude/agents/dev-orchestrator-agent.md` — separate development orchestrator reached through `/develop`: greenfield initialization/verification → requirements validation → planning → tech-lead review → implementation → unit tests → code review → verification → QA handoff.
- `.claude/skills/product-discovery/SKILL.md` — discovery orchestration and Architecture Suite/HLD/LLD procedure (§7b).
- `.claude/skills/validation-review/SKILL.md` — reusable consistency, completeness, feasibility, and quality/security validation.
- `.claude/skills/confluence-publish/SKILL.md` — search-before-create, CREATE/UPDATE confirmation, and Confluence publication.
- `.claude/commands/` — discovery commands, `/generate-architecture`, `/init-project`, and `/develop`.
- `workflow/status.json`, `workflow/events.jsonl`, `workflow/decisions.md` — discovery/architecture workflow state, audit events, and decisions. Only `orchestrator-agent` writes discovery/architecture state.
- `artifacts/architecture/` — solution architecture, overview, security architecture, technology stack, HLD, LLD, and architecture validation.
- `artifacts/development/<work-item-id>/` — project initialization and per-work-item development evidence. `/develop` stops at `READY_FOR_QA`.
- `config/project.yaml` — non-secret project, Confluence, Jira, and workflow configuration.

## Hard rules

- Never fabricate research, estimates, metrics, command results, approvals, or Confluence/Jira connectivity.
- Never convert an assumption into a requirement without labeling it.
- Every artifact item uses a stable ID (`REQ-`, `FEAT-`, `US-`, `ARCH-`, `HLD-`, `LLD-`, `UI-`, `EST-`, `RISK-`, `TS-`) and traces to its source.
- Never overwrite a Confluence page or Jira issue without the workflow’s explicit human confirmation.
- Never commit credentials or secrets.
- Development uses `.claude/agents/dev-orchestrator-agent.md`; do not mix it with the retired numbered-artifact pipeline.
- Development cannot start from solution architecture alone. Approved HLD, approved LLD, and matching `architecture-validation.json` are mandatory.
- Greenfield development must pass `dev-scaffold-agent` and produce `project-initialization.json`. Existing compatible repositories skip initialization and must not be overwritten.
- A development stage advances only on a matching explicit `PASS` artifact. `COMPLETED` does not mean reviewed or QA-ready.
- `READY_FOR_QA` is the terminal development state. QA/e2e, PR, release, and deployment require separate explicit workflows and evidence.

## Known scope boundary

There are two independently gated orchestrators:

- `orchestrator-agent` owns discovery and Architecture Suite/HLD/LLD, tracked in `workflow/status.json`.
- `dev-orchestrator-agent` owns development through `READY_FOR_QA`, tracked in `<artifact_dir>/dev-status.json`.

The architecture orchestrator hands approved architecture/HLD/LLD paths to development but does not dispatch or control development. The older numbered change-request chain is retained only for compatibility and is not part of the canonical workflow. `release-pr-agent` and `release-deploy-agent` are not wired into either orchestrator; PR, QA, release, and deployment remain separate gated work.
