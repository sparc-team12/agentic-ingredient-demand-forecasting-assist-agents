---
description: Run the Estimation & Cost agent against requirements, features, architecture, and UI/UX
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `estimation_cost`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. Require Gate 2 (`SOLUTION_REVIEW`) to be `APPROVED` — if not, stop and explain what's pending. Otherwise dispatch `estimation-cost-agent` (`.claude/agents/estimation-cost-agent.md`) using the requirements baseline, feature specification, solution architecture, and UI/UX specification. Report the result as ranges/assumptions, never as fixed facts.
