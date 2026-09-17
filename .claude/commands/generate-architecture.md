---
description: Resolve the currently-approved PRD from Confluence (by space + keyword + status, not a pinned page), sync it locally, generate the ARCH-XXX solution architecture and the Solution Architecture / Security Architecture / Technology Stack / Infrastructure Architecture Confluence-ready docs (only the ones not already generated and approved), run every validation and human-approval gate, then publish via confluence-publish.
argument-hint: "[workflow-id]"
---

# Generate Architecture

Runs the full chain: resolve the approved PRD → generate `ARCH-XXX` → human-approve it → generate whichever of the four architecture docs (Solution Architecture Overview, Security Architecture, Technology Stack, Infrastructure Architecture) don't already exist as an approved artifact → validate → human-approve (with a hard stop on any unacknowledged `[SECURITY REVIEW REQUIRED]`) → publish to Confluence.

The Infrastructure Architecture document is required ground truth for `/terraform-code` and `/terraform-pipeline` — those commands stop without it.

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

## Step 1.5 — PRD-change detection gate (hard rule — never assume)

This closes a real gap: Steps 2 and 3 below would otherwise decide whether to (re)generate purely from an artifact's own `Human approval status: APPROVED` flag, which says nothing about whether the PRD it was built against is still the current one. A new PRD version landing in `Approved`/`Confirmed` status (the exact scenario Step 1 already guards for during PRD resolution) must never be silently absorbed as "nothing to do" (blind skip) or silently trigger "regenerate everything" (blind regen) — both are assumptions this gate exists to block. Do not skip this step, and do not infer the answer yourself — it is a human decision.

1. If `artifacts/architecture/solution-architecture.md` does not exist yet, there's nothing to compare against — continue to Step 2 as a first-time generation.
2. If it exists, read the PRD version it was built against from its metadata block's `PRD source` line (see `solution-architect-agent`'s output contract). Compare it to the PRD version/title just resolved in Step 1.
   - If the existing artifact predates this check and has no recorded `PRD source` line, don't assume the versions match — treat it the same as a detected mismatch (step 4) rather than silently trusting a stale artifact.
3. **Same PRD version** → no PRD change detected. Continue to Step 2/3's normal skip-if-approved behavior.
4. **Different PRD version** (a new PRD version found in `Approved`/`Confirmed` status that the existing architecture wasn't built against) → **STOP.** Present to the human:
   - The PRD version/title the current `solution-architecture.md` (and, transitively, the four suite docs, which trace to it rather than to the PRD directly) was built against
   - The new PRD version/title just resolved in Step 1
   - What changed between them if derivable — a coarse list of added/changed/removed `REQ-XXX` ids is enough, this isn't a full review

   Then ask explicitly, before Step 2 or Step 3 touches anything — one of:
   - **`EDIT`** — the new PRD is an incremental change; revise the existing `solution-architecture.md` (and, in Step 3, whichever of the four suite docs are actually affected) to reflect only what changed. When dispatching, instruct the specialist to read its existing draft first and update the affected content rather than regenerate from a blank page — but the resulting document must still read as a clean, current-state artifact: no inline "previously this was X, now it's Y" narration, before/after callouts, or version-history commentary in the document body. It should look indistinguishable from a fresh draft written directly against the current PRD; anything about what changed belongs only in the completion summary and `workflow/decisions.md`.
   - **`REGENERATE`** — treat the existing architecture as superseded; dispatch `solution-architect-agent` (and, in Step 3, all four suite specialists) fresh against the new PRD, ignoring their current `APPROVED` status.
   - **`STOP`** — hold; do not touch Step 2 or Step 3 this run.

   Record the decision and its rationale in `workflow/decisions.md` — a general "looks fine, go ahead" without picking `EDIT` or `REGENERATE` does not clear this gate.
5. Whichever of `EDIT`/`REGENERATE` was chosen governs both Step 2 and Step 3 for the rest of this run. Step 3's suite orchestrator must not independently re-run its own missing-or-unapproved gap-check as a substitute for this decision (see the hard rule in `solution-architecture-suite-orchestrator-agent`).

## Step 2 — Generate and approve the solution architecture (`ARCH-XXX`)

1. Check `artifacts/architecture/solution-architecture.md`. If it exists, its metadata block already shows `Human approval status: APPROVED`, **and Step 1.5 found no PRD version change**, skip to Step 3.
2. Otherwise (missing, not yet approved, or Step 1.5 resolved to `EDIT`/`REGENERATE`), dispatch `solution-architect-agent` against the resolved PRD (Shape B — `docs/01-prd/prd-*.md`, tracing every `ARCH-XXX` to a `REQ-XXX`) — in `EDIT` mode, per Step 1.5's instruction to patch rather than rewrite; in `REGENERATE` mode or first-time generation, a full fresh draft.
3. **Gate ARCH-1 — Solution Architecture Approval.** Present the full `ARCH-XXX` artifact to the human, calling out every item flagged as an irreversible/high-impact technology decision, and — individually, one at a time if that's what it takes — every open question from `solution-architect-agent`'s completion summary. Require one of: `APPROVE`, `REQUEST_CHANGES` (route back to `solution-architect-agent`, re-present), or `STOP`.
   **Hard rule — mandatory human intervention, no silent `[TBD]`:** `APPROVE` does not clear this gate while the artifact still contains an unaddressed gap (an open question the agent couldn't answer from the PRD/input artifacts, whether or not it's literally tagged `[TBD]`) or an unaddressed irreversible-decision flag. Ask about each one specifically — do not accept a blanket "looks good" as covering them. Every such gap must get one of two outcomes before `APPROVE` is valid:
   - The human supplies the missing information → update the artifact to replace the gap with the real answer (never leave the placeholder in place once it's been answered).
   - The human explicitly defers it, with a stated reason → the placeholder may remain, but record the deferral and reason in `workflow/decisions.md`; it is a logged decision, not a silent gap.
   Do not regenerate the whole artifact from scratch to "resolve" these — asking and recording the answer is the fix, not a rewrite.
4. On `APPROVE`, update the artifact's metadata block to `Human approval status: APPROVED`, and record the current PRD version in its `PRD source` line so future runs of Step 1.5 can compare against it.

## Step 3 — Generate the architecture doc suite, validate, approve, publish

Dispatch `solution-architecture-suite-orchestrator-agent`, telling it Step 1.5's outcome (no change / `EDIT` / `REGENERATE`) explicitly rather than letting it re-derive PRD staleness on its own. It owns everything from here:
- If Step 1.5 found no PRD change: checks all four target artifacts (`solution-architecture-overview.md`, `security-architecture.md`, `tech-stack.md`, `infrastructure-architecture.md`) and dispatches `solution-architecture-overview-agent`, `solution-security-architecture-agent`, `solution-tech-stack-agent`, `infra-architecture-agent` **only for whichever are missing or not yet `APPROVED`**, in parallel (Shape B input, since the PRD in Step 1 is `REQ-XXX`-only for this product)
- If Step 1.5 resolved to `REGENERATE`: dispatches all four specialists fresh, regardless of their current `APPROVED` status
- If Step 1.5 resolved to `EDIT`: dispatches only the specialists whose document is actually affected by what changed in the new PRD, instructing each to patch its existing draft rather than rewrite it from scratch
- Runs the `validation-review` checklist across the full four-document artifact set, including any already-approved documents it skipped regenerating
- Presents **Gate — Architecture Suite Approval**, individually listing every `[SECURITY REVIEW REQUIRED]` marker and `[TBD]` item — a blanket approval does not clear an unacknowledged security marker
- On approval, invokes `confluence-publish` with `PageSet` = all four approved documents

Do not skip straight to `confluence-publish` yourself — the suite orchestrator's gate is the only thing authorized to hand it an approved `PageSet`.

## Before Step 3 can actually publish

`config/project.yaml` has `confluence.space` and `confluence.parent_page` blank, and `create_if_missing: false` / `allow_updates: false`. Per `confluence-publish`'s own hard rules, it will stop and ask rather than override these. Resolve this with the human **before** Step 3's publish sub-step — confirm: which space (the PRD currently lives in the personal space `~712020c78d0510dbf248218881c00989970857`, "sparc.team12" — is that the intended target for architecture docs too, or a different/shared space?), which parent page, and explicit permission to flip `create_if_missing`/`allow_updates` for this run. Generation and validation (Steps 1–2, and the generation/validation part of Step 3) can proceed without this; only the final publish call needs it.

## Report

On completion, summarize: which PRD was used (local or freshly fetched), the `ARCH-XXX` count and approval status, all four doc statuses (skipped-already-approved / freshly generated / draft / approved / published), any outstanding `[SECURITY REVIEW REQUIRED]`/`[TBD]` items, and — if published — each page's Confluence URL.
