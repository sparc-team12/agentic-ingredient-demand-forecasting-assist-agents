---
description: Run only a selected subset of the product discovery agents against an existing (or new) workflow
argument-hint: "--only <agent1,agent2,...> [workflow-id] [requirement]"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **ORCHESTRATE_ONLY**.

Arguments given: `$ARGUMENTS`

Parse the `--only <list>` agent names (from: research, features, stories, architecture, uiux, estimate, risk). If a workflow ID is present in the remaining arguments, target that workflow and reuse its existing artifacts; otherwise create a new workflow (only valid if `research` is in the list). Enforce whatever gate sits between the named agents' required inputs and their approval status — do not run an agent whose upstream artifact is not yet human-approved.
