---
description: Run the UI/UX Designer agent against requirements, features, and user stories
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `uiux_designer`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. If `feature_analyst` is not `COMPLETED`, stop and explain what's missing. Otherwise dispatch `uiux-designer-agent` (`.claude/agents/uiux-designer-agent.md`) using the requirements baseline, feature specification, and user stories if available (note the gap if stories don't exist yet). Report the result — never claim a visual design/mockup was produced unless a real design/image capability was actually used.
