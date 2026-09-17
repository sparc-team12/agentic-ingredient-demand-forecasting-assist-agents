---
description: Run the Test Strategy agent against the approved PRD, features, stories, architecture, UI/UX spec, and risk register
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `test_strategy`.

Workflow ID given: `$ARGUMENTS`

Read `workflow/status.json`. Require Gate 4 (`ESTIMATE_RISK_REVIEW`) to be `APPROVED` — if not, stop and explain what's pending; a test strategy written against an unapproved risk register will need redoing the moment risk severities change. Otherwise dispatch `test-strategy-agent` (`.claude/agents/test-strategy-agent.md`) using the PRD, feature specification, user stories, solution architecture, UI/UX specification, and risk register — by this point in the pipeline all of these exist. It will ask the human directly for QA-specific context (tooling, environments, regulatory obligations, team maturity) no artifact captures. This command does not by itself run Gate 5 (`TEST_STRATEGY_REVIEW`); the resulting document is presented there, then folded into the final PRD assembly as a summary + link.
