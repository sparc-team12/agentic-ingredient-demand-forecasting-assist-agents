---
description: Initialize or verify a project boilerplate from the approved technology stack, HLD, LLD, and architecture validation
argument-hint: "<project-id> --target <path> [--name <name>] [--architecture <path>] [--tech-stack <path>] [--hld <path>] [--lld <path>] [--validation <path>]"
---

Load and follow `.claude/agents/dev-scaffold-agent.md`.

Arguments: `$ARGUMENTS`

Require a project ID and explicit `--target`. Defaults for design inputs are:

- `artifacts/architecture/solution-architecture.md`
- `artifacts/architecture/tech-stack.md`
- `artifacts/architecture/high-level-design.md`
- `artifacts/architecture/low-level-design.md`
- `artifacts/architecture/architecture-validation.json`

Use `artifacts/development/<normalized-project-id>/` as `artifact_dir`. Normalize only the artifact directory name; preserve the original ID in the report.

Do not initialize from draft/stale design, overwrite a non-empty conflicting target, run git initialization, create a remote, or implement features. Finish only when `project-initialization.json` is `PASS`, or report the exact blocker.
