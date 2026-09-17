# Demo input — Ingredient Demand Forecasting Assistant

> This is a demo/example input for exercising the product discovery workflow end-to-end. It is illustrative, not a real approved business requirement — treat everything the orchestrator produces from it as draft output for a walkthrough, subject to the same human gates as any real workflow.

## Product/problem statement

Build an agentic assistant that helps a multi-location food-service operator (restaurants/kitchens) forecast ingredient demand and reduce waste and stockouts. The assistant should:

- Ingest historical ingredient usage/purchase data and menu/recipe data per location.
- Account for seasonality, day-of-week patterns, local events, and promotions.
- Produce short-horizon (daily/weekly) demand forecasts per ingredient per location.
- Recommend purchase-order quantities to kitchen/procurement staff.
- Flag anomalies (e.g., unexpected demand spikes/drops, supplier lead-time risk).
- Allow a human (kitchen manager or procurement lead) to review and approve recommendations before any order is placed.

## Known constraints (example)

- Must not auto-place purchase orders without human approval.
- Must work with incomplete/noisy historical data for newly opened locations.
- Should integrate with the operator's existing POS/inventory system (exact system TBD — this is exactly the kind of item the Research & Requirements agent should flag as an open question, not assume).

## How to run the demo

```text
1. Start Claude Code in this repository.
2. /product-plan examples/ingredient-demand-forecasting.md
3. Gate 0b (Project Identification) appears — say new or continuation; if new, give the orchestrator the Confluence folder name (it never guesses one), which it creates under confluence.parent_page; separately, it also asks you to confirm which Jira project user stories should be created in (offering config/project.yaml's jira.project_key as a default only if set, never assuming it) — both get recorded in workflow/status.json's projects registry
4. prd-agent interviews you; if it hits a gap it can't resolve from your answers, it flags it to the orchestrator, which runs research-requirements-agent narrowly (-> artifacts/research/requirements-baseline.md + open-questions.md) and hands the result back
5. Gate 1 (Requirements Approval) appears — respond APPROVE, REQUEST_CHANGES, PROVIDE_CLARIFICATION, or STOP; approval also publishes "PRD - <Project Name>" to Confluence, into this project's folder (own confirmation)
6. feature-analyst-agent and solution-architect-agent run in parallel, then uiux-designer-agent runs once the feature spec exists
7. Gate 2 (Feature/Architecture/UI-UX Review) appears; approving offers to publish each of the three to Confluence individually, into the same project folder, titled "Feature Specification - <Project Name>" / "Solution Architecture - <Project Name>" / "Design Document - <Project Name>"
8. user-story-analyst-agent runs, given the approved PRD, feature spec, architecture, and UI/UX spec
9. Gate 3 (User Stories Review) appears, including the proposed US-XXX -> Jira issue-type mapping; approving publishes the stories to Jira (not Confluence)
10. estimation-cost-agent runs (using the user stories as input too), then risk-compliance-agent runs
11. Gate 4 (Estimate/Risk Review) appears; approving offers to publish "Estimate and Cost - <Project Name>" and "Risk Register - <Project Name>" to Confluence individually
12. test-strategy-agent runs last (PRD + feature spec + stories + architecture + UI/UX spec + risk register all exist by now)
13. Gate 5 (Test Strategy Review) appears; approving offers to publish "Test Strategy - <Project Name>" to Confluence
14. Validation runs (/review is also available standalone)
15. /prd assembles the final PRD with traceability matrix (including each story's Jira link)
16. Gate 6 (Final PRD Approval) — requires the literal response APPROVE_AND_PUBLISH
17. /publish runs Gate 7 (Confluence Publication) — updates "PRD - <Project Name>" in place with the full package rather than creating a new page — requires explicit per-page confirmation
18. workflow/status.json records the published Confluence page IDs/URLs and Jira issue keys/URLs
```

Use `/status <workflow-id>` at any point to see where the workflow stands.
