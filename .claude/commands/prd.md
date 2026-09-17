---
description: Assemble the final PRD package with traceability matrix for a workflow that has passed Gate 3
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **PRD** (§7).

Workflow ID given: `$ARGUMENTS`

Require Gate 3 (`ESTIMATE_RISK_REVIEW`) to be `APPROVED` — if not, stop and explain what's pending. Otherwise run the Validation procedure (§6), then assemble `artifacts/prd/final-prd.md` with the traceability matrix and decision log, and present it at **Gate 4 — Final PRD Approval**, requiring the literal response `APPROVE_AND_PUBLISH` before any publication step runs.
