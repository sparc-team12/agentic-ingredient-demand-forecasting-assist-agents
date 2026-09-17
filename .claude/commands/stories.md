---
description: Run the User Story Analyst agent against requirements, features, architecture, and UI/UX — after Gate 2
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `user_story_analyst`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. Require Gate 2 (`FEATURE_ARCHITECTURE_UIUX_REVIEW`) to be `APPROVED` — if not, stop and explain what's pending. Otherwise dispatch `user-story-analyst-agent` (`.claude/agents/user-story-analyst-agent.md`) using `artifacts/prd/prd-<slug>.md`, `artifacts/features/feature-specification.md`, `artifacts/architecture/solution-architecture.md`, and `artifacts/design/ui-ux-specification.md` — the last two are extra context the orchestrator provides on top of that agent's own documented input contract (its file is not modified), and report the result. This command does not itself run Gate 3 or publish anything to Jira — that happens in the full pipeline.
