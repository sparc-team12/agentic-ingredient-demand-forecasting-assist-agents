---
description: Run the UI/UX Designer agent against requirements, features, and user stories
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `uiux_designer`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. If `feature_analyst` is not `COMPLETED`, stop and explain what's missing — this agent's contract requires a feature-level breakdown to exist first. Otherwise dispatch `uiux-designer-agent` (`.claude/agents/uiux-designer-agent.md`) using the requirements baseline and feature specification (user stories don't exist yet at this point in the pipeline — that's expected; this agent's contract already treats them as optional). Report the result — never claim a visual design/mockup was produced unless a real design/image capability was actually used.
