# Decision Log

Records every material human decision made during a product discovery workflow — one `## DEC-XXX` entry per decision, IDs sequential across all workflows. Written by the orchestrator only after a human has actually made the decision at a gate; never fabricated, never attributed to an unnamed person.

Entry format:

```markdown
## DEC-XXX — <short title>

Decision:
<what was decided>

Decided by:
<human stakeholder name/role as given, or "human (unspecified)" if not stated>

Reason:
<why>

Alternatives considered:
<if any>

Impact:
<what downstream artifacts/agents are affected>

Related:
<artifact IDs, e.g. ARCH-003, FEAT-007, RISK-004>
```

## DEC-001 — Solution Architecture (overview) approved at Architecture Suite Approval gate

Decision:
`artifacts/architecture/solution-architecture-overview.md` is APPROVED as submitted. This document carries no open `[SECURITY REVIEW REQUIRED]` markers. Its open `[TBD]` items — backend API framework/language, state-management library, build tooling, and the AWS compute service/topology (all inherited, unresolved-upstream items from `artifacts/architecture/solution-architecture.md`), the absent `docs/04-design/` wireframes/process-flow page, and the carried-forward ARCH-016-vs-PRD "no login" Non-Goal discrepancy — are accepted as known open items to be resolved in a later stage, not as blockers to publishing this narrative/stakeholder-facing document now.

Decided by:
human (unspecified name; account sparc.team12@experionglobal.com), via blanket "APPROVE" message during the `solution-architecture-publish-resume-agent` run on 2026-09-17.

Reason:
No open security-review marker exists on this document; remaining items are pre-existing `[TBD]` scoping gaps already disclosed in the document's own Gaps section and inherited from the approved `solution-architecture.md` engineering artifact (Gate ARCH-1 Round 2). The human's blanket APPROVE is sufficient to clear a document with no unaddressed `[SECURITY REVIEW REQUIRED]` marker.

Alternatives considered:
None offered by the human; no `APPROVE_WITH_CHANGES` or `STOP` was given for this document.

Impact:
`solution-architecture-overview.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. Document is now eligible for publication to Confluence via `.claude/skills/confluence-publish/SKILL.md`.

Related:
solution-architecture-overview.md (Agent: solution_architecture_overview)

## DEC-002 — Technology Stack approved at Architecture Suite Approval gate

Decision:
`artifacts/architecture/tech-stack.md` is APPROVED as submitted. This document carries no `[SECURITY REVIEW REQUIRED]` markers. Its open `[TBD]` items (frontend framework version/state-management/build tooling; backend API framework/language and runtime choices; API protocol; IAM session/token protocol and identity provider; observability/logging service; entire Security Tooling table; CI/CD tooling; entire Infrastructure-as-Code table; issue tracker/team-communication tooling) are accepted as known open items inherited from unresolved upstream architecture decisions (`solution-architecture.md`, ARCH-002/ARCH-018), not as blockers to publishing this document now.

Decided by:
human (unspecified name; account sparc.team12@experionglobal.com), via blanket "APPROVE" message during the `solution-architecture-publish-resume-agent` run on 2026-09-17.

Reason:
No open security-review marker exists on this document; remaining items are pre-existing `[TBD]` technology-choice gaps already disclosed in the document's own Summary section. The human's blanket APPROVE is sufficient to clear a document with no unaddressed `[SECURITY REVIEW REQUIRED]` marker.

Alternatives considered:
None offered by the human; no `APPROVE_WITH_CHANGES` or `STOP` was given for this document.

Impact:
`tech-stack.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. Document is now eligible for publication to Confluence via `.claude/skills/confluence-publish/SKILL.md`.

Related:
tech-stack.md (Agent: solution_tech_stack)

## DEC-003 — Security Architecture approved at Architecture Suite Approval gate (itemized clearing of MFA marker and two deferred items)

Decision:
`artifacts/architecture/security-architecture.md` is APPROVED. Unlike DEC-001/DEC-002, this was **not** a blanket approval — each of the three outstanding items was individually answered:

1. **§3 MFA marker (`[SECURITY REVIEW REQUIRED]`):** No MFA is required. Simple email + password login is accepted as sufficient for v1. This gap is accepted, not mitigated further.
2. **§3 marker 2 — ARCH-016 login vs. PRD "no login" Non-Goal:** Login remains required (ARCH-016 confirmed, not walked back). Formally recorded here as a deferral: the human will amend the PRD separately, in a future, dedicated PRD-amendment run, to reconcile the "no login" Non-Goal with the now-confirmed login requirement. Approval of this document is explicitly **not** blocked on that PRD amendment landing first.
3. **§11 marker 6 — login-email vs. "no personal/customer/payment data" Non-Goal:** Accepted as-is. The human does not consider a login email address to constitute a conflict with the PRD's Non-Goal requiring further mitigation; no additional PII control is required beyond what the document already describes.

The one item from DEC-001/DEC-002 that does not apply here: this document also carries several `[TBD]` items (session/token mechanism specifics, password-hashing library/version, AWS security-group configuration, failed-login alert threshold, and the full list of infrastructure/tooling gaps already disclosed in the document's own Summary section) — these remain open technical `[TBD]`s, not `[SECURITY REVIEW REQUIRED]` markers, and are accepted as known open items carried into a later engineering stage, consistent with the treatment given to the same category of items in DEC-001 and DEC-002.

Decided by:
sparc.team12@experionglobal.com, communicated to the coordinating orchestrator in the main session and relayed to this agent on 2026-09-17, itemized per the three specific outstanding markers (not a blanket approval).

Reason:
Per this agent's hard rule, a blanket approval cannot clear a document with an unaddressed `[SECURITY REVIEW REQUIRED]` marker — each open marker requires its own explicit answer. All three outstanding items (the MFA marker and the two "acknowledged and deferred" items previously recorded only as in-document narrative, not as a recorded gate decision) have now been individually answered by the human, satisfying that requirement.

Alternatives considered:
None offered; no `APPROVE_WITH_CHANGES` or `STOP` was given for this document.

Impact:
`security-architecture.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. Document is now eligible for publication to Confluence via `.claude/skills/confluence-publish/SKILL.md`, pending a fresh search-before-create check and a separate Gate 5 human confirmation before any `createConfluencePage` call. Note: the document's own body content (§3, §11, and the "Summary of `[SECURITY REVIEW REQUIRED]` markers" section) still narrates the MFA item as "carried forward... still open" and the two deferred items as unresolved narrative — this agent does not rewrite that body content (out of scope per this agent's hard rules; only the metadata block was updated). A future pass by `solution-security-architecture-agent` should reconcile the body narrative with this DEC-003 record.

Related:
security-architecture.md (Agent: solution_security_architecture)
