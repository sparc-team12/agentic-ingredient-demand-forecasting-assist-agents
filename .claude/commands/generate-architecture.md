---
description: Fetch the confirmed PRD (local file or Confluence), generate the ARCH-XXX solution architecture and the Solution Architecture / Security Architecture / Technology Stack Confluence-ready docs, run every validation and human-approval gate, then publish via confluence-publish.
argument-hint: "[workflow-id]"
---

# Generate Architecture

Runs the full chain: resolve PRD → generate `ARCH-XXX` → human-approve it → generate the three architecture docs → validate → human-approve (with a hard stop on any unacknowledged `[SECURITY REVIEW REQUIRED]`) → publish to Confluence.

Workflow ID given: `$ARGUMENTS` (optional — only needed if this project is also running the discovery-pipeline's multi-workflow tracking; a standalone PRD project can omit it).

## Step 1 — Resolve the PRD

1. Check `config/project.yaml` → `confluence.prd_local_path`. If set and the file exists, read it.
2. If not set, or the file doesn't exist, glob `docs/01-prd/prd-*.md`. Exactly one match → use it. Multiple → ask which. None → go to Step 1b.
3. Confirm the resolved PRD's header shows **`Status: Confirmed`**. If it shows `Draft`, **STOP** — architecture must never be designed against an unconfirmed PRD. Report which open items are blocking confirmation and wait.

### Step 1b — Fetch from Confluence if no local PRD exists

1. Read `confluence.prd_page_url` from `config/project.yaml`. If present, resolve it via the `confluence-doc-resolver` skill (URL form).
2. If no URL is stored, resolve by name via the same skill (bare-name form), scoped to `confluence.site`.
3. On `Resolved`, reconstruct the PRD in `prd-agent`'s standard template (the fetched Confluence body already follows it, minus the provenance banner — strip that banner, keep everything from `Problem Statement` through `Change Log`) and write it to `docs/01-prd/prd-<slug>.md`. This restores the repo as source of truth per the page's own provenance statement — do not leave the PRD living only in Confluence going forward.
4. Update `config/project.yaml`'s `confluence.prd_local_path` to point at the newly written file.
5. Re-run the `Status: Confirmed` check from Step 1.3 against the reconstructed file.

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
