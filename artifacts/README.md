# Artifacts

Every file under this directory is generated output from a specialist agent (see `.claude/agents/`), gated by human approval as described in the root `README.md`. Nothing here is pre-populated with sample content — each subfolder is created on demand by its owning agent the first time it runs, via:

Before any of these run, the orchestrator resolves this workflow's **project and Confluence folder** (Gate 0b — see root `README.md` §11) — every local artifact below still lives in the paths listed here regardless, but where each one publishes to on Confluence depends on that resolution, titled `<Document Type> - <Project Name>` (e.g. `PRD - <name>`, `Design Document - <name>`).

| Folder | Owning agent | Output file |
|---|---|---|
| `prd/` | prd-agent (entry point) | `prd-<slug>.md` — the Gate-1-approved PRD, source of `REQ-` ids. Published as `PRD - <Project Name>` to Confluence right after Gate 1. |
| `research/` | research-requirements-agent | `requirements-baseline.md`, `open-questions.md` — dispatched by orchestrator-agent whenever prd-agent flags a specific, scoped research gap, not run standalone or speculatively |
| `features/` | feature-analyst-agent | `feature-specification.md` — dispatched in parallel with `architecture/`, right after Gate 1 |
| `architecture/` | solution-architect-agent | `solution-architecture.md` — dispatched in parallel with `features/`, right after Gate 1 |
| `architecture/` | architecture-suite agents, coordinated by `orchestrator-agent` (`/generate-architecture`, a separate workflow from its discovery-pipeline Gates 1-7) | `solution-architecture-overview.md`, `security-architecture.md`, `tech-stack.md`, `high-level-design.md`, `low-level-design.md`, and `architecture-validation.json` |
| `design/` | uiux-designer-agent | `ui-ux-specification.md` — dispatched once `features/feature-specification.md` exists (its contract requires the feature breakdown) |
| `stories/` | user-story-analyst-agent | `user-stories.md` — dispatched after Gate 2, given the approved PRD, feature spec, architecture, and UI/UX spec; published to **Jira**, not Confluence, after Gate 3 |
| `estimation/` | estimation-cost-agent | `estimation-cost-analysis.md` — dispatched after Gate 3, and takes `stories/user-stories.md` as an input alongside the PRD/features/architecture/UI-UX |
| `risk/` | risk-compliance-agent | `risk-register.md` — dispatched after estimation-cost-agent completes (its contract requires the estimate) |
| `test-strategy/` | test-strategy-agent | `test-strategy.md` — dispatched last, after Gate 4, once feature spec/stories/architecture/UI-UX/risk register all exist; guideline for later test planning/case generation/automation |
| `prd/` | orchestrator-agent (`/prd`) | `final-prd.md` — the Gate-5-onward assembled package, requiring Gate 6's literal `APPROVE_AND_PUBLISH` before Gate 7 publishes it |
| `development/<work-item-id>/` | dev-orchestrator-agent (`/develop`, a separately-gated pipeline — see `.claude/CLAUDE.md`'s "Known scope boundary") + development specialists | requirements validation, implementation plan, tech-lead review, implementation evidence, unit-test report, code review, final verification, and `qa-handoff.md` |

Every artifact carries the metadata block (Workflow ID, Agent, Created, Status, Source artifacts, Human approval status) described in `.claude/skills/product-discovery/SKILL.md`. Treat any artifact whose `Human approval status` is not `APPROVED` as a draft — downstream agents must not build on it as if it were final.

Development artifacts use the schemas in `.claude/agents/dev-orchestrator-agent.md`. They are linked by `work_item_id` and plan checksum rather than the discovery metadata block. Do not create legacy root-level files such as `01-jira.md` or `07-code-verification.json` for new work.
