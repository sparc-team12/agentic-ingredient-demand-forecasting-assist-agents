---
description: Run the lightweight consistency/completeness/feasibility/quality-security validation pass against current artifacts
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/validation-review/SKILL.md` directly (this command doesn't need the full orchestration procedure, just the checklist).

Workflow ID given: `$ARGUMENTS`

Check whatever artifacts currently exist for this workflow against the four validation dimensions (consistency, completeness, feasibility, quality/security). Report findings only — do not modify any already human-approved artifact. If a finding implies a needed change, say which human gate it should route back through.
