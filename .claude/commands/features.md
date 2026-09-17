---
description: Run the Feature Analyst agent against an approved requirements baseline
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `feature_analyst`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json` for this workflow. If `prd_agent` is not `COMPLETED` or Gate 1 (`REQUIREMENTS_APPROVAL`) is not `APPROVED`, stop and explain what's missing instead of proceeding. Otherwise dispatch `feature-analyst-agent` (`.claude/agents/feature-analyst-agent.md`) using the existing `artifacts/prd/prd-<slug>.md` (plus `artifacts/research/requirements-baseline.md` if present), and report the result. In the full pipeline this runs in parallel with `solution-architect-agent` — this command does not by itself advance past Gate 2 (`FEATURE_ARCHITECTURE_UIUX_REVIEW`).
