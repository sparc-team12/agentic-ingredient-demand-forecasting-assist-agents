---
name: validation-review
description: Lightweight, on-demand validation pass over product-discovery artifacts across four dimensions — consistency, completeness, feasibility, quality/security. Produces findings only, never edits an already human-approved artifact. Invoked standalone by /review and by the product-discovery skill before Gate 4 (Final PRD Approval). Does not stand up a permanent reviewer-agent hierarchy — it's a short-lived pass performed by whichever session invokes it.
---

# Validation & Review

Spec source: `CLAUDE_PRODUCT_DISCOVERY_ORCHESTRATOR_SETUP.md` §9. This skill exists so the four validation dimensions have one canonical checklist, reusable from `/review` (ad hoc, any time) and from `.claude/skills/product-discovery/SKILL.md` (mandatory, right before Gate 4).

## Input

- A workflow ID — read `workflow/status.json` for that workflow and load whichever of the following artifacts currently exist (do not fail if some are missing; report the gap instead, since `/review` can legitimately be run mid-workflow):
  - `artifacts/prd/prd-<slug>.md` (the Gate-1-approved PRD — source of `REQ-` ids)
  - `artifacts/research/requirements-baseline.md` (supporting research context)
  - `artifacts/features/feature-specification.md`
  - `artifacts/stories/user-stories.md`
  - `artifacts/architecture/solution-architecture.md`
  - `artifacts/design/ui-ux-specification.md`
  - `artifacts/estimation/estimation-cost-analysis.md`
  - `artifacts/risk/risk-register.md`
  - `artifacts/test-strategy/test-strategy.md`
  - `artifacts/architecture/solution-architecture-overview.md` (narrative Confluence-page draft from `solution-architecture-overview-agent`)
  - `artifacts/architecture/security-architecture.md` (from `solution-security-architecture-agent`)
  - `artifacts/architecture/tech-stack.md` (from `solution-tech-stack-agent`)

## Checklist

### Consistency
- Feature vs. user-story alignment — every `FEAT-XXX` has at least one story, every story's `Traces to` resolves to a real feature ID.
- Architecture vs. feature requirements — every `ARCH-XXX` traces to a real feature/requirement; no feature requiring persistence/integration/auth left unaddressed by any `ARCH-XXX`.
- Solution Architecture Overview / Security Architecture / Tech Stack vs. `ARCH-XXX` — every component/technology named in these three narrative pages traces to an actual `ARCH-XXX` entry; flag any page that names a technology or component the engineering architecture artifact never mentions.
- Security Architecture vs. risk register — every control in `security-architecture.md` has a corresponding `RISK-XXX` (or is itself the mitigation named on one); every security-relevant `RISK-XXX` has a corresponding control.
- UI/UX vs. user journeys — every `UI-XXX` traces to a real story/feature; no story implying a screen that has no `UI-XXX`.
- Estimate vs. architecture — every `EST-XXX` traces to a real `FEAT-XXX`/`ARCH-XXX`; no architecture component left unestimated.
- Risks vs. architecture/features — spot-check that high-impact architecture assumptions and integration points have a corresponding `RISK-XXX`.
- Risk vs. test strategy — every `RISK-XXX` rated Critical or High has at least one `TS-XXX` mapping it to a required test depth; flag any that don't.

### Completeness
- Missing requirements — anything features/stories imply that isn't a `REQ-` in the PRD (or, failing that, the requirements baseline).
- Missing acceptance criteria — any `US-XXX` without testable acceptance criteria.
- Missing error/empty/loading states — any `UI-XXX` flow without them noted.
- Missing non-functional requirements — features with no NFR coverage at all.
- Missing test coverage — any NFR `REQ-XXX` or Critical/High `RISK-XXX` with no corresponding `TS-XXX`; any `FEAT-XXX`/`US-XXX` the test strategy's coverage approach never mentions.
- Missing dependencies — features/stories/architecture items with no dependency section filled in when one plausibly exists.
- Missing assumptions — architecture/estimation/risk items that read as certain but rest on an unstated assumption.

### Feasibility
- Technical feasibility — architecture choices that conflict with stated constraints.
- Timeline sanity — does the overall estimate range look internally consistent with the stated complexity distribution.
- Cost sanity — does the cost basis match what was actually specified (no invented vendor pricing).
- Integration feasibility — external integrations named in architecture but never surfaced as an open question/risk when their availability is unconfirmed.

### Quality / Security
- Security gaps — authN/authZ, data-at-rest/in-transit, and API boundary items from architecture that have no corresponding risk entry.
- Privacy concerns — any personal/sensitive data handling implied by requirements/features with no privacy risk entry.
- Compliance review requirements — any `RISK-XXX` making a compliance claim without `Requires legal/security review: yes` when evidence is thin.
- Every `[SECURITY REVIEW REQUIRED]` marker in `security-architecture.md` — surface each one individually as a High-severity finding; these route through the Architecture Suite human-approval gate (`solution-architecture-suite-orchestrator-agent`), not this checklist alone.
- Testability — acceptance criteria that aren't actually verifiable as written.
- Operational readiness — architecture's observability/availability notes actually cover what the NFRs demand.

## Output contract

Findings only, grouped by dimension, each with: severity (Low/Medium/High), affected artifact ID(s), a one-line description, and which human gate the fix should route through (never apply the fix yourself to an already-approved artifact). If invoked mid-workflow with several artifacts still missing, say so plainly instead of treating gaps as findings against artifacts that were never supposed to exist yet.

Return a short completion summary: finding counts per dimension/severity, and the specific IDs most in need of human attention.

## Hard rules

- Never modify an approved artifact — a finding is a recommendation, not an edit.
- Never assign false precision to a feasibility/cost judgment — say "plausible" / "uncertain" / "contradicts constraint X", not invented confidence percentages.
- Never silently drop a finding because it's inconvenient for the workflow to proceed — surface everything found.
