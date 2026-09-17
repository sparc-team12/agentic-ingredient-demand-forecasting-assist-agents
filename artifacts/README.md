# Artifacts

Every file under this directory is generated output from a specialist agent (see `.claude/agents/`), gated by human approval as described in the root `README.md`. Nothing here is pre-populated with sample content — each subfolder is created on demand by its owning agent the first time it runs, via:

| Folder | Owning agent | Output file |
|---|---|---|
| `prd/` | prd-agent (entry point) | `prd-<slug>.md` — the Gate-1-approved PRD, source of `REQ-` ids |
| `prd/` | product-discovery-orchestrator (`/prd`) | `final-prd.md` — the Gate-4 assembled package |
| `research/` | research-requirements-agent | `requirements-baseline.md`, `open-questions.md` — dispatched by prd-agent as it hits gaps, not run standalone first |
| `features/` | feature-analyst-agent | `feature-specification.md` |
| `stories/` | user-story-analyst-agent | `user-stories.md` |
| `architecture/` | solution-architect-agent | `solution-architecture.md` |
| `design/` | uiux-designer-agent | `ui-ux-specification.md` |
| `estimation/` | estimation-cost-agent | `estimation-cost-analysis.md` |
| `risk/` | risk-compliance-agent | `risk-register.md` |
| `test-strategy/` | test-strategy-agent | `test-strategy.md` — guideline for later test planning/case generation/automation |

Every artifact carries the metadata block (Workflow ID, Agent, Created, Status, Source artifacts, Human approval status) described in `.claude/skills/product-discovery/SKILL.md`. Treat any artifact whose `Human approval status` is not `APPROVED` as a draft — downstream agents must not build on it as if it were final.
