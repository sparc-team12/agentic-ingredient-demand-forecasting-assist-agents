---
description: Run development from approved HLD/LLD through implementation, review, verification, and QA handoff
argument-hint: "<work-item-id> <requirement-path> [--repo <path>] [--architecture <path>] [--hld <path>] [--lld <path>] [--architecture-validation <path>] [--test-strategy <path>] | --resume <work-item-id>"
---

Load and follow `.claude/agents/dev-orchestrator-agent.md`.

Arguments given: `$ARGUMENTS`

- With `--resume <work-item-id>`, read `artifacts/development/<normalized-work-item-id>/dev-status.json`, verify existing artifacts, and continue from the first incomplete/failed stage. Never skip a failed gate.
- Otherwise parse the work item ID, requirement source, repository root (default: current repository), approved solution architecture, HLD, LLD, architecture validation, and optional test strategy.
- Defaults are `artifacts/architecture/solution-architecture.md`, `artifacts/architecture/high-level-design.md`, `artifacts/architecture/low-level-design.md`, and `artifacts/architecture/architecture-validation.json`.
- Require approved HLD and LLD plus validation `PASS` / `development_ready: true`. If any are absent, stale, or draft, stop and direct the user to `/generate-architecture`.
- If the repository is missing or empty, run the project-initialization stage using `dev-scaffold-agent`. If it is an existing compatible project, record that stage as `SKIPPED`; never overlay boilerplate on conflicting files.

Run through `READY_FOR_QA`, then stop. Do not create a PR, deploy, or execute QA-owned e2e scenarios.
