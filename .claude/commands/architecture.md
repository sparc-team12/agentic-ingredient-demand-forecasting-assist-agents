---
description: Run the Solution Architect agent against requirements, features, and user stories
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `solution_architect`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. Require Gate 1 (`REQUIREMENTS_APPROVAL`) to be `APPROVED` — if not, stop and explain what's pending. Otherwise dispatch `solution-architect-agent` (`.claude/agents/solution-architect-agent.md`) using the approved PRD and requirements baseline (this agent needs only the PRD; in the full pipeline it runs in parallel with `feature-analyst-agent`, so a feature specification or user stories won't exist yet — that's expected, not a gap to report). Report the result, and flag any irreversible technology decision that needs explicit human sign-off.
