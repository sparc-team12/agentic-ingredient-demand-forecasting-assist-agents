---
description: Generate and approve the complete architecture package—solution architecture, security, technology stack, HLD, LLD, and validation—then optionally publish it.
argument-hint: "[workflow-id] [--repo <target-repository>]"
---

# Generate Architecture

Build the complete implementation-ready architecture package before `/develop` is allowed.

Arguments: `$ARGUMENTS`

## 1. Resolve the approved PRD

1. Prefer `config/project.yaml` → `confluence.prd_local_path` when it exists.
2. Otherwise resolve exactly one `docs/01-prd/prd-*.md`.
3. If no local PRD exists, use `.claude/skills/confluence-doc-resolver/SKILL.md` with the configured URL/name, then restore the resolved document locally.
4. Require `Status: Confirmed`. Stop on a draft or ambiguous PRD.

## 2. Generate and approve engineering solution architecture

If `artifacts/architecture/solution-architecture.md` is not already human-approved, dispatch `solution-architect-agent`, present all high-impact/irreversible choices, and require `APPROVE`, `REQUEST_CHANGES`, or `STOP`. Only explicit approval updates `Human approval status: APPROVED`.

## 3. Generate HLD and LLD suite

Dispatch `.claude/agents/solution-architecture-suite-orchestrator-agent.md` with the resolved inputs and `--repo` target when supplied. It owns this dependency chain:

```text
Architecture Overview + Security Architecture + Technology Stack (parallel)
  -> High-Level Design
  -> Low-Level Design
  -> Independent Architecture Validation
  -> Human approval of all five documents
  -> DEVELOPMENT_READY
```

Do not dispatch HLD and LLD in parallel, skip validation, or treat earlier solution-architecture approval as approval of these implementation designs.

## 4. Optional publication

After the suite's human gate passes, offer Confluence publication of the five-page set. Publication requires the configured site/space/parent and the `confluence-publish` skill's per-page CREATE/UPDATE confirmation. Lack of Confluence access does not invalidate locally approved architecture or development readiness.

## Report

Report the PRD source; solution architecture, overview, security, stack, HLD, LLD, and validation paths/statuses; outstanding security/TBD items; human gate decision; target repository; development eligibility; and publication URLs if published.
