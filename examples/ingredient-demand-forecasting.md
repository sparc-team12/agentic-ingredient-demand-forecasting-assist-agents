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
3. research-requirements-agent runs -> artifacts/research/requirements-baseline.md + open-questions.md
4. Gate 1 (Requirements Approval) appears — respond APPROVE, REQUEST_CHANGES, PROVIDE_CLARIFICATION, or STOP
5. feature-analyst-agent runs, then user-story-analyst-agent / solution-architect-agent / uiux-designer-agent run in parallel
6. Gate 2 (Solution Review) appears
7. estimation-cost-agent runs, then risk-compliance-agent runs
8. Gate 3 (Estimate/Risk Review) appears
9. Validation runs (/review is also available standalone)
10. /prd assembles the final PRD with traceability matrix
11. Gate 4 (Final PRD Approval) — requires the literal response APPROVE_AND_PUBLISH
12. /publish runs Gate 5 (Confluence Publication) — requires explicit per-page confirmation
13. workflow/status.json records the published page IDs/URLs
```

Use `/status <workflow-id>` at any point to see where the workflow stands.
