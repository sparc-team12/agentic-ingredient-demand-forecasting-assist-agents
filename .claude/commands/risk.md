---
description: Run the Risk & Compliance agent against requirements, features, architecture, UI/UX, and estimates
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `risk_compliance`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. If `estimation_cost` is not `COMPLETED`, stop and explain what's missing. Otherwise dispatch `risk-compliance-agent` (`.claude/agents/risk-compliance-agent.md`) using the requirements baseline, feature specification, solution architecture, UI/UX specification, and estimation/cost analysis. After this completes, run **Gate 4 — Estimate/Risk Review** (`ESTIMATE_RISK_REVIEW`) and stop for human approval.
