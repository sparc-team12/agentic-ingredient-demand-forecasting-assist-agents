---
description: Run the User Story Analyst agent against requirements and the feature specification
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `user_story_analyst`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. If `feature_analyst` is not `COMPLETED`, stop and explain what's missing. Otherwise dispatch `user-story-analyst-agent` (`.claude/agents/user-story-analyst-agent.md`) using `artifacts/research/requirements-baseline.md` and `artifacts/features/feature-specification.md`, and report the result.
