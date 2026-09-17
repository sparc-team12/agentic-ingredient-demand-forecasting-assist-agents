---
name: confluence-doc-resolver
description: Resolve a document (Architecture Document, Deployment Architecture, Security Architecture, HLD/LLD, PRD) from either a Confluence page URL or a bare document/project name, via the Atlassian MCP connector, falling back to a local PDF/YAML/JSON file only when Atlassian is unreachable or the caller explicitly provides one. Extracted from the duplicated resolution logic in dev-scaffold-agent, infra-terraform-coding-agent, infra-pipeline-agent, and docs-knowledge-agent — call this instead of reimplementing it per agent.
---

# Confluence Document Resolver

A single, shared implementation of "given a document reference, fetch its content" — used by every agent that consumes an Architecture Document, PRD, HLD/LLD, or similarly Confluence-hosted spec. Centralizing this avoids the URL-parsing and search-fallback logic drifting out of sync across agents.

## Used by

`dev-scaffold-agent`, `infra-terraform-coding-agent`, `infra-pipeline-agent`, `docs-knowledge-agent`, and any future agent that needs to resolve a Confluence-hosted document by URL or name.

## Input

| Parameter | Required | Description |
|---|---|---|
| `Source` | Yes | `atlassian` (primary) or `pdf`/`yaml_json` (local file fallback) |
| `Value` | Yes | A Confluence page URL, a bare document/project name/title, or (only for the local fallback) a file path |
| `ScopePath` | No | An optional Confluence space/page-tree path to scope name search to (e.g. `AI SDLC - Architecture >> Architecture`) — if the caller has a fixed convention, pass it so search doesn't wander into unrelated spaces |

## Steps

### `atlassian` source

**A. `Value` looks like a URL** (starts with `http://` or `https://`)

1. Extract the `cloudId` — the site hostname (e.g. `https://myorg.atlassian.net/...` → `cloudId = "myorg.atlassian.net"`).
2. Extract the `pageId` — support all three Confluence URL formats:
   - `/pages/123456789` → numeric ID
   - `?pageId=123456789` → numeric ID
   - `/wiki/x/AbCdEf` → tiny-link ID (the encoded segment after `/x/`)
3. Fetch with `mcp__claude_ai_Atlassian_Rovo__getConfluencePage(cloudId, pageId, contentFormat="markdown")`.
4. On an auth or not-found error, call `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources()` to get the correct `cloudId` (UUID) and retry once.

**B. `Value` is a bare name/title, not a URL**

1. Search with `mcp__claude_ai_Atlassian_Rovo__search` or `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql`, scoped to `ScopePath` if one was given.
2. Exactly one clear match → fetch it with `getConfluencePage` using the matched `cloudId`/`pageId`.
3. Multiple plausible matches → list titles/spaces to the caller and ask which one — never guess.
4. No matches → return `Status: NotFound` with the message `No Confluence page found matching "<Value>"<ScopePath suffix if given>. Provide the exact document title or a page URL.`

### `pdf` / `yaml_json` source (fallback only)

Use only when `atlassian` is not available (MCP connector not configured, unreachable, or the caller explicitly chose a local file). `Read` the file directly — never silently prefer a local file over a reachable Atlassian source.

## Output

| Field | Description |
|---|---|
| `Status` | `Resolved` \| `NotFound` \| `AmbiguousMatches` \| `Failed` |
| `Title` | The resolved document's title |
| `Body` | The resolved document's content |
| `CloudId` / `PageId` | Present on `Resolved` via the `atlassian` source, for reuse in later calls (e.g. `updateConfluencePage`) |
| `Matches` | Present on `AmbiguousMatches` — list of `{title, space, url}` for the caller to choose from |
| `Error` | Populated only on `Failed` |

## Error Handling

- Never fabricate document content — a `NotFound`/`Failed` result must be surfaced to the calling agent's own hard-stop behavior (most treat a missing required document as a blocker), not papered over with an assumption.
- An `AmbiguousMatches` result is not a failure — relay the list to the human/developer and wait for a choice rather than picking the "most likely" one.
