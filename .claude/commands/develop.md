---
description: Run the approved development workflow through implementation, review, verification, and QA handoff
argument-hint: "<work-item-id> <requirement-or-ticket-path> [--repo <path>] [--architecture <path>] [--test-strategy <path>] | --resume <work-item-id>"
---

Load and follow `.claude/agents/dev-orchestrator-agent.md`.

Arguments given: `$ARGUMENTS`

- With `--resume <work-item-id>`, read `artifacts/development/<normalized-work-item-id>/dev-status.json`, verify existing artifacts, and continue from the first incomplete/failed stage. Never skip a failed gate.
- Otherwise parse the work item ID, requirement source, repository root (default: current repository), approved architecture source, and optional test strategy source.
- If architecture is omitted, use `artifacts/architecture/solution-architecture.md` only when its metadata says human approval is `APPROVED`; otherwise stop and request the approved source.

Run through `READY_FOR_QA`, then stop. Do not create a PR, deploy, or execute QA-owned e2e scenarios.
