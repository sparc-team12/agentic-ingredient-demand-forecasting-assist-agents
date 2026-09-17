---
description: Resolve the currently-approved PRD from Confluence (by space + keyword + status, not a pinned page), sync it locally, generate the ARCH-XXX solution architecture and the Solution Architecture / Security Architecture / Technology Stack Confluence-ready docs, run every validation and human-approval gate, then publish via confluence-publish.
argument-hint: "[workflow-id]"
---

# Generate Architecture

Runs the full chain: resolve the approved PRD → generate `ARCH-XXX` → human-approve it → generate the three architecture docs → validate → human-approve (with a hard stop on any unacknowledged `[SECURITY REVIEW REQUIRED]`) → publish to Confluence.

Workflow ID given: `$ARGUMENTS` (optional — only needed if this project is also running the discovery-pipeline's multi-workflow tracking; a standalone PRD project can omit it).

## Step 1 — Resolve the approved PRD

Confluence, not the local file, is authoritative for *which* PRD is current — a re-versioned PRD publishes as a brand-new sibling page rather than an in-place edit (observed 2026-09-17: this exact product had two live PRD pages at once, an old `Status: Confirmed` v1.0 and a new `Status: Approved` v1.1, with the old one pending deletion). A pinned local file or a pinned page URL can silently go stale the moment that happens. So this step always re-resolves from Confluence rather than trusting the local file at face value.

1. Invoke `confluence-doc-resolver` with `Mode: keyword_status`:
   - `ScopeSpace` = `confluence.space` from `config/project.yaml`
   - `Keyword` = `confluence.prd_search_keyword` (default `"PRD"`)
   - `RequiredStatus` = `confluence.prd_required_status` (a list — e.g. `["Approved", "Confirmed"]` — treat any listed value as qualifying, since different PRD-authoring runs in this repo have used different terminal-status wording)
2. **`Resolved`** → continue to step 3.
3. **`NotFound`** → **STOP**. Report exactly what was searched (space, keyword, required status) and what candidates (if any) were found with their actual status, so it's clear whether the blocker is "no PRD yet" or "PRD exists but isn't approved yet."
4. **`AmbiguousMatches`** → **STOP**. Present every match (title, page ID, version, last-modified, extracted status) and ask which one is actually current — never guess by "newest," since a pending-deletion sibling page is exactly this shape of ambiguity and picking wrong means designing architecture against a superseded PRD.
5. On `Resolved`, reconstruct the PRD in `prd-agent`'s standard template (the fetched Confluence body already follows it, minus the provenance banner — strip that banner, keep everything from `Problem Statement` through `Change Log`, and record the resolved page's version number in the local file's header). Write/overwrite it at `confluence.prd_local_path`, and note in the run report if this replaced a different-version local file (so a stale-PRD run doesn't pass silently).
6. If `prd_search_keyword`/`prd_required_status` aren't set in `config/project.yaml` yet, ask for them once and offer to save them — don't default silently to a guessed keyword.

## Step 2 — Generate and approve the solution architecture (`ARCH-XXX`)

1. Check `artifacts/architecture/solution-architecture.md`. If it exists and its metadata block already shows `Human approval status: APPROVED`, skip to Step 3.
2. Otherwise, dispatch `solution-architect-agent` against the resolved PRD (Shape B — `docs/01-prd/prd-*.md`, tracing every `ARCH-XXX` to a `REQ-XXX`).
3. **Gate ARCH-1 — Solution Architecture Approval.** Present the full `ARCH-XXX` artifact to the human, calling out every item flagged as an irreversible/high-impact technology decision. Require one of: `APPROVE`, `REQUEST_CHANGES` (route back to `solution-architect-agent`, re-present), or `STOP`. A general "looks good" without addressing each flagged irreversible decision does not clear this gate — ask about each one specifically.
4. On `APPROVE`, update the artifact's metadata block to `Human approval status: APPROVED`.

## Step 3 — Generate the architecture doc suite, validate, approve, publish

Dispatch `solution-architecture-suite-orchestrator-agent`. It owns everything from here:
- Generates `solution-architecture-overview-agent`, `solution-security-architecture-agent`, `solution-tech-stack-agent` in parallel (Shape B input, since the PRD in Step 1 is `REQ-XXX`-only for this product)
- Runs the `validation-review` checklist across the full artifact set
- Presents **Gate — Architecture Suite Approval**, individually listing every `[SECURITY REVIEW REQUIRED]` marker and `[TBD]` item — a blanket approval does not clear an unacknowledged security marker
- On approval, invokes `confluence-publish` with `PageSet` = the three approved documents

Do not skip straight to `confluence-publish` yourself — the suite orchestrator's gate is the only thing authorized to hand it an approved `PageSet`.

## Before Step 3 can actually publish

`config/project.yaml` has `confluence.space` and `confluence.parent_page` blank, and `create_if_missing: false` / `allow_updates: false`. Per `confluence-publish`'s own hard rules, it will stop and ask rather than override these. Resolve this with the human **before** Step 3's publish sub-step — confirm: which space (the PRD currently lives in the personal space `~712020c78d0510dbf248218881c00989970857`, "sparc.team12" — is that the intended target for architecture docs too, or a different/shared space?), which parent page, and explicit permission to flip `create_if_missing`/`allow_updates` for this run. Generation and validation (Steps 1–2, and the generation/validation part of Step 3) can proceed without this; only the final publish call needs it.

## Report

On completion, summarize: which PRD was used (local or freshly fetched), the `ARCH-XXX` count and approval status, the three doc statuses (draft/approved/published), any outstanding `[SECURITY REVIEW REQUIRED]`/`[TBD]` items, and — if published — each page's Confluence URL.
