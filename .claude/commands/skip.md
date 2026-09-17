---
description: Skip a failed or unnecessary specialist agent, with mandatory human confirmation
argument-hint: "<workflow-id> <agent-key>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SKIP** (§5).

Arguments given: `$ARGUMENTS` (expected: `<workflow-id> <agent-key>`)

Before doing anything, list every downstream agent and gate that depends on this agent's output, and what will be missing or degraded in the final PRD if it's skipped. Only mark the agent `SKIPPED` in `status.json` after the human explicitly confirms, and log the decision to `workflow/decisions.md`.
