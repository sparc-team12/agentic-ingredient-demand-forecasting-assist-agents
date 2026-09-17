---
description: Fetch the confirmed PRD (local file or Confluence), generate the ARCH-XXX solution architecture and the Solution Architecture / Security Architecture / Technology Stack Confluence-ready docs, run every validation and human-approval gate, then publish via confluence-publish.
argument-hint: "[workflow-id]"
---

# Generate Architecture

Delegate to the `product-discovery` skill (`.claude/skills/product-discovery/SKILL.md`) with `mode: GENERATE_ARCHITECTURE` and `$ARGUMENTS` as the optional workflow ID. The skill's §7b ("Architecture Suite workflow") owns the full procedure — PRD resolution, `ARCH-XXX` generation/approval, the three-document suite, validation, the Architecture Suite Approval gate (hard block on unacknowledged `[SECURITY REVIEW REQUIRED]`), and publish via `confluence-publish`. `orchestrator-agent` dispatches and gates every step; this command does not implement any of that procedure itself.
