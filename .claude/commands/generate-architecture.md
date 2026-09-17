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

## 2. Generate and approve engineering solution architecture

If `artifacts/architecture/solution-architecture.md` is not already human-approved, dispatch `solution-architect-agent`, present all high-impact/irreversible choices, and require `APPROVE`, `REQUEST_CHANGES`, or `STOP`. Only explicit approval updates `Human approval status: APPROVED`.

## 3. Generate HLD and LLD suite

Dispatch `.claude/agents/solution-architecture-suite-orchestrator-agent.md` with the resolved inputs and `--repo` target when supplied. It owns this dependency chain:

```text
Architecture Overview + Security Architecture + Technology Stack (parallel)
  -> High-Level Design
  -> Low-Level Design
  -> Independent Architecture Validation
  -> Human approval of all five documents
  -> DEVELOPMENT_READY
```

Do not dispatch HLD and LLD in parallel, skip validation, or treat earlier solution-architecture approval as approval of these implementation designs.

## 4. Optional publication

After the suite's human gate passes, offer Confluence publication of the five-page set. Publication requires the configured site/space/parent and the `confluence-publish` skill's per-page CREATE/UPDATE confirmation. Lack of Confluence access does not invalidate locally approved architecture or development readiness.

## Report

Report the PRD source; solution architecture, overview, security, stack, HLD, LLD, and validation paths/statuses; outstanding security/TBD items; human gate decision; target repository; development eligibility; and publication URLs if published.
