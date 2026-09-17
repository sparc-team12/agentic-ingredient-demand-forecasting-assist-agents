---
description: Run the Research & Requirements agent for a new product/problem statement
argument-hint: "<requirement text or path to a document>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `research_requirements`.

Requirement/input given: `$ARGUMENTS`

Note: in the full `/product-plan` workflow, `research_requirements` is normally dispatched by `prd_agent` itself, mid-interview, not run standalone first — Gate 1 gates on `prd_agent`'s `Confirmed` PRD, not on this command's output directly. Use this command for an ad hoc research pass (e.g. `prd_agent` requesting it, or a human wanting research without a full interview).

If no existing workflow matches this input, create a new workflow ID first. Dispatch `research-requirements-agent` (`.claude/agents/research-requirements-agent.md`) and report its output — do not run Gate 1 from this command, since that gate belongs to the `Confirmed` PRD, not to a standalone research pass. Do not dispatch any other specialist from this command.
