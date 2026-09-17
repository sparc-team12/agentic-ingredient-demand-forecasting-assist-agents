---
description: Run the Feature Analyst agent against an approved requirements baseline
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `feature_analyst`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json` for this workflow. If `research_requirements` is not `COMPLETED` or Gate 1 is not `APPROVED`, stop and explain what's missing instead of proceeding. Otherwise dispatch `feature-analyst-agent` (`.claude/agents/feature-analyst-agent.md`) using the existing `artifacts/research/requirements-baseline.md`, and report the result — this command does not by itself advance past Gate 2.
