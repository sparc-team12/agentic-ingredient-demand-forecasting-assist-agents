# Setup Decisions

Decisions made while building the product discovery orchestrator system itself, per `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md` §1.8. (Decisions made *during a product discovery workflow* — e.g. an architecture or scope choice — belong in `workflow/decisions.md`, not here.)

## SD-001 — Orchestration logic lives in a skill, commands are thin dispatchers

The spec allows either `.claude/skills/*/SKILL.md` or `.claude/commands/*.md` for reusable workflow logic, and asks for ~15 different commands (`/product-plan`, `/research`, `/features`, ... `/retry`, `/skip`). Putting the full gate/validation/Confluence logic in every command file would duplicate it 15 times. Instead, all orchestration procedure lives in `.claude/skills/product-discovery/SKILL.md`, and each command file is a short dispatcher naming its mode and delegating there. This keeps the gate logic in one place to change.

## SD-002 — `workflow/status.json` is a multi-workflow registry

The spec's example schema shows a single flat workflow object at the top of `status.json`. Since `/product-plan` can be run more than once in this repo over time, `status.json` is instead `{ "activeWorkflowId", "workflows": { "<id>": {...spec schema...} } }` — each value under `workflows` matches the spec's example schema exactly. This is additive, not a deviation from the required fields.

## SD-003 — Demo domain uses this repo's actual purpose, not "furniture e-commerce"

The spec's demo example (`examples/furniture-ecommerce.md`) is a generic placeholder from the template document. Since this repository is specifically `agentic-ingredient-demand-forecasting-assist-agents`, the demo input was written as `examples/ingredient-demand-forecasting.md` describing an ingredient demand forecasting assistant instead, so the walkthrough exercises a scenario relevant to this repo. The workflow/commands/agents themselves remain fully domain-agnostic.

## SD-004 — Confluence integration verified via the claude.ai Atlassian Rovo connector, not `claude mcp add`

The spec assumes a Claude Code CLI setup where Atlassian MCP may need to be added with `claude mcp add --transport http atlassian ...`. This session is running as a Claude Code VS Code extension with the **claude.ai Atlassian Rovo** connector already available. Verified live on 2026-09-17 via `atlassianUserInfo` (account: sparc.team12@experionglobal.com) and `getAccessibleAtlassianResources` (site: `https://experionglobal.atlassian.net`, scopes include read/write Confluence pages and comments, read/write Jira work). `config/project.yaml` records this site as a convenience default. **Not yet confirmed:** which Confluence space and parent page to publish under — those are intentionally left blank in `config/project.yaml` pending a human decision (Gate 5 will ask before first publish).

## SD-005 — No pre-populated artifact/example content beyond the demo input

`artifacts/` subfolders are not pre-created with placeholder files — they appear only when their owning agent actually runs, so nothing in the repo could be mistaken for a real (but fabricated) requirements/estimate/risk output.

## SD-006 — Validation and Confluence-publishing extracted into their own reusable skills

The spec's §9 explicitly calls out "reusable reviewer skills" for the consistency/completeness/feasibility/quality-security checks, separately from the general "prefer skills for reusable workflows" guidance in §10. On review, the original `product-discovery/SKILL.md` had this checklist (and the full Confluence §13–14 procedure) inlined, which meant `/review` and `/publish` couldn't be exercised without pulling in the entire orchestration file, and the checklist logic wasn't reusable outside a workflow context. Split out:

- `.claude/skills/validation-review/SKILL.md` — the four-dimension checklist, invoked standalone by `/review` and by `product-discovery` before Gate 4.
- `.claude/skills/confluence-publish/SKILL.md` — MCP-connector verification, site/space/parent-page confirmation, search-before-create, CREATE-vs-UPDATE detection, and the actual publish calls, invoked by `/publish` and by `product-discovery`'s Gate 5.

`product-discovery/SKILL.md` now delegates to both rather than duplicating their content; it remains the sole writer of `workflow/status.json` and `workflow/events.jsonl` — the two sub-skills return data, they don't write workflow files themselves.

## SD-007 — Orchestrator consolidation: one canonical orchestrator, sole Confluence/Jira access

An audit found four coexisting orchestration mechanisms: `product-discovery-orchestrator.md` and `prd-orchestrator-agent.md` (byte-identical duplicates, both self-describing as "the live orchestrator," dispatching two different specialist name-sets), `solution-architecture-suite-orchestrator-agent.md` (a real second, narrower orchestrator scoped to the 3-document architecture suite), and `product-discovery/SKILL.md` (the actual procedure all commands delegate to). It also found `prd-agent.md` deciding for itself when to dispatch `research-requirements-agent` — a hidden-orchestrator pattern.

Consolidated to a single canonical orchestrator, `.claude/agents/orchestrator-agent.md`:
- `product-discovery-orchestrator.md` was renamed to `orchestrator-agent.md` (kept as the base — it referenced the live, non-prefixed specialist names).
- `prd-orchestrator-agent.md` was deleted (pure duplicate).
- `solution-architecture-suite-orchestrator-agent.md` was deleted; its responsibilities became `orchestrator-agent.md`'s Architecture Suite workflow (dispatched via a new `GENERATE_ARCHITECTURE` mode in `product-discovery/SKILL.md` §3/§7b), so `/generate-architecture` now routes through the same orchestrator instead of embedding its own procedure or a sub-orchestrator.
- Six orphaned, already-drifted forks of live specialist agents (`prd-feature-analyst-agent.md`, `prd-research-requirements-agent.md`, `prd-risk-compliance-agent.md`, `prd-user-story-analyst-agent.md`, `planning-estimation-cost-agent.md`, `solution-uiux-designer-agent.md`) were deleted — referenced by nothing, kept as duplicates of no benefit.
- `prd-agent.md` no longer dispatches `research-requirements-agent` itself; it flags the need to `orchestrator-agent`, which dispatches it and hands the result back.
- Confluence MCP tool access moved entirely from `prd-agent.md` to `orchestrator-agent.md` — `orchestrator-agent` is now the only agent in the discovery/architecture-suite pipeline with Confluence/Jira access. `prd-agent`'s "publish the confirmed PRD" behavior became `orchestrator-agent`'s post-Gate-1 publish step (see SD-008 — this later became the PRD's normal publish point, not an "optional early" one).

**Explicitly out of scope for this pass** (by the human's direction, not an oversight): the ported SDLC pipeline (`docs-knowledge-agent` → ... → `release-deploy-agent`) and the change-request pipeline (`prd-change-request-agent` → ...) remain un-gated and un-wired into `orchestrator-agent`. See `.claude/CLAUDE.md`'s "Known scope boundary" section.

Also decided: no new automated validation layer for specialist outputs. Human review at the existing gates remains the validation mechanism; `validation-review` stays optional/on-demand exactly as before (used before Gate 4 and via `/review`) — token-efficient, no new agents added.

## SD-008 — Re-sequenced the discovery pipeline: PRD publishes first, stories gate estimation, test strategy runs last, stories go to Jira

On review, the pipeline's actual dependency graph didn't match what was documented or built: `estimation-cost-agent` and `risk-compliance-agent` ran before `user-story-analyst-agent` even though nothing in their contracts required that order; `test-strategy-agent` was dispatched "in parallel with PRD assembly" even though its own contract requires the feature spec, user stories, architecture, UI/UX spec, and risk register to already exist (none of which existed at that point under the old ordering); and the PRD's Confluence publish was framed as an "optional early" side gate rather than its normal publish point.

Re-sequenced to (see `.claude/agents/orchestrator-agent.md` and `.claude/skills/product-discovery/SKILL.md` §2 for the authoritative version):

1. `prd-agent` (flagging research needs to the orchestrator, never dispatching itself; kept deliberately narrow/token-efficient) → **Gate 1** → PRD published to Confluence as its normal next step.
2. `feature-analyst-agent` + `solution-architect-agent` in parallel (both need only the PRD), then `uiux-designer-agent` once the feature spec exists (its contract requires it) → **Gate 2** (merged review of all three) → each publishable to Confluence individually.
3. `user-story-analyst-agent`, given the approved PRD, feature spec, architecture, and UI/UX spec (the last two are extra context handed over by the orchestrator, not part of that agent's own documented contract — **that agent's file was not modified**, per explicit instruction) → **Gate 3** (includes confirming each story's proposed Jira issue type) → stories published to **Jira**, not Confluence.
4. `estimation-cost-agent` (now takes `user-stories.md` as an explicit additional input — this agent's file *was* edited, per explicit instruction, to use story detail for more grounded per-feature effort estimates), then `risk-compliance-agent` (runs after estimation because its existing contract already required the estimate — this ordering was unchanged, just moved later) → **Gate 4** → each publishable to Confluence individually.
5. `test-strategy-agent` last — every input its contract lists now actually exists → **Gate 5** → publishable to Confluence.
6. Validation → final PRD assembly (traceability matrix now includes each story's Jira issue key/URL) → **Gate 6** (`APPROVE_AND_PUBLISH`) → **Gate 7** (Confluence publish of the final package).

Also decided: every individual Confluence page or Jira issue write requires its own explicit confirmation at write time, in addition to (not instead of) the content-review gate before it — a batch's review gate authorizes attempting the publish, it is never itself the publish confirmation. Added a `jira:` block to `config/project.yaml` (mirroring the `confluence:` block: `enabled`, `site`, `project_key`, `issue_type_mapping`) since story publication needs a target project the same way Confluence publication needs a space/parent page.

## SD-009 — Per-project Confluence folders, resolved at a new Gate 0b, plus a fixed document-naming convention

Previously every workflow published under one blanket `PRD` folder directly beneath `confluence.parent_page`, with pages named `<Section> — WF-<id>` — there was no concept of "this workflow belongs to project X" distinct from "this workflow has this ID," so two workflows for the same product over time (e.g. an initial discovery pass and a later amendment) had no guaranteed shared home, and a genuinely new product could collide into the same folder as an old one.

Added, per explicit direction:

- **Gate 0b — Project Identification**, the very first gate, before the workflow ID is even minted: the orchestrator asks whether this is a **new project** or a **continuation of an existing one**. For a new project, it asks the human for the Confluence folder name (never derives or guesses it) and creates that folder (search-before-create, to catch an accidental duplicate). For a continuation, it resolves the existing folder — first from the new `projects` registry in `workflow/status.json` (§1a), falling back to a live Confluence search under `confluence.parent_page` if the registry doesn't have it yet (and backfilling the registry when found).
- **`workflow/status.json`'s `projects` map** (§1a): keyed by project slug, holding the project name, Confluence folder ID/URL, creation timestamp, and the list of workflow IDs that belong to it. Every workflow object gained a `projectSlug` field pointing into it.
- **Fixed naming convention**: every published page is titled `<Document Type> - <Project Name>` — `PRD`, `Feature Specification`, `Solution Architecture`, `Design Document` (the UI/UX spec), `Estimate and Cost`, `Risk Register`, `Test Strategy`, and the Architecture Suite's `Solution Architecture Overview` / `Security Architecture` / `Technology Stack` — replacing the old workflow-ID-prefixed titles. This is what makes search-before-create meaningful across a project's whole lifetime, not just within one workflow.
- The final PRD package (Gate 7) no longer creates a separate wrapper page — it **updates the existing `PRD - <Project Name>` page in place** (created back at Gate 1) to add the Executive Summary, Traceability Matrix, and Decision Log; the other documents (Feature Specification, Solution Architecture, etc.) stay their own already-published pages, referenced by link rather than duplicated.
- `confluence-publish`'s `ParentPage` input is now **required** (previously optional, defaulting to `confluence.parent_page`) — every caller must resolve and pass the project folder explicitly; the skill refuses rather than falling back to publishing under the space root.

See `.claude/agents/orchestrator-agent.md` ("Project identification and publish destinations", "Confluence page naming convention") and `.claude/skills/product-discovery/SKILL.md` §1a for the authoritative procedure.

## SD-010 — Jira destination for user stories also confirmed at Gate 0b, never trusted from config alone

SD-009 resolved *where documents go* (the Confluence folder) but left Jira story publication resolving its target silently from `config/project.yaml`'s `jira.project_key` — the orchestrator would read it and act, with no explicit human confirmation that this was the intended destination for *this* workflow. Per explicit direction, this is no longer good enough: creating issues in the wrong Jira project is exactly the kind of mistake that's expensive to notice and undo.

Extended Gate 0b to resolve **and require explicit human confirmation of** the Jira destination alongside the Confluence folder:

- `jira.project_key` in `config/project.yaml`, if set, is now only ever offered as a **suggested default** — the orchestrator still calls `getVisibleJiraProjects` and requires the human to explicitly confirm it (or name a different project) before it's used for this workflow. It is never silently trusted, whether it comes from config or from a prior workflow's recorded choice.
- The confirmed project (key + name) is recorded per-project in `workflow/status.json`'s `projects` registry (`jiraProjectKey`, `jiraProjectName`, `jiraProjectConfirmedAt`), mirroring the Confluence folder fields — but on a **continuation** workflow, a recorded value is re-verified (`getVisibleJiraProjects`) and re-confirmed with the human, not silently reused, since a project's Jira target is exactly the kind of thing worth double-checking each time rather than assuming still holds.
- This destination confirmation is deliberately separate from, and happens before, the per-story create/update confirmation already required at Gate 3 (`orchestrator-agent.md`'s "Publishing user stories to Jira" step 5) — approving *where* stories go and approving *which specific stories* go there are two different decisions, and neither substitutes for the other. Step 5 now also calls out the destination project on its own line rather than burying it in a table column, as a final visible check immediately before the write.

No changes to `user-story-analyst-agent.md` (still out of scope for edits) or to the Jira write mechanics themselves (search-before-create, issue-type mapping) — this only tightens *which project* those mechanics are allowed to point at, and how confidently that's known before Gate 3 ever runs.

See `.claude/agents/orchestrator-agent.md` ("Project identification and publish destinations", "Publishing user stories to Jira") and `.claude/skills/product-discovery/SKILL.md` §1a for the authoritative procedure.

## SD-011 — Folded the architecture-suite/HLD/LLD bridge into orchestrator-agent; deleted its publish helpers

The merge in SD-010's neighborhood (see the merge commit) restored `solution-architecture-suite-orchestrator-agent.md` as a second orchestrator, because a parallel branch had substantially extended it (HLD, LLD, independent validation, development handoff) with real executed history. Per explicit direction after that merge, folded it into `orchestrator-agent` instead of leaving it as a second orchestrator — the same treatment the original consolidation gave the 3-document version of this workflow before the merge reintroduced it.

- Deleted `solution-architecture-suite-orchestrator-agent.md`; its full procedure (suite in parallel → HLD → LLD → validation → Architecture/HLD/LLD Approval gate → development handoff → optional 5-page Confluence publish) is now `orchestrator-agent.md`'s "Architecture Suite / HLD / LLD workflow" section, reusing the same project-folder/naming-convention machinery as the discovery pipeline.
- Deleted `solution-architecture-publish-agent.md` and `solution-architecture-publish-resume-agent.md` (direct-Confluence-write day-2/recovery helpers) and the `/architecture-publish` command that dispatched the resume agent — their entire reason for existing was working around gaps in the old sub-orchestrator's publish step. `orchestrator-agent` closes those gaps directly: a resume-safety check (read each document's `Status`/`Human approval status` before regenerating) replaces the resume agent, and `confluence-publish`'s existing search-before-create replaces the publish agent's existence-check. This also removes the last agent outside `orchestrator-agent` with direct Confluence MCP write access.
- `/generate-architecture` is a thin dispatcher again, routing through `product-discovery/SKILL.md` §7b to `orchestrator-agent`, matching every other command.
- `dev-orchestrator-agent.md`'s one reference to the old sub-orchestrator (where to route missing/stale design evidence) now points at `orchestrator-agent`.
- **Explicitly not folded in this pass**: `dev-orchestrator-agent` (development, via `/develop`) stays a separate orchestrator — development is a distinct, larger surface, and the call was to consolidate the architecture bridge first. `.claude/CLAUDE.md`'s "Known scope boundary" section now describes two orchestrators, not three, and states this as an open follow-up rather than settled.

See `.claude/agents/orchestrator-agent.md`'s "Architecture Suite / HLD / LLD workflow" and "Scope boundary" sections, and `.claude/skills/product-discovery/SKILL.md` §7b, for the authoritative procedure.

---

## Known limitations

- Orchestrator-to-specialist dispatch assumes this session's Agent/Task tooling can invoke the named subagents from within a skill/command context. If a given Claude Code installation doesn't support that, the top-level assistant session must perform the dispatch itself following the same skill logic (see the environment note in `.claude/agents/orchestrator-agent.md`).
- No end-to-end demo workflow has been run yet (no `WF-2026-0xx` exists in `workflow/status.json`) — the system has been built and the Confluence connection verified, but nothing has been published, and no research/estimate/risk output has been generated or reviewed by a human yet.
- Token/cost metrics are not exposed to agents in this environment, so `workflow/metrics.json` only tracks timestamps, durations, and status counts, per spec §20 ("do not invent token/cost numbers").

## Human decisions still required before a real (non-demo) workflow can publish

- `confluence.space` and `confluence.parent_page` are set (see SD-004), but `create_if_missing` / `allow_updates` are still `false` — decide whether to turn them on for this project, or leave them `false` until reviewed further.
- The demo project (Ingredient Demand Forecasting Assistant) has no Confluence folder created/registered yet under the new per-project model (SD-009) — its first real `/product-plan` run will hit Gate 0b and need a human to actually answer new-vs-continuation and confirm a folder name.
- `jira.enabled` is currently `false` and `jira.project_key` is blank in `config/project.yaml` — Jira story publication stays unavailable until `jira.enabled: true` at minimum; `project_key` is optional even then (Gate 0b will ask directly if it's unset, per SD-010), but setting a sensible default avoids re-typing the same key on every workflow's confirmation prompt.
