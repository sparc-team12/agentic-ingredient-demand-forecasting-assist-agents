---
description: Run the Research & Requirements agent for a new product/problem statement
argument-hint: "<requirement text or path to a document>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md`, mode **SINGLE_AGENT** for `research_requirements`.

Requirement/input given: `$ARGUMENTS`

If no existing workflow matches this input, create a new workflow ID first. Dispatch `research-requirements-agent` (`.claude/agents/research-requirements-agent.md`), then run **Gate 1 — Requirements Approval** and stop for the human's decision (`APPROVE` / `REQUEST_CHANGES` / `PROVIDE_CLARIFICATION` / `STOP`). Do not dispatch any other specialist from this command.
