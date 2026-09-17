---
description: Show the current status of one workflow, or list all workflows
argument-hint: "[workflow-id]"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **STATUS**.

Argument given: `$ARGUMENTS`

If a workflow ID is given, read `workflow/status.json` and render: overall status, current gate, per-agent status table, open questions, and recent events for that workflow. If no argument is given, list every workflow in `workflow/status.json` with its ID, name, overall status, and current gate.
