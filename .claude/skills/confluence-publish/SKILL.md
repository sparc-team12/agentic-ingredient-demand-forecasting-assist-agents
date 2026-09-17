---
name: confluence-publish
description: Confluence publication procedure via the Atlassian MCP integration — verifies the connector, confirms site/space/parent page, searches before creating, detects CREATE vs UPDATE, flags destructive changes, and requires explicit human confirmation before any write. Invoked by /publish and by product-discovery at every publish point in the pipeline (Gates 1, 2, 4, 5, and 7). Never overwrites an existing page without approval for that specific page, and never fabricates a "connected" status.
---

# Confluence Publication

This skill is the only place Confluence-write logic lives in this repository — `.claude/skills/product-discovery/SKILL.md` calls into it after Gate 1 (the PRD), after Gate 2 (feature/architecture/UI-UX, one call per document), after Gate 4 (estimation/risk, one call per document), after Gate 5 (test strategy), at Gate 7 (the final assembled package), and at the Architecture/HLD/LLD Approval gate (the five-document suite) — never duplicating this logic elsewhere. `orchestrator-agent` (`.claude/agents/orchestrator-agent.md`) is the sole agent in this repository with Confluence/Jira access, for every workflow it owns. (User stories publish to **Jira**, not here — see `orchestrator-agent.md`'s "Publishing user stories to Jira".)

## Input

| Parameter | Required | Description |
|---|---|---|
| `PageSet` | Yes | The set of pages to publish this call, as `{title, body}` pairs, already titled per the `<Document Type> - <Project Name>` naming convention (`orchestrator-agent.md`). Usually one or a handful of pages per call (a single PRD page after Gate 1, one document after Gate 2/4/5, the five Architecture Suite/HLD/LLD documents, or the final `final-prd.md` content at Gate 7) — never a fixed default set, since which documents exist depends entirely on which gates this workflow has cleared so far. |
| `ParentPage` | Yes | The Confluence page ID of **this workflow's resolved project folder** (`orchestrator-agent.md`'s "Project identification and publish destinations", `product-discovery/SKILL.md` §1a — resolved the same way whether the caller is the discovery pipeline or the Architecture Suite/HLD/LLD workflow) — never `confluence.parent_page` directly. If the caller hasn't resolved a project folder yet, refuse and say so; do not fall back to publishing under the space root. |

## Precondition (caller's responsibility, verify before invoking)

The caller must have already recorded an explicit human-approval decision for every page in `PageSet` before invoking this skill — this skill performs no approval logic of its own, only publication mechanics. For the final-package call, that is `workflow/status.json` Gate 6 (`FINAL_PRD_APPROVAL`) with the literal decision `APPROVE_AND_PUBLISH`. For every other call (the PRD after Gate 1, a document after Gate 2/4/5, or the Architecture Suite), `orchestrator-agent` states which gate was cleared when invoking this skill — a content-review gate clearing is what authorizes *attempting* the publish; this skill's own Step 4 confirmation is what actually authorizes the write. If no gate decision is stated, refuse and ask which approval covers this call.

## Step 1 — Verify the MCP connector (don't assume)

Do not assume a specific MCP server or tool name. In this repository's environment, Confluence/Jira access is confirmed available through the **claude.ai Atlassian Rovo** connector (`mcp__claude_ai_Atlassian_Rovo__*` tools) — verified 2026-09-17 via `atlassianUserInfo` and `getAccessibleAtlassianResources`. If those tools error, are missing, or this is a different environment:
- Check for any other configured Atlassian MCP server instead of guessing.
- If none exists, tell the human and give the CLI setup path:
  ```bash
  claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp
  ```
  then have them run `/mcp` and complete authentication.
- Do not claim the connection works until a real read call (e.g. `atlassianUserInfo`) has succeeded in this session.

## Step 2 — Resolve target site/space

Read `confluence.site` and `confluence.space` from `config/project.yaml`. If `space` is blank, ask the human before proceeding — do not guess a space key. Resolve the Atlassian `cloudId` via `getAccessibleAtlassianResources`, matching by the site hostname; re-resolve each session rather than trusting a cached ID indefinitely. The project folder itself (`ParentPage`) is resolved by the caller before invoking this skill (Gate 0b) — this skill does not create or search for project folders, only the pages inside one.

## Step 3 — Search before creating

Search directly under `ParentPage` (the project folder) for each page in `PageSet` (`searchConfluenceUsingCql`, or list children via `getPagesInConfluenceSpace` / `getConfluencePageDescendants`) to determine whether a same-titled page already exists. In the full pipeline, most documents are created incrementally, one call at a time, well before the final-package call — that's expected: this search step is exactly what turns a repeat publish of an already-existing page (e.g. updating `PRD - <Project Name>` at Gate 7 after it was already created at Gate 1) into an UPDATE instead of a duplicate CREATE.

A project's folder, once created, looks like this once every document type has been published at least once:

```
<Project Name>                              (the project folder — created once, reused by every workflow for this project)
├── PRD - <Project Name>                    (created at Gate 1; updated in place at Gate 7 with Executive Summary/Traceability Matrix/Decision Log)
├── Feature Specification - <Project Name>  (Gate 2)
├── Solution Architecture - <Project Name>  (Gate 2)
├── Design Document - <Project Name>        (Gate 2 — the UI/UX spec)
├── Estimate and Cost - <Project Name>      (Gate 4)
├── Risk Register - <Project Name>          (Gate 4)
├── Test Strategy - <Project Name>          (Gate 5)
├── Solution Architecture Overview - <Project Name>  (Architecture Suite workflow, if generated)
├── Security Architecture - <Project Name>           (Architecture Suite workflow, if generated)
├── Technology Stack - <Project Name>                (Architecture Suite workflow, if generated)
├── High-Level Design - <Project Name>               (Architecture Suite workflow, if generated)
└── Low-Level Design - <Project Name>                (Architecture Suite workflow, if generated)
```

User stories are **not** a page here — they publish to Jira (see `orchestrator-agent.md`'s "Publishing user stories to Jira"); the PRD page's Traceability Matrix links to them by Jira key/URL instead of duplicating their content here.

Titles are fixed by the naming convention (`<Document Type> - <Project Name>`, exact labels in `orchestrator-agent.md`) — there is no workflow-ID prefix and no per-call naming decision to make; the same document type always resolves to the same title for a given project, which is what makes the search-before-create check meaningful across multiple workflows for the same project.

**Note on "Solution Architecture" vs. "Solution Architecture Overview":** these are deliberately different labels for different documents (the discovery pipeline's engineering `ARCH-XXX` spec vs. the Architecture Suite's executive-facing overview) — don't conflate them into one title, and don't let a search for one match the other.

## Step 4 — Present the exact page list and wait

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
