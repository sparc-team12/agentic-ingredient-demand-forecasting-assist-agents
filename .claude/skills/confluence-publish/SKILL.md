---
name: confluence-publish
description: Confluence publication procedure via the Atlassian MCP integration — verifies the connector, confirms site/space/parent page, searches before creating, detects CREATE vs UPDATE, flags destructive changes, and requires explicit human confirmation before any write. Invoked by /publish and by product-discovery's Gate 5. Never overwrites an existing page without approval for that specific page, and never fabricates a "connected" status.
---

# Confluence Publication

Spec source: `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md` §13–14. This skill is the only place Confluence-write logic lives — `.claude/skills/product-discovery/SKILL.md` calls into it at Gate 5 rather than duplicating it.

## Precondition (caller's responsibility, verify before invoking)

`workflow/status.json` for the target workflow must show Gate 4 (`FINAL_PRD_APPROVAL`) with the literal decision `APPROVE_AND_PUBLISH`. If this skill is invoked without that, refuse and say why.

## Step 1 — Verify the MCP connector (don't assume)

Do not assume a specific MCP server or tool name. In this repository's environment, Confluence/Jira access is confirmed available through the **claude.ai Atlassian Rovo** connector (`mcp__claude_ai_Atlassian_Rovo__*` tools) — verified 2026-09-17 via `atlassianUserInfo` and `getAccessibleAtlassianResources`. If those tools error, are missing, or this is a different environment:
- Check for any other configured Atlassian MCP server instead of guessing.
- If none exists, tell the human and give the CLI setup path:
  ```bash
  claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
  ```
  then have them run `/mcp` and complete authentication.
- Do not claim the connection works until a real read call (e.g. `atlassianUserInfo`) has succeeded in this session.

## Step 2 — Resolve target site/space/parent page

Read `confluence.site`, `confluence.space`, `confluence.parent_page` from `config/project.yaml`. If `space` or `parent_page` is blank, ask the human before proceeding — do not guess a space key or page title. Resolve the Atlassian `cloudId` via `getAccessibleAtlassianResources`, matching by the site hostname; re-resolve each session rather than trusting a cached ID indefinitely.

## Step 3 — Search before creating

For each of the ten PRD section pages below, search under the target space/parent page first (`searchConfluenceUsingCql`, or list children of the parent via `getPagesInConfluenceSpace` / `getConfluencePageDescendants`) to determine whether a same-titled page already exists:

```
<Project Name> PRD — WF-<id>
├── Executive Summary
├── Requirements
├── Feature Specification
├── User Stories
├── Solution Architecture
├── UI/UX Specification
├── Estimation & Cost
├── Risk Register
├── Traceability Matrix
└── Decision Log
```

Page naming convention: prefix every page title with the workflow ID (e.g. `WF-2026-001 — Requirements`) unless the human specifies a different convention at Gate 5 — confirm the convention rather than assuming.

## Step 4 — Present at Gate 5 and wait

Show the human, before calling any write tool:
- Target site, space, parent page.
- The exact list of pages with CREATE or UPDATE determined by Step 3.
- For every UPDATE, that it is a potentially destructive change (existing content will be replaced) — call this out explicitly, don't bury it.
- Wait for explicit confirmation. Anything other than clear confirmation stops publication; a general "yes" that doesn't distinguish per-page is only sufficient if the human was shown the full page list with CREATE/UPDATE and confirmed against exactly that list.

## Step 5 — Publish only what was confirmed

- CREATE missing pages with `createConfluencePage` under the confirmed parent.
- UPDATE only the specific pages the human approved for overwrite, using `updateConfluencePage` — never a page that wasn't explicitly called out and approved.
- If `config/project.yaml` has `confluence.enabled: false`, or the action needs `create_if_missing`/`allow_updates` and that flag is `false`, stop and say so rather than overriding config.
- Every published page's body must include the standard metadata block (Workflow ID, Agent, Created, Status, Source artifacts, Human approval status) plus a link back to the source artifact file(s) it was generated from.

## Step 6 — Record the result

- Append each page's Confluence page ID/URL to `confluence.pages` in `status.json` for this workflow (the caller — `product-discovery` skill — owns the actual file write; this skill returns the data needed).
- Report a `PUBLISHED` event per page for `workflow/events.jsonl`, including timestamp, workflow ID, page title, page ID/URL, CREATE or UPDATE.
- Give the human a final summary listing every page created/updated with its URL.

## Hard rules

1. Search before creating or updating — always.
2. Never overwrite an existing page without explicit approval for that specific page.
3. Show intended changes before publication — never publish silently.
4. Preserve the workflow ID on every published page.
5. Add source/traceability metadata to every page.
6. Record page IDs/URLs in `workflow/status.json`.
7. Record publication events in `workflow/events.jsonl`.
8. Treat Confluence publication as entirely human-controlled — this skill only executes what was just shown and confirmed, nothing broader.
9. Never claim a page was published if the write call didn't actually succeed — surface API errors verbatim, don't paper over them.
