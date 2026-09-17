---
description: Resume publishing the architecture doc suite (Solution Architecture, Security Architecture, Technology Stack) to Confluence when the documents already exist locally but a prior publish attempt didn't finish — e.g. it hit a token/rate limit mid-run. Checks real status first, closes any outstanding human-approval gate, then publishes via confluence-publish.
argument-hint: "[workflow-id]"
---

# Resume Architecture Suite Publish

Workflow ID given: `$ARGUMENTS` (optional — only relevant if this project tracks the suite under a workflow ID; most standalone runs use `UNASSIGNED`, per each document's metadata block).

Dispatch `solution-architecture-publish-resume-agent` (`.claude/agents/solution-architecture-publish-resume-agent.md`). Do **not** re-run `/generate-architecture` or `solution-architecture-suite-orchestrator-agent` for this — that would re-dispatch the specialist agents against documents that already exist. This command is specifically for the case where `artifacts/architecture/solution-architecture-overview.md`, `security-architecture.md`, and `tech-stack.md` already exist on disk and only the approval/publish tail end needs finishing.

The agent will:
1. Reconcile each document's local `Human approval status` against what's actually already in Confluence (a prior interrupted run may have created some pages without the local metadata reflecting it, or the reverse).
2. Present a status table and, for any document still `PENDING` or blocked on an open `[SECURITY REVIEW REQUIRED]` marker, run the human-approval gate — a narrative "resolved by human decision" note inside a document does not by itself count as a recorded approval.
3. For everything that clears the gate (or was already `APPROVED`) and is confirmed missing from Confluence, invoke the `confluence-publish` skill to actually publish it — never bypassing that skill's own search-before-create or Gate 5 confirmation.

Report back the final status table, every gate decision recorded (with its `DEC-XXX` ID in `workflow/decisions.md`), and the Confluence URL for anything actually published this run.
