---
name: confluence-publish
description: Confluence publication procedure via the Atlassian MCP integration — verifies the connector, confirms site/space/parent page, searches before creating, detects CREATE vs UPDATE, flags destructive changes, and requires explicit human confirmation before any write. Invoked by /publish and by product-discovery's Gate 5. Never overwrites an existing page without approval for that specific page, and never fabricates a "connected" status.
---

# Confluence Publication

Spec source: `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md` §13–14. This skill is the only place Confluence-write logic lives — `.claude/skills/product-discovery/SKILL.md` calls into it at Gate 5 rather than duplicating it.

## Input

| Parameter | Required | Description |
|---|---|---|
| `PageSet` | No | The set of pages to publish, as `{title, body}` pairs. Defaults to the ten PRD section pages below if omitted, for backward compatibility with the PRD flow. A caller publishing a different document set (e.g. `solution-architecture-suite-orchestrator-agent`'s three architecture pages) passes its own `PageSet` instead — the search-before-create, CREATE-vs-UPDATE, and Gate 5 confirmation steps below apply identically regardless of which set is passed. |
| `ParentPage` | No | Overrides `confluence.parent_page` from `config/project.yaml` for this call, if the caller's document set lives under a different parent (e.g. an "Architecture" page tree instead of the PRD tree). |

## Precondition (caller's responsibility, verify before invoking)

The caller must have already recorded an explicit human-approval decision for every page in `PageSet` before invoking this skill — this skill performs no approval logic of its own, only publication mechanics. For the PRD flow, that is `workflow/status.json` Gate 4 (`FINAL_PRD_APPROVAL`) with the literal decision `APPROVE_AND_PUBLISH`. For any other `PageSet` (e.g. the architecture suite), the calling orchestrator defines and records its own equivalent gate (see `solution-architecture-suite-orchestrator-agent`'s Human gate) and must state which gate was cleared when invoking this skill. If no such gate decision is stated, refuse and ask which approval covers this call.

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

The whole package nests under a `PRD` child page directly beneath the configured `parent_page` — find or create that `PRD` page first (same search-before-create rule applies to it), then search for each of the ten section pages below underneath it (`searchConfluenceUsingCql`, or list children via `getPagesInConfluenceSpace` / `getConfluencePageDescendants`) to determine whether a same-titled page already exists:

```
PRD
├── <Project Name> PRD — WF-<id>
│   ├── Executive Summary
│   ├── Requirements
│   ├── Feature Specification
│   ├── User Stories
│   ├── Solution Architecture
│   ├── UI/UX Specification
│   ├── Estimation & Cost
│   ├── Risk Register
│   ├── Traceability Matrix
│   └── Decision Log
└── <Project Name> Test Strategy — WF-<id>   (only if the caller says the test strategy was approved alongside the PRD)
```

The test strategy is a single sibling page (it's one document, not ten sections) — same search-before-create/CREATE-vs-UPDATE treatment as every other page here, just don't invent it if the caller didn't say Gate 4 covered it.

Page naming convention: prefix every page title with the workflow ID (e.g. `WF-2026-001 — Requirements`) unless the human specifies a different convention at Gate 5 — confirm the convention rather than assuming.

**Note on `PageSet`'s "Solution Architecture" vs. the architecture suite's "Solution Architecture" page:** if both the PRD flow and `solution-architecture-suite-orchestrator-agent` are publishing to the same space, the search in this step is what prevents creating a duplicate — a same-titled page found here is a CREATE-vs-UPDATE case like any other, not a special case to special-case around.

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
