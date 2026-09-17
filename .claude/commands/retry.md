---
description: Retry a failed specialist agent with the same inputs
argument-hint: "<workflow-id> <agent-key>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **RETRY** (§5).

Arguments given: `$ARGUMENTS` (expected: `<workflow-id> <agent-key>`, agent-key one of `prd_agent, research_requirements, feature_analyst, user_story_analyst, solution_architect, uiux_designer, estimation_cost, risk_compliance`)

Reset the named agent's status to `QUEUED`, increment its `revisionCount` in `status.json`, log the retry event, and re-dispatch it with the same input artifacts it originally used.
