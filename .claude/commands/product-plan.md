---
description: Run the full human-gated product discovery workflow for a requirement (or resume/target a subset)
argument-hint: "<requirement text or path> | --resume <workflow-id> | --agents <a,b,c> <requirement>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`.

Arguments given: `$ARGUMENTS`

Parse the arguments:
- If they start with `--resume <workflow-id>`, run mode **RESUME** for that workflow ID.
- Else if they contain `--agents <list>`, run mode **ORCHESTRATE_ONLY** with that agent list against a new or (if a workflow id is also given) existing workflow.
- Otherwise treat the full argument string as the product/problem statement and run mode **FULL**, creating a new workflow.

Follow every gate in the skill exactly (do not skip Gate 1 before dispatching downstream agents). Stop and wait for the human at each gate rather than assuming approval.
