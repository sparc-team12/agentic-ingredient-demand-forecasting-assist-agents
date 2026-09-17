---
description: Publish the approved final PRD to Confluence via the Atlassian MCP integration (Gate 5)
argument-hint: "<workflow-id>"
---

Load and follow `.claude/skills/product-discovery/SKILL.md` §8, which delegates the actual publish mechanics to `.claude/skills/confluence-publish/SKILL.md`.

Workflow ID given: `$ARGUMENTS`

Require Gate 4 to have recorded the literal `APPROVE_AND_PUBLISH` decision — if not, refuse and explain. Otherwise invoke `confluence-publish`, which will: confirm/collect Confluence site, space, and parent page from `config/project.yaml`; resolve the Atlassian cloud ID; search for existing pages before deciding CREATE vs UPDATE per title; present the exact page list with CREATE/UPDATE and any destructive change at **Gate 5 — Confluence Publication**; and wait for explicit confirmation before calling any write tool. Never overwrite an existing page without explicit approval for that specific page. After it returns, record the resulting page IDs/URLs in `workflow/status.json` and append its publish events to `workflow/events.jsonl`.
