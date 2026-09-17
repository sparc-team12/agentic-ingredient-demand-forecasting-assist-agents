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
| `Mode` | No | `url` (default if `Value` looks like a URL), `name` (default otherwise), or `keyword_status` — resolve by searching a space for a keyword and filtering to a required status field, without needing a specific page pinned anywhere. Use `keyword_status` whenever the caller only has a space, not a specific page (e.g. a PRD that gets re-versioned as new sibling pages over time — see Hard-earned lesson below). |
| `Value` | Conditional | A Confluence page URL or a bare document/project name/title — required for `url`/`name` modes, unused for `keyword_status`. For the local fallback, a file path. |
| `ScopePath` | No | An optional Confluence space/page-tree path to scope `name`-mode search to (e.g. `AI SDLC - Architecture >> Architecture`) |
| `ScopeSpace` | Conditional | The Confluence space key — required for `keyword_status` mode |
| `Keyword` | Conditional | Title/text keyword to search for within `ScopeSpace` — required for `keyword_status` mode (e.g. `"PRD"`) |
| `RequiredStatus` | Conditional | The value a page's own `Status:` line must equal (case-insensitive) to qualify — required for `keyword_status` mode. Accept synonyms the caller names as equivalent (e.g. a caller may treat `Confirmed` and `Approved` as the same terminal state across different document-author conventions) rather than a single hardcoded string. |

## Steps

### `atlassian` source, Mode `url`

1. Extract the `cloudId` — the site hostname (e.g. `https://myorg.atlassian.net/...` → `cloudId = "myorg.atlassian.net"`).
2. Extract the `pageId` — support all three Confluence URL formats:
   - `/pages/123456789` → numeric ID
   - `?pageId=123456789` → numeric ID
   - `/wiki/x/AbCdEf` → tiny-link ID (the encoded segment after `/x/`)
3. Fetch with `mcp__claude_ai_Atlassian_Rovo__getConfluencePage(cloudId, pageId, contentFormat="markdown")`.
4. On an auth or not-found error, call `mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources()` to get the correct `cloudId` (UUID) and retry once.

### `atlassian` source, Mode `name`

1. Search with `mcp__claude_ai_Atlassian_Rovo__search` or `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql`, scoped to `ScopePath` if one was given.
2. Exactly one clear match → fetch it with `getConfluencePage` using the matched `cloudId`/`pageId`.
3. Multiple plausible matches → list titles/spaces to the caller and ask which one — never guess.
4. No matches → return `Status: NotFound` with the message `No Confluence page found matching "<Value>"<ScopePath suffix if given>. Provide the exact document title or a page URL.`

### `atlassian` source, Mode `keyword_status`

Use this when the caller wants "whatever page in this space is currently the approved one," pinning only a space, not a page — a document that gets re-versioned as a brand-new sibling page (rather than an in-place edit) will otherwise silently go stale behind a pinned URL.

1. Resolve `cloudId` the same way as Mode `url` step 1, from `ScopeSpace`'s site.
2. Search with `mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql`: `space = "<ScopeSpace>" AND type = page AND (title ~ "<Keyword>" OR text ~ "<Keyword>")`.
3. Fetch every result's full content (`getConfluencePage`, `contentFormat="markdown"`) — the search snippet alone isn't reliable enough to read the status field from.
4. From each page's body, extract its status line — match `**Status:**`, `Status:`, or an equivalent labelled field, case-insensitively — and compare against `RequiredStatus` (and any caller-named synonyms).
5. Filter to pages whose extracted status matches. Then:
   - **Exactly one match** → `Resolved`.
   - **Zero matches** → `Status: NotFound`, message: `No page with Status: <RequiredStatus> found matching "<Keyword>" in space <ScopeSpace>.` List whatever candidates were found and their actual statuses, so the caller can see what's blocking (e.g. still `Draft`).
   - **More than one match** → `Status: AmbiguousMatches`. This is a real, observed failure mode — a re-versioned document can leave two live pages both carrying the same "approved" status (a new version published as a sibling page, old one pending deletion) — list every match with title, page ID, version, and last-modified, and ask which one, never pick "the newest" automatically.

### `pdf` / `yaml_json` source (fallback only)

Use only when `atlassian` is not available (MCP connector not configured, unreachable, or the caller explicitly chose a local file). `Read` the file directly — never silently prefer a local file over a reachable Atlassian source.

## Output

| Field | Description |
|---|---|
| `Status` | `Resolved` \| `NotFound` \| `AmbiguousMatches` \| `Failed` |
| `Title` | The resolved document's title |
| `Body` | The resolved document's content |
| `CloudId` / `PageId` | Present on `Resolved` via the `atlassian` source, for reuse in later calls (e.g. `updateConfluencePage`) |
| `Matches` | Present on `AmbiguousMatches` — list of `{title, space, url, pageId, version, lastModified, extractedStatus}` for the caller to choose from (Mode `keyword_status` includes `extractedStatus`/`version` so the human can tell which one is actually current) |
| `ExtractedStatus` | Mode `keyword_status` only, present on `Resolved` — the literal status value found on the page, for the caller to log/display |
| `Error` | Populated only on `Failed` |

## Error Handling

- Never fabricate document content — a `NotFound`/`Failed` result must be surfaced to the calling agent's own hard-stop behavior (most treat a missing required document as a blocker), not papered over with an assumption.
- An `AmbiguousMatches` result is not a failure — relay the list to the human/developer and wait for a choice rather than picking the "most likely" one, and this applies with extra force to Mode `keyword_status`: two pages both showing the required status is exactly the scenario this mode exists to catch, not a false positive to work around.
