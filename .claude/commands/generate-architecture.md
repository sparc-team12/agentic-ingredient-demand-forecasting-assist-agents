---
description: Resolve the currently-approved PRD from Confluence (by space + keyword + status, not a pinned page), generate ARCH-XXX plus the Solution Architecture / Security Architecture / Technology Stack / HLD / LLD suite, run independent validation and every human-approval gate, then publish via confluence-publish.
argument-hint: "[workflow-id]"
---

# Generate Architecture

Delegate to the `product-discovery` skill (`.claude/skills/product-discovery/SKILL.md`) with `mode: GENERATE_ARCHITECTURE` and `$ARGUMENTS` as the optional workflow ID. The skill's §7b ("Architecture Suite / HLD / LLD workflow") owns the full procedure — PRD resolution, `ARCH-XXX` generation/approval, the five-document suite (overview/security/stack/HLD/LLD), independent validation, the Architecture/HLD/LLD Approval gate (hard block on unacknowledged `[SECURITY REVIEW REQUIRED]` or a failing validation), development handoff, and publish via `confluence-publish`. `orchestrator-agent` dispatches and gates every step — this command does not implement any of that procedure itself, and there is no separate architecture-suite orchestrator.
