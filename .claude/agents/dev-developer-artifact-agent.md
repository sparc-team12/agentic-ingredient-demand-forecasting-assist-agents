---
name: dev-developer-artifact-agent
description: Legacy compatibility alias for old numbered-artifact workflows. Do not select for new work; use dev-developer-agent through dev-orchestrator-agent.
tools: Read
---

# Legacy Developer Agent Alias

This definition is retained only so older references fail safely instead of selecting a second, conflicting implementation workflow.

For all new work, dispatch `.claude/agents/dev-developer-agent.md` through `.claude/agents/dev-orchestrator-agent.md`. The canonical workflow stores artifacts under `artifacts/development/<work-item-id>/` and does not use root-level `01-jira.md` through `08-pr.md` files.

If invoked, do not modify code. Return `BLOCKED` with the migration instruction above.
