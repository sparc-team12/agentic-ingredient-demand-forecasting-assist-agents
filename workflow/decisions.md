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

## DEC-004 — PRD-change detection gate (Step 1.5): EDIT, not REGENERATE, for v1.1 → v1.3 drift

Decision:
The approved `artifacts/architecture/solution-architecture.md` (built against PRD `Version 1.1, Status: Approved`) is stale against the now-Confirmed Confluence PRD `Version 1.3` (page id `5883461703`). Human chose **EDIT**: `solution-architect-agent` (Step 2) and, in Step 3, only the suite specialists actually affected by the diff, are to patch their existing approved drafts against the v1.1→v1.3 diff rather than regenerating from a blank page. Their current `APPROVED` status does not exempt them from this patch — Step 2/3 will re-open them for a bounded, diff-scoped revision.

The diff driving this (from the PRD's own Change Log, v1.1 → v1.3):
- **Added (v1.2):** REQ-037–REQ-041 — Data Setup hub + 4 setup screens (Menu & Recipe, Ingredients & Suppliers, Current Stock, Sales History Import). Confirmed via grep that `solution-architecture.md` has zero coverage of these — a real scope gap, not cosmetic.
- **Added (v1.3):** REQ-042 — spoilage severity bands (Critical ≥₹2000 / High ₹500–1999 / Low <₹500).
- **Changed (v1.3):** REQ-007, REQ-009, REQ-012, REQ-023, REQ-026, REQ-027, REQ-034, REQ-039 — resolves OQ-1 through OQ-5 (safety-margin as per-ingredient/per-supplier config value, stockout severity band thresholds, materiality threshold default ₹500, dashboard cross-type ranking rule).
- **Retired:** none.

Decided by:
sparc.team12@experionglobal.com, via AskUserQuestion during the `/generate-architecture` run on 2026-09-17.

Reason:
Per the Step 1.5 hard rule, a new PRD version found in Approved/Confirmed status must never be silently absorbed (blind skip) or trigger a full regenerate without asking. The human judged the v1.1→v1.3 changes to be additive/incremental (new screens + concrete values resolving previously-open questions) rather than a scope overhaul, so EDIT (patch) was chosen over REGENERATE (full rewrite).

Alternatives considered:
REGENERATE (full fresh rewrite of solution-architecture.md and all four suite docs) and STOP (hold the run) were offered; not chosen.

Impact:
Governs both Step 2 (solution-architect-agent patches `solution-architecture.md`) and Step 3 (`solution-architecture-suite-orchestrator-agent` dispatches only the affected suite specialists in patch mode) for the remainder of this `/generate-architecture` run. `docs/01-prd/prd-ingredient-demand-forecasting.md` was already refreshed to v1.3 in Step 1 of this same run.

Related:
solution-architecture.md (ARCH-XXX, Agent: solution_architect), REQ-037–REQ-042

## DEC-005 — Solution Architecture (ARCH-XXX) re-approved at Gate ARCH-1 after Step 1.5 EDIT patch

Decision:
`artifacts/architecture/solution-architecture.md` is APPROVED at Gate ARCH-1, covering the DEC-004 EDIT patch against PRD v1.3: five new elements (ARCH-023 Data Setup hub, ARCH-024 Menu & Recipe Setup, ARCH-025 Ingredients & Suppliers Setup, ARCH-026 Current Stock Setup, ARCH-027 Sales History Import — REQ-037–041) and four patched elements (ARCH-002, ARCH-006, ARCH-007, ARCH-013 — reflecting the OQ-1–OQ-5 resolved values and REQ-042). This was not a blanket approval on the first pass — the human first returned **REQUEST_CHANGES** with feedback that the document should not narrate its own edit history (no "Round 1/Round 2/Step 1.5 EDIT patch" language, no "previously X, now resolved to Y" phrasing per element); `solution-architect-agent` rewrote the document as a single current-state narrative (all 27 ARCH-XXX ids and their substantive content, traceability, and resolved values preserved — only the diff/history framing was removed), and the human then approved that rewrite.

The irreversible technology choices carried into this approval (unchanged in substance from the prior Round 1/Round 2 approvals, now stated plainly rather than narrated as prior-round decisions): React (ARCH-002), SQLite (ARCH-012), self-hosted Gemma 4B (ARCH-015), AWS (ARCH-018). The AuthN/AuthZ posture (ARCH-016, basic email+password, single shared login) is also carried forward unchanged, including its still-open discrepancy against the PRD's stated "single user, no login, no roles" Constraint/Non-Goal — this approval does not resolve that discrepancy; it remains deferred to a future `prd-agent` PRD-amendment run.

Decided by:
sparc.team12@experionglobal.com, via AskUserQuestion during the `/generate-architecture` run on 2026-09-17 (REQUEST_CHANGES on the first presentation, APPROVE on the rewritten presentation).

Reason:
Per Step 2's Gate ARCH-1 rule, a general "looks good" does not clear this gate — each flagged irreversible decision (React, SQLite, Gemma 4B, AWS) and the login/PRD discrepancy were named explicitly in the gate presentation before the human approved. The REQUEST_CHANGES round addressed a presentation concern (the document should stand on its own, not read as a change-tracking diff), not a substantive one — no design decision was reopened or altered between the two presentations.

Alternatives considered:
STOP was available at both rounds; not chosen. A further REQUEST_CHANGES round was available after the rewrite; not needed — the human approved on the second presentation.

Impact:
`solution-architecture.md` metadata updated to `Status: Approved`, `Human approval status: APPROVED`, `Source artifact` recorded as PRD Version 1.3/Confirmed. This document is now the current input for `/generate-architecture` Step 3 (`solution-architecture-suite-orchestrator-agent`), which will patch/regenerate whichever of the four suite documents (Solution Architecture Overview, Security Architecture, Technology Stack, Infrastructure Architecture) are affected by the same v1.1→v1.3 diff, per the DEC-004 EDIT decision.

Related:
solution-architecture.md (ARCH-001 through ARCH-027, Agent: solution_architect), DEC-004, REQ-037–REQ-042

## DEC-006 — Architecture Suite Approval gate: all four suite documents approved (PRD v1.3 patch round)

Decision:
All four architecture suite documents are APPROVED:
- `solution-architecture-overview.md` — PATCHED (Data Setup capability/actor added, resolved severity-band/threshold values reflected, source metadata updated to ARCH-027/PRD v1.3).
- `tech-stack.md` — PATCHED (frontend screen inventory corrected to include the five Data Setup screens; no technology choice changed).
- `security-architecture.md` — PATCHED, narrow (DEC-003's 8 itemized decisions preserved verbatim and not reopened; one addition — a new `[TBD]` in §4 for Data Setup import validation, explicitly reviewed at this gate and confirmed to remain a `[TBD]`, not escalated to `[SECURITY REVIEW REQUIRED]`).
- `infrastructure-architecture.md` — NEWLY GENERATED (did not exist before this run; heavily `[TBD]` on region/compute-service/IaC-tool/CI-CD-tooling since no upstream artifact names them).

Zero open `[SECURITY REVIEW REQUIRED]` markers across the suite. Every `[TBD]` item touched by this patch round was individually presented at this gate (see the run's Gate — Architecture Suite Approval message) rather than cleared by a blanket approval; the one substantive judgment call (the new Data Setup import-validation gap) was decided explicitly, not inferred.

Decided by:
sparc.team12@experionglobal.com, via AskUserQuestion during the `/generate-architecture` run on 2026-09-17 — two separate confirmations: (1) leave the Data Setup import-validation gap as `[TBD]` rather than escalating it, and (2) approve all four documents.

Reason:
Per Step 3's gate rule, a blanket approval cannot clear an unacknowledged `[SECURITY REVIEW REQUIRED]` marker, and every `[TBD]`/marker must be individually presented. There were zero open markers this round, but the one genuinely new judgment call (import-validation gap severity) was surfaced and decided on its own before the overall APPROVE was accepted.

Alternatives considered:
Escalating the import-validation gap to `[SECURITY REVIEW REQUIRED]` was offered; not chosen. REQUEST_CHANGES and STOP were available for the overall gate; not chosen.

Operational note:
The `solution-architecture-suite-orchestrator-agent` run that produced these four documents reported it had no subagent-dispatch tool available and performed each specialist's patch/generation work directly under its own authority (reading each specialist's agent-definition contract and matching its output structure/hard rules), rather than actually invoking `solution-architecture-overview-agent`, `solution-security-architecture-agent`, `solution-tech-stack-agent`, and `infra-architecture-agent` as separate agents. This was disclosed transparently by the orchestrator agent and surfaced to the human before this approval was sought; the human approved with this known.

Impact:
All four documents' `Status`/`Human approval status` updated to `APPROVED`. Three (`solution-architecture-overview.md`, `tech-stack.md`, `security-architecture.md`) have prior Confluence publications (page IDs 5885984847, 5885657157, 5885821047) and will need an UPDATE, not a CREATE, on next publish — `config/project.yaml` currently has `allow_updates: false`, so this needs explicit human confirmation before `/generate-architecture`'s Step 3 publish sub-step ("Before Step 3 can actually publish") can proceed. `infrastructure-architecture.md` has no prior publication and will be a CREATE (`create_if_missing: true` already permits this).

Related:
solution-architecture-overview.md (Agent: solution_architecture_overview), tech-stack.md (Agent: solution_tech_stack), security-architecture.md (Agent: solution_security_architecture), infrastructure-architecture.md (Agent: infra_architecture), DEC-001, DEC-002, DEC-003, DEC-004, DEC-005

**Publication outcome (2026-09-17, same run):** `config/project.yaml`'s `allow_updates` was flipped to `true` for this run specifically to cover the three UPDATEs below (see the comment left in that file). `confluence-publish` was invoked with all four documents; the initial `contentFormat: "markdown"` update attempt on Solution Architecture Overview was rejected by the API (422 — the existing page contains info/note panels, an expand, and an extension that markdown cannot represent without data loss), so all four were republished using `contentFormat: "html"` instead, converting each document's full content (Confluence's converter upgraded the mermaid fenced-code blocks to its native Mermaid-diagram extension automatically). All four succeeded:

| Document | Action | Page ID | Version | URL |
|---|---|---|---|---|
| Solution Architecture Overview | UPDATE | 5885984847 | 2 | https://experionglobal.atlassian.net/wiki/spaces/~712020c78d0510dbf248218881c00989970857/pages/5885984847/Solution+Architecture |
| Technology Stack | UPDATE | 5885657157 | 3 | https://experionglobal.atlassian.net/wiki/spaces/~712020c78d0510dbf248218881c00989970857/pages/5885657157/Technology+Stack |
| Security Architecture | UPDATE | 5885821047 | 2 | https://experionglobal.atlassian.net/wiki/spaces/~712020c78d0510dbf248218881c00989970857/pages/5885821047/Security+Architecture |
| Infrastructure Architecture | CREATE | 5885722960 | 1 | https://experionglobal.atlassian.net/wiki/spaces/~712020c78d0510dbf248218881c00989970857/pages/5885722960/Infrastructure+Architecture |

4 `PUBLISHED` events recorded in `workflow/events.jsonl` (each with `decision_ref: "DEC-006"`). `workflow/status.json` was not updated — this Shape B (standalone-PRD) project has never populated its discovery-pipeline workflow-tracking schema (`activeWorkflowId: null`, no workflow entries), consistent with every artifact in this run being labeled `Workflow ID: UNASSIGNED`/`N/A`; inventing a workflow entry there was judged out of scope for this publish step.

## DEC-007 — DevOps Defaults Approval gate: tf-coding-inputs.md approved (22 assumptions) with 6 organizational facts deferred

Decision:
`artifacts/architecture/tf-coding-inputs.md` (produced by `infra-devops-expert-agent` from `infrastructure-architecture.md`/`tech-stack.md`'s open `[TBD]` fields) is APPROVED as submitted — all 22 numbered engineering-default assumptions (VPC CIDR `10.0.0.0/16`; 1 public + 1 private subnet, no NAT; two separate EC2 instances for app vs. LLM; app compute EC2 `t3.small`; `gp3` 20 GiB unencrypted disk; LLM compute EC2 `m6i.xlarge` CPU-only; LLM inbound restricted via security group to the app instance; CloudWatch Logs sink, 30-day retention; no WAF/CDN/load balancer; naming convention `<app>-<resource>-<env>` with app token `ingredient-forecast`; `ManagedBy` tag `terraform`; region `us-east-1`; cost profile `low`; prod-only environment topology; IaC tool Terraform; S3+DynamoDB state backend with key pattern `terraform/<stack>/<env>/terraform.tfstate`; trunk-based branching; GitHub Actions CI/CD; tflint + terraform validate + checkov; GitHub Environments required-reviewers manual-approval gate) were individually presented and confirmed, not cleared by a blanket approval.

The 6 organizational-fact gaps that cannot be inferred by any engineering judgment — AWS account ID, `Owner` tag value, `CostCenter` tag value, final Terraform state-bucket name (blocked on account ID for global-uniqueness suffixing), persistent-disk backup/snapshot cadence, and the GitHub reviewer group/individuals for the manual-approval gate — are explicitly DEFERRED, not silently passed through. `infra-terraform-coding-agent` is to proceed using placeholders (e.g. `{{ACCOUNT_ID}}`) for these fields rather than treating them as resolved.

Decided by:
sparc.team_17@experionglobal.com, via two separate AskUserQuestion confirmations during the `/terraform-code` run on 2026-09-17 — (1) explicit approval of all 22 assumptions by number, and (2) explicit choice to defer all 6 organizational-fact gaps with placeholders rather than supply real values now.

Reason:
Per the `/terraform-code` command's Step 0.5 hard rule, a blanket "approve" that doesn't address each flagged assumption/gap by name does not clear this gate. The human's first "APPROVE" message was rejected as insufficient on that basis and re-asked in itemized form before being accepted.

Alternatives considered:
`REQUEST_CHANGES` (routing back to `infra-devops-expert-agent` to revise specific items) and `STOP` were available for the assumptions question; not chosen. Supplying real organizational-fact values now was available for the gaps question; not chosen — deferred with placeholders instead.

Impact:
`tf-coding-inputs.md` metadata updated to `Status: APPROVED`, `Human approval status: APPROVED`. This file (not raw `infrastructure-architecture.md`) becomes the source for `infra-terraform-coding-agent`'s Terraform generation. Generated Terraform/tags will carry `{{ACCOUNT_ID}}`, `{{OWNER}}`, `{{COST_CENTER}}` (and equivalent) placeholders for the 6 deferred fields rather than real values.

Related:
tf-coding-inputs.md (Agent: infra_devops_expert), infrastructure-architecture.md (DEC-006), tech-stack.md (DEC-002, DEC-006)

## DEC-008 — Override: single combined app+LLM instance (prod), superseding DEC-007 assumption #3

Decision:
`tf-coding-inputs.md` assumption #3 (deployable-unit topology — "two separate EC2 instances, app vs. LLM," approved under DEC-007) is overridden. Prod now runs exactly **one** EC2 instance hosting both the application and the self-hosted Gemma 4B model. Consequences applied directly to the generated Terraform (not just the input document):
- `infra/network/`: removed the private subnet (`ingredient-forecast-subnet-private-prod`) and its variables/output — no longer any tenant needing network isolation.
- `infra/application/`: removed the `llm_instance` module call, the `llm_security_group` module call, and the `llm_inference_port`/`llm_*` variables; the app's instance size was raised to `m6i.xlarge` (30 GiB root volume) — carried over from the LLM instance's original sizing, since one instance must now cover both workloads.
- `tf-coding-inputs.md`: assumptions #2, #3, #5, #7, #8, #9 updated/struck through to match, with the original approved reasoning kept visible (not deleted) alongside the override.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-17 — "we only want one instance which is prod we want to generate according to that."

Reason:
Explicit user preference for operational simplicity (one instance to manage, patch, and pay for) over the independent-resize/patch and security-group-isolation benefits DEC-007 originally cited for two instances. No new PRD/architecture information changed — this is a direct human override of a previously-approved engineering assumption, not a re-run of `infra-devops-expert-agent`.

Alternatives considered:
Keeping two instances (the DEC-007 default) was the status quo; not chosen. Re-running `infra-devops-expert-agent` from scratch to re-derive a topology was not necessary since the user's instruction was unambiguous.

Impact:
Instance sizing is now a carried-over assumption (LLM's original `m6i.xlarge`/30 GiB), not a value derived for the combined workload's actual needs — flagged in `infra/application/README.md` and `tf-coding-inputs.md` as needing right-sizing after real load testing. The LLM's original network-isolation security control (security-architecture.md §7 marker 5, restricting its inbound traffic to the app instance only) is now moot — there is no network path between them to restrict, since both run on one instance and communicate over localhost.

Related:
tf-coding-inputs.md (Agent: infra_devops_expert, DEC-007), infra/application/main.tf, infra/application/variables.tf, infra/network/main.tf, infrastructure-architecture.md §3/§4 (ARCH-017's "one deployable unit vs. two" — now resolved as one)

## DEC-009 — Flatten infra/ to a single directory; drop self-hosted LLM for the Gemini API, resize to t3.micro

Decision:
Two changes, both by explicit user instruction on 2026-09-17:
1. **Layout:** `infra/` is flattened from the modules/root-modules/environments structure (already reduced to one instance under DEC-008) into a single flat directory — `main.tf` (everything inline: VPC, subnet, security group, EC2, EBS, EIP, CloudWatch log group, IAM role), `variables.tf`, `terraform.tfvars`, `backend.tf`/`backend.hcl`, `outputs.tf`. The `modules/`, `network/`, `application/`, and `environments/` directories were deleted.
2. **Compute:** the self-hosted Gemma 4B model (ARCH-015) is dropped entirely. AI functionality is now provided by a Python process calling the external Gemini API (a free-tier key), not a locally-run model. The instance is resized from DEC-008's carried-over `m6i.xlarge` to `t3.micro` — there's no local model to run, just an app process making outbound API calls.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-17 — after being asked to choose a target layout (fully flat / single-root-still-modular / leave as-is), replied: "we will flatten the structure itself we will use a python file with free gemini api keys for invoking ai about the product details and all so create a single file terraform with t3.micro."

Reason:
User judged the module/root-module/environments structure not worth its file count for one instance and one environment (explicit "still there is a lot of folder structure and document" feedback), and separately decided to use the free-tier Gemini API instead of self-hosting an LLM, which removes the compute justification for anything larger than the smallest instance tier.

Alternatives considered:
Two other layout options were offered and not chosen: keeping the modular structure with network/application merged into one root but modules/ retained; and leaving the current (DEC-008) structure entirely as-is.

Impact:
- `infra/` now has no module indirection and one state file (no more `terraform_remote_state` data source).
- `tf-coding-inputs.md` assumption #5 revised again (t3.micro, superseding DEC-008's m6i.xlarge); its LLM-inference-specific rows (formerly #7/#8/#9, already struck through under DEC-008) are now doubly moot.
- **Not yet done, flagged not silently skipped:** `solution-architecture.md` (ARCH-015 "self-hosted Gemma", ARCH-017 "zero external, third-party network dependencies"), `security-architecture.md`, and `tech-stack.md` still describe the self-hosted-LLM design and have not been updated to reflect the Gemini API dependency. This is a real architecture change (an external third-party API now exists in the data path), not just an infra-sizing change, and those documents are now stale relative to what's actually being built. Surfaced in `infra/README.md`'s "Gemini-API decision" section; revisiting those documents was out of scope of this specific instruction.
- The Python integration code itself (the Gemini API client, key handling) is application code, not Terraform, and was not created as part of this change — the API key is expected to land in the same `.env` file security-architecture.md §6 already designates for secrets.

Related:
infra/main.tf, infra/variables.tf, infra/terraform.tfvars, infra/README.md, tf-coding-inputs.md (DEC-007, DEC-008), solution-architecture.md ARCH-015/ARCH-017 (now stale, not yet revised)

## DEC-010 — Propagate the Gemini API / single-instance / t3.micro change into the full architecture suite

Decision:
Following DEC-009's infra-layer change (Gemini API replacing self-hosted Gemma; `t3.micro` instead of `m6i.xlarge`; flat `infra/` layout), the user asked to update the architecture suite itself to match. Updated, with the original approved content preserved as struck-through historical record rather than silently deleted:
- `solution-architecture.md` — ARCH-015 (LLM provider) rewritten for the Gemini API, with the original self-hosted-Gemma decision kept as a labeled historical record; ARCH-017 ("zero external dependencies") revised — that claim is retracted, not merely qualified; ARCH-018 and ARCH-019's assumptions/notes updated to drop the now-moot GPU/CPU-sizing consequence; the summary diagram's LLM node moved outside the AWS boundary (it's genuinely external now); Open Items section updated.
- `security-architecture.md` — added a **new, currently OPEN `[SECURITY REVIEW REQUIRED]` marker (marker 9)**: DEC-010 reintroduces the exact data-confidentiality risk (supplier cost data leaving organization-controlled infrastructure) that the original self-hosted decision was chosen to avoid. §2 diagram, §3 (M2M auth), §6 (secrets), §7 (encryption/network-segmentation — marker 5 marked superseded/moot), §8 (security groups/egress — now meaningful, since egress is open and unscoped), §11/§12 (compliance/PII), and §14 (incident response) updated to match. Marker 9 is **not resolved** — this document has not been re-presented at the Architecture Suite Approval gate for this specific change.
- `tech-stack.md` — §2 diagram, §7 (app-to-LLM call, now a real external API integration), §14 (External Systems & APIs — previously asserted zero external systems, now lists the Gemini API), §12 (IaC tooling — resolved to Terraform, confirmed by the actual generated code, incidentally fixing a pre-existing stale `[TBD]`), and §15 (rationale) updated.
- `infrastructure-architecture.md` — §2 (Architecture Overview), §3 (diagram — Gemini API moved outside the AWS account boundary), §4 (Resource Inventory — LLM-inference compute row removed, Gemini API added as an external dependency row), and the Gaps section updated.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-18 — "update all the architecture to this new implementation."

Reason:
DEC-009 changed the infrastructure layer but left the engineering architecture documents (which the infrastructure was originally derived from, and which are the human-approved, Confluence-published record of the system's design) silently out of sync. Since this session had already established a pattern of surfacing exactly this kind of drift rather than letting it pass quietly (the whole PRD-change-detection-gate and mandatory-`[TBD]`-question work earlier in this session), updating the documents to match was the consistent thing to do rather than leaving them stale.

Alternatives considered:
Leaving the four documents as-is (with only `infra/README.md`'s and `tf-coding-inputs.md`'s revision notes pointing at the drift) was the status quo before this decision; not chosen, per the user's explicit instruction.

Impact:
All four documents' bodies now reflect the Gemini API / single-instance / `t3.micro` design, with original approved content preserved as visible historical record (struck through or in a labeled "historical record" block), not deleted — consistent with how DEC-008/DEC-009 were recorded in `tf-coding-inputs.md`. **None of the four documents' `Human approval status` metadata fields were changed to reflect a fresh approval** — they remain in whatever state they were in before this edit, and `security-architecture.md`'s new marker 9 is explicitly recorded as open and unresolved. This content update does not itself constitute the security-review sign-off marker 9 requires; per this repo's own hard rule (`solution-architecture-suite-orchestrator-agent`'s Human gate), that marker must still be individually presented to and answered by a human before it can be considered closed, and before any of these documents could be considered re-approved as a whole.

Related:
solution-architecture.md (ARCH-015, ARCH-017, ARCH-018, ARCH-019), security-architecture.md (marker 9, new/open), tech-stack.md, infrastructure-architecture.md, DEC-005 (original Gate ARCH-1), DEC-006 (original Architecture Suite Approval), DEC-009

## DEC-011 — Consolidate infra/ into a single main.tf; remove variables.tf, outputs.tf, terraform.tfvars, backend.tf, backend.hcl

Decision:
`infra/` (already flattened to one directory under DEC-009) is consolidated further into exactly one Terraform file, `main.tf`, containing the `terraform`/`backend`/`provider` blocks, every `variable` declaration (now each carrying a `default` equal to what used to live in `terraform.tfvars`, so no `-var-file` is needed to apply), every resource, and every output. `variables.tf`, `outputs.tf`, `terraform.tfvars`, `backend.tf`, and `backend.hcl` were deleted. `iam-policy.json` and `README.md` were kept — the former is a distinct, non-Terraform artifact (an IAM policy document for the operator, not HCL Terraform reads), the latter is documentation.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-18 — "generate a single terraform file for setting up the instance in the infra and remove all the unnecessory files."

Reason:
Continues the same simplification direction as DEC-009 (flattening modules/root-modules/environments to one directory) — for one instance and one environment, a single file is more legible than five small ones, and folding `terraform.tfvars`'s values into variable defaults removes the need for a companion file to make `terraform apply` runnable at all.

Alternatives considered:
Keeping `iam-policy.json` as a JSON-embedded string inside `main.tf` was considered and rejected — it's not something Terraform reads or manages, and inlining it would make the actual IAM policy harder to read/copy for whoever needs to attach it to an operator role.

Impact:
`terraform init`/`plan`/`apply` now only need `main.tf` (plus `-backend-config="bucket=..."` at init time, since the state-bucket name remains an unresolved organizational fact — DEC-007). Overriding a value now requires `-var="..."` on the command line rather than editing a `.tfvars` file. No resource definitions changed — this is a pure file-organization change; behaviorally identical to the DEC-009 layout.

Related:
infra/main.tf, infra/README.md, infra/iam-policy.json, DEC-009 (prior flattening)

## DEC-012 — GitHub Actions Terraform pipeline: static AWS keys, single-environment (no matrix), iam-policy.json out of scope

Decision:
Created `.github/workflows/terraform.yml` — a purpose-built pipeline matching the actual `infra/` layout (one `main.tf`, `prod`-only), not `infra-pipeline-agent`'s general per-environment/per-stack matrix template, since that template assumes a `network`/`application` split and a `dev`/`qa`/`stage`/`prod` matrix that no longer exist here (DEC-009/DEC-011). Four jobs: `lint` (tflint + checkov) → `validate` (terraform validate + fmt check) → `plan` (on every push/PR, uploads the plan artifact) → `apply` (push to `main` only, gated by the `prod` GitHub Environment's required-reviewers setting). AWS authentication uses static `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` GitHub Actions secrets (not OIDC role assumption) per explicit user choice. `iam-policy.json` (the least-privilege policy for whoever runs Terraform) is explicitly out of scope of this pipeline — the user will attach appropriate permissions to the credentials behind those two secrets themselves.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-18 — asked for the pipeline YAML, stated AWS auth tokens would be provided via GitHub Actions secrets ("dont worry about the .json file"), and when asked to choose between static keys and OIDC role assumption, chose static access key + secret key.

Reason:
Matching the pipeline's job structure to the actual (flattened, single-instance, single-environment) infra saves real complexity — a matrix over one environment and one stack is dead weight, not defensive design. Static keys were the user's explicit, informed choice over the OIDC alternative that was offered and explained.

Alternatives considered:
OIDC role assumption (`AWS_ROLE_ARN` secret, no long-lived keys) was offered and explained as the more secure default; not chosen. Reusing `infra-pipeline-agent`'s full per-environment matrix template as-is was not chosen, since it doesn't match this project's actual (simplified) infra layout.

Impact:
Before this pipeline can run successfully, the following must be configured in the GitHub repository (not done by this decision — a human/repo-admin task):
- A `prod` GitHub Environment with **Required reviewers** set (the manual-approval gate the `apply` job's `environment: prod` relies on).
- Repository secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `TFSTATE_BUCKET_NAME` (still a placeholder organizational fact — DEC-007).
- Optionally a repository variable `AWS_REGION` (defaults to `us-east-1` in the workflow if unset).
- The credentials behind the two AWS secrets must have permissions at least matching `infra/iam-policy.json` (with `{{ACCOUNT_ID}}`/`{{PROJECT_NAME}}` resolved) attached by the user themselves — this pipeline does not create or attach that policy.

Related:
.github/workflows/terraform.yml, infra/main.tf, infra/iam-policy.json, DEC-009, DEC-011

## DEC-013 — Application-code deploy pipeline (deploy.yml), adapted from a sample; several values are unconfirmed assumptions

Decision:
Created `.github/workflows/deploy.yml` — a separate workflow from `terraform.yml`, covering application-code deploy (SSH into the already-provisioned EC2 instance, pull latest, install/build, restart) rather than infrastructure provisioning. Adapted directly from a sample the user pasted from a different, unrelated project (`arc-forge-hackathon`'s `deploy.yaml`), not generated from this project's own architecture docs, because several of the facts it depends on don't exist yet in this repo: `src/backend` and `src/frontend` are both empty (no code, no `package.json`/`requirements.txt`), `tech-stack.md` §3/§4 still mark frontend build tooling and backend language/framework `[TBD]`, and no systemd unit or SSH key pair is provisioned by `infra/main.tf` or anywhere else. The backend is assumed Python (`pip install -r requirements.txt`) based on the user's earlier statement that AI integration is "a python file with free gemini api keys," not a confirmed tech-stack decision.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-18 — pasted a sample `deploy.yaml` from a different project and asked to "generate it for mine."

Reason:
User asked for a direct adaptation of a working example rather than a fresh design; honored that shape while flagging every place the adaptation rests on an assumption this repo hasn't actually confirmed, rather than silently presenting a guessed backend language/build process as decided.

Alternatives considered:
Declining to generate anything until `tech-stack.md`'s backend `[TBD]` items are resolved was considered and rejected — the user asked for the file now, and a clearly-flagged draft is more useful than nothing, provided the assumptions are visible rather than hidden.

Impact:
This pipeline **will not work as-is** — it references a systemd unit (`ingredient-forecast-app`) that nothing in this repo creates, and depends on `src/backend`/`src/frontend` actually containing code with the assumed tooling. Required before this can run: real application code in `src/`, a systemd service set up on the instance (or added to `infra/main.tf`'s `user_data`), an SSH key pair provisioned and authorized on the instance, and repo secrets `EC2_HOST`/`EC2_SSH_KEY`.

Related:
.github/workflows/deploy.yml, .github/workflows/terraform.yml (DEC-012), tech-stack.md §3/§4 (still [TBD])

## DEC-014 — Checkov CKV2_AWS_2 (unencrypted EBS) suppressed with a reference, not fixed by encrypting

Decision:
The `lint` job's Checkov scan (`soft_fail: false`, DEC-012) failed `CKV2_AWS_2` ("only encrypted EBS volumes attached to EC2 instances") against `aws_ebs_volume.data`. Rather than flipping `encrypted = true` — which would silently override an already-approved human decision — added inline `#checkov:skip=CKV2_AWS_2:...` (and, defensively, `#checkov:skip=CKV_AWS_8:...`) annotations to both `aws_instance.app`'s `root_block_device` and `aws_ebs_volume.data`, each citing `security-architecture.md` §7 marker 4 (the RESOLVED, human-approved "no at-rest encryption required for v1" decision) as the reason.

Decided by:
sparc.team12@experionglobal.com pasted the Checkov failure output directly; the response (suppress-with-reference, not silently encrypt) follows this session's standing rule against unilaterally overriding an already-recorded human decision, not a fresh confirmation from the user on this specific point.

Reason:
`encrypted = false` on both resources is not a bug — it's the literal implementation of a decision already made and recorded (security-architecture.md marker 4). A CI scanner correctly flagging an intentionally-accepted risk should be told about the acceptance (with a pointer to where it was decided and why), not overridden by changing the infrastructure to make the scanner happy, and not ignored via a blanket `soft_fail: true` that would also hide genuinely new findings.

Alternatives considered:
Setting `encrypted = true` was rejected — it would contradict an approved architecture decision without going back through a gate. Setting the `lint` job's Checkov step to `soft_fail: true` globally was rejected — too broad; it would silently swallow future, real findings along with this accepted one.

Impact:
The `lint` job's Checkov step should now pass without weakening its ability to catch other findings. If `security-architecture.md` marker 4 is ever revisited (e.g., at-rest encryption becomes required), these two skip annotations must be removed as part of that change, not left stale.

Related:
infra/main.tf, security-architecture.md §7 (marker 4), .github/workflows/terraform.yml (DEC-012)

## DEC-015 — Switch pipeline auth from static AWS keys to GitHub OIDC; add the OIDC provider/role to infra/main.tf

Decision:
Reverses part of DEC-012's choice. Added `aws_iam_openid_connect_provider.github_actions` and `aws_iam_role.github_actions` (trust policy scoped to `repo:sparc-team12/agentic-ingredient-demand-forecasting-assist-agents:*` via `token.actions.githubusercontent.com:sub`, plus the `aud=sts.amazonaws.com` condition) to `infra/main.tf`, and a new `github_actions_role_arn` output. Updated `.github/workflows/terraform.yml`'s `plan` and `apply` jobs to use `role-to-assume: ${{ secrets.AWS_ROLE_ARN }}` via OIDC (with `permissions: id-token: write` added to both jobs) instead of `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`. Permissions for the new role are deliberately not wired up in Terraform — same as DEC-012, the user attaches them.

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-18 — "Im using OIDC as the authentication and connection from the github to aws."

Reason:
Direct, explicit reversal of the earlier choice (DEC-012 asked and the user picked static keys at the time; they've since decided to use OIDC instead) — no long-lived AWS credentials need to be stored as GitHub secrets this way.

Alternatives considered:
Keeping the static-key setup from DEC-012 was the status quo; superseded by this explicit change, not run side-by-side.

Impact:
**Bootstrapping requirement, not yet satisfiable by the pipeline itself:** the very first `terraform apply` that creates the OIDC provider and role must run with separate credentials (e.g. the user's own local AWS CLI access) — the pipeline cannot assume a role that doesn't exist yet. After that one-time apply, the role's ARN (from the new `github_actions_role_arn` output) must be stored as the repo's `AWS_ROLE_ARN` secret, and `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (DEC-012) are no longer used by the pipeline (harmless to leave configured or to remove). `infra/README.md`'s placeholder/setup table should be updated to reflect `AWS_ROLE_ARN` instead of the two static-key secrets.

Related:
infra/main.tf (aws_iam_openid_connect_provider.github_actions, aws_iam_role.github_actions), .github/workflows/terraform.yml, DEC-012 (superseded on auth method only)

## DEC-016 — Fixed the three remaining Checkov findings for real (KMS log encryption, detailed monitoring, VPC flow logs)

Decision:
Unlike DEC-014 (suppress-with-reference for already-decided items), these three had no prior decision behind them, so they were fixed directly rather than suppressed: added `aws_kms_key.logs` (CMK, key rotation enabled) and wired it into `aws_cloudwatch_log_group.app` (CKV_AWS_158); added `monitoring = true` to `aws_instance.app` (CKV_AWS_126); added VPC Flow Logs — `aws_cloudwatch_log_group.vpc_flow_logs`, `aws_iam_role.vpc_flow_logs` + policy, and `aws_flow_log.vpc` (CKV2_AWS_11).

Decided by:
sparc.team12@experionglobal.com, directly in conversation on 2026-09-18 — pasted the three remaining Checkov failures and asked "why these errors can we fix these."

Reason:
User asked for fixes, not just explanations. Detailed monitoring and the flow-log role/policy are cheap and add real observability value; the KMS key is one new resource shared by both log groups, not per-log-group duplication.

Alternatives considered:
Suppressing CKV_AWS_158 (default AWS-owned-key encryption is already applied; a CMK adds no compliance-driven benefit — security-architecture.md §11 finds no regulation applies) was the leaner option and was explained as a judgment call before fixing it properly instead, per the user's explicit "fix these."

Impact:
New resources requiring additional IAM permissions beyond what `infra/iam-policy.json` currently lists (kms:CreateKey/PutKeyPolicy/CreateAlias etc., iam:CreateRole/PutRolePolicy for the flow-logs role, ec2:CreateFlowLogs/DeleteFlowLogs) — relevant once that file (or its replacement) is recreated/reconciled per the pending question about the deleted `infra/README.md`/`iam-policy.json`/`deploy.yml` files. `CKV_AWS_382` (wide-open security-group egress) remains unaddressed — not part of this specific ask.

Related:
infra/main.tf (aws_kms_key.logs, aws_cloudwatch_log_group.vpc_flow_logs, aws_iam_role.vpc_flow_logs, aws_flow_log.vpc), DEC-014

## DEC-017 — Scope security-group egress to HTTPS (443) only, resolving the CKV_AWS_382 finding and security-architecture.md's egress-scoping TBD

Decision:
`aws_security_group.app`'s egress rule changed from all ports/protocols (`0.0.0.0/0`, protocol `-1`) to HTTPS only (`443/tcp`, `0.0.0.0/0`). Resolves Checkov `CKV_AWS_382` and the specific "should egress be scoped" question `security-architecture.md` §8 left open after DEC-010 (distinct from — and does not resolve — the broader marker 9 data-confidentiality question of whether sending data to Gemini at all is acceptable).

Decided by:
sparc.team12@experionglobal.com pasted the `CKV_AWS_382` failure; this was the previously-identified "recommended" option (scope to 443) from an earlier (rejected) multi-choice question, applied directly since the user has consistently asked for fixes over discussion in this session.

Reason:
Gemini API is HTTPS-only and is the only outbound dependency the application has — 443 covers the real need with no functional loss, and is a strict narrowing of what egress was previously open.

Alternatives considered:
Leaving egress fully open and suppressing `CKV_AWS_382` with a reference (the same treatment as DEC-014's already-approved items) was the other option surfaced earlier; not chosen — this wasn't an already-approved decision the way encryption was, so tightening it for real was preferred over documenting an acceptance of unnecessary exposure.

Impact:
If OS package installs during instance bootstrap need plain HTTP (port 80) egress (some older apt/yum mirrors aren't HTTPS-only), that would need a second egress rule added — not currently present. `security-architecture.md` §8 updated to mark this resolved; marker 9 remains open and unrelated to this specific fix.

Related:
infra/main.tf (aws_security_group.app), security-architecture.md §8 (marker 9 still open), DEC-010

## DEC-018 — Fixed `terraform fmt -check` failure: misaligned `=` in aws_route.igw

Decision:
`terraform fmt -check -recursive` failed in CI (exit code 3). Root cause: `aws_route.igw`'s `gateway_id` line had one extra space before `=`, breaking Terraform's column-alignment convention with the other two attributes in that block (`route_table_id`, `destination_cidr_block`). Fixed by removing the stray space. No Terraform CLI is available in this execution environment, so alignment across the whole file was verified with a PowerShell script that checks every contiguous group of single-line attribute assignments for consistent `=` column position, rather than by eye.

Decided by:
sparc.team12@experionglobal.com pasted the CI log showing the `terraform fmt` failure; this is a pure formatting fix with no judgment call involved, so no confirmation was sought before applying it.

Reason:
`terraform fmt -check` requires exact canonical formatting; a single stray space fails the whole check regardless of severity. This particular misalignment likely originated from one of the many sequential edits made to this file across the session.

Alternatives considered:
None — this is a mechanical formatting fix, not a design decision.

Impact:
`terraform fmt -check -recursive` should now pass. The alignment-check script also flagged `Sid`/`Effect`/`Principal`/`Action` in the `aws_kms_key.logs` policy's second statement as "misaligned" — confirmed to be a false positive (a multi-line list value, `Action = [...]`, legitimately breaks Terraform's alignment grouping from the single-line attributes above it), not a real formatting bug.

Related:
infra/main.tf (aws_route.igw)
