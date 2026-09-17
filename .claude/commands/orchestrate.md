---
description: Run only a selected subset of the product discovery agents against an existing (or new) workflow
argument-hint: "--only <agent1,agent2,...> [workflow-id] [requirement]"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **ORCHESTRATE_ONLY**.

Arguments given: `$ARGUMENTS`

Parse the `--only <list>` agent names (from: prd, research, features, architecture, uiux, stories, estimate, risk, test-strategy). If a workflow ID is present in the remaining arguments, target that workflow and reuse its existing artifacts; otherwise create a new workflow (only valid if `prd` is in the list — it's the only entry point that can take raw human input with no prior artifacts). Enforce whatever gate sits between the named agents' required inputs and their approval status, per the dependency order in `.claude/skills/product-discovery/SKILL.md` §2 — do not run an agent whose upstream artifact is not yet human-approved (`stories` requires Gate 2 `APPROVED`; `estimate` requires Gate 3 `APPROVED`; `test-strategy` requires Gate 4 `APPROVED`).
