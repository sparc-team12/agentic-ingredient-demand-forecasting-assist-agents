---
description: Assemble the final PRD package with traceability matrix for a workflow that has passed Gate 5
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **PRD** (§7).

Workflow ID given: `$ARGUMENTS`

Require Gate 5 (`TEST_STRATEGY_REVIEW`) to be `APPROVED` — if not, stop and explain what's pending. Otherwise run the Validation procedure (§6), then assemble `artifacts/prd/final-prd.md` with the traceability matrix (including each `US-XXX` story's Jira issue key/URL) and decision log, and present it at **Gate 6 — Final PRD Approval**, requiring the literal response `APPROVE_AND_PUBLISH` before any publication step runs.
