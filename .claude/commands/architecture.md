---
description: Run the Solution Architect agent against requirements, features, and user stories
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `solution_architect`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. If `feature_analyst` is not `COMPLETED`, stop and explain what's missing. Otherwise dispatch `solution-architect-agent` (`.claude/agents/solution-architect-agent.md`) using the requirements baseline, feature specification, and user stories if available (note the gap if stories don't exist yet). Report the result, and flag any irreversible technology decision that needs explicit human sign-off.
