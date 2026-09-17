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

---

## Known limitations

- Orchestrator-to-specialist dispatch assumes this session's Agent/Task tooling can invoke the named subagents from within a skill/command context. If a given Claude Code installation doesn't support that, the top-level assistant session must perform the dispatch itself following the same skill logic (see the environment note in `.claude/agents/product-discovery-orchestrator.md`).
- No end-to-end demo workflow has been run yet (no `WF-2026-0xx` exists in `workflow/status.json`) — the system has been built and the Confluence connection verified, but nothing has been published, and no research/estimate/risk output has been generated or reviewed by a human yet.
- Token/cost metrics are not exposed to agents in this environment, so `workflow/metrics.json` only tracks timestamps, durations, and status counts, per spec §20 ("do not invent token/cost numbers").

## Human decisions still required before a real (non-demo) workflow can publish

- Target Confluence **space** and **parent page** (currently blank in `config/project.yaml`).
- Whether `confluence.create_if_missing` / `confluence.allow_updates` should be turned on for this project, or left `false` until reviewed further.
