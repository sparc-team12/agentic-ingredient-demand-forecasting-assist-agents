---
description: Run the Estimation & Cost agent against requirements, features, architecture, UI/UX, and user stories
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `estimation_cost`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. Require Gate 3 (`USER_STORIES_REVIEW`) to be `APPROVED` — if not, stop and explain what's pending. Otherwise dispatch `estimation-cost-agent` (`.claude/agents/estimation-cost-agent.md`) using the requirements baseline, feature specification, solution architecture, UI/UX specification, and `artifacts/stories/user-stories.md`. Report the result as ranges/assumptions, never as fixed facts.
