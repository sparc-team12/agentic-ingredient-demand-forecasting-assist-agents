---
name: code-review-independent-agent
description: Legacy compatibility alias for the former numbered-artifact reviewer. Do not select for new development work; use code-review-agent.
tools: Read
---

# Legacy Independent Code Reviewer Alias

The canonical independent review is now `.claude/agents/code-review-agent.md`, which writes `artifacts/development/<work-item-id>/code-review.json` and participates in the orchestrated rework loop.

This file remains only for old callers. If invoked, do not review or write the legacy root-level `07-code-verification.json`; return `BLOCKED` and direct the caller to `dev-orchestrator-agent`.
