# PRD: Agentic Ingredient Demand Forecasting Assistant

**Version:** 1.0 | **Status:** Confirmed | **Last Updated:** 2026-09-17

## Problem Statement

Kitchen managers at restaurants and hotels order ingredients by gut feel — there is no forecasting tool today. This causes stockouts on fast-moving ingredients and spoilage waste on perishables, with no visibility into which risk is actually worth acting on (i.e., its waste cost) or when to reorder given each supplier's lead time.

## Goals

- The kitchen manager trusts and acts on the flags the system produces. (Qualitative for v1 — no numeric waste/stockout reduction target is set; see OQ-2.)

## Non-Goals

- Real POS or supplier-catalogue ingestion, including native pack sizes and unit conversion (v1 seed data is synthetic and pre-normalized to a single base unit per ingredient).
- Multi-kitchen / multi-property support or data isolation.
- User accounts or authentication of any kind.
- Ongoing daily sales entry or any write path for new sales records after the initial seed load.
- Formal accessibility conformance (WCAG target, audit, screen-reader or keyboard-navigation testing).
- Per-user LLM quotas, spend dashboards, token metering, model fallback chains, or streaming responses.
- Compliance controls of any kind. Note only, not specced: a production deployment ingesting real POS data would carry the operator's existing obligations for transaction and staffing data, and supplier pricing is typically commercially confidential.

## Target Users

- **kitchen-manager** — the person who makes the reorder call for one kitchen: reviews the dashboard, asks the chat agent why an ingredient is flagged, runs what-if scenarios, and sends the drafted purchase order to the supplier.

## Requirements

### Must Have (v1)

This list is a ceiling for v1, not a floor — nothing here is aspirational and nothing outside it is implied "if time permits."

- [ ] **REQ-001** — System generates 12 weeks of synthetic dish-level sales history at seed time; no path exists to import real historical sales data.
- [ ] **REQ-002** — The generated seed history includes a weekend demand spike for at least one dish.
- [ ] **REQ-003** — The generated seed history includes at least one perishable ingredient that reaches its spoilage condition within the forecast horizon.
- [ ] **REQ-004** — The generated seed history includes at least one fast-moving ingredient that reaches a stockout condition within the forecast horizon.
- [ ] **REQ-005** — The system stores a recipe/BOM mapping of 15–20 dishes to their component ingredients and quantities.
- [ ] **REQ-006** — The system stores a supplier list of 3–5 suppliers, each with a lead time and a per-unit cost.
- [ ] **REQ-007** — Each ingredient record stores unit, perishable flag, shelf_life_days, unit_cost, and supplier_id, all supplied at seed time; the system never infers or defaults these values.
- [ ] **REQ-008** — Recipe ingredient quantities and the corresponding supplier's per-unit cost for a given ingredient are expressed in the same base unit.
- [ ] **REQ-009** — The system uses a fixed, pinned "current date" constant, not the system clock, to separate historical records from the forward-looking forecast horizon.
- [ ] **REQ-010** — The forecasting agent computes a per-ingredient, per-weekday baseline demand as the median of same-weekday historical observations, using at least six same-weekday samples.
- [ ] **REQ-011** — The forecasting agent computes a trend adjustment by comparing the trailing 2-week mean of demand against the preceding 4-week mean.
- [ ] **REQ-012** — The forecasting agent rolls up dish-level demand forecasts into ingredient-level projected consumption using the recipe/BOM mapping.
- [ ] **REQ-013** — Forecast output is deterministic: re-running the forecast against unchanged seed data produces identical projected values every time.
- [ ] **REQ-014** — The risk agent flags stockout risk for an ingredient when projected consumption will exhaust on-hand stock before the next feasible reorder can arrive.
- [ ] **REQ-015** — The risk agent flags spoilage risk for a perishable ingredient when its projected time-to-consumption exceeds its shelf_life_days.
- [ ] **REQ-016** — Each spoilage risk flag carries an estimated waste cost, computed from the projected unconsumed quantity and the ingredient's unit_cost.
- [ ] **REQ-017** — The reorder-timing logic computes an "order by" date for each flagged ingredient, factoring in that ingredient's supplier lead time.
- [ ] **REQ-018** — The chat agent answers a "why is [ingredient] flagged" question with the specific forecast values and risk basis behind that flag.
- [ ] **REQ-019** — The chat agent accepts a what-if input that adds projected demand for a specified dish on a specified date.
- [ ] **REQ-020** — Submitting a what-if scenario recomputes the risk table, waste-cost estimates, and order-by dates against an overlay, without modifying the underlying seed data.
- [ ] **REQ-021** — What-if overlay state is held in memory only and resets when the page is reloaded.
- [ ] **REQ-022** — The draft-PO agent generates a ready-to-send, text/email-style purchase-order line for a flagged ingredient, addressed to that ingredient's supplier, including item, quantity, and order-by date.
- [ ] **REQ-023** — The dashboard lists all currently at-risk ingredients across the menu together with their waste-cost estimates.
- [ ] **REQ-024** — The dashboard conveys risk severity using a label or icon in addition to color, so severity remains distinguishable when color is not perceptible (e.g., under projector or overhead-lit conditions). This is functional, not an accessibility nice-to-have — severity is the dashboard's primary signal.

### Should Have

None. The client explicitly scoped v1 as a fixed ceiling for a hackathon deadline; no phase-2 or "if time permits" items are carried inside this document. Deferred capabilities are recorded under Non-Goals above without requirement ids.

### Could Have (later)

None, for the same reason as above.

### Non-Functional

- [ ] **REQ-025** — All demand forecasting, risk scoring, and waste-cost computation is performed by deterministic Python logic that makes no LLM calls.
- [ ] **REQ-026** — The chat explanation, what-if intent parsing, and purchase-order draft text are generated by Claude Sonnet in a single-turn, tool-use pattern.
- [ ] **REQ-027** — Chat conversation history is capped at the last 6 turns; older turns are dropped, not summarized.
- [ ] **REQ-028** — The LLM is invoked only on explicit user action (a chat question, a what-if submission, or a PO draft request) — never on page load, polling, or a background schedule.
- [ ] **REQ-029** — A response cache keyed on question text is checked before any LLM call; a cache hit returns the cached answer without calling the API.
- [ ] **REQ-030** — Dashboard text remains legible under typical projector/overhead-lighting conditions — no small or low-contrast type on primary content.
- [ ] **REQ-031** — The application requires no login or authentication in v1.
- [ ] **REQ-032** — The application supports exactly one kitchen (single tenant); no multi-property data isolation is provided.
- [ ] **REQ-033** — Seed data is loaded once at initialization; no UI or API path exists to add or edit sales records afterward.
- [ ] **REQ-034** — The application's supported browser for v1 is the current version of Chrome; no other browser support is guaranteed.

## Constraints

- Hackathon deadline, hard, no slip: build window is approximately 24–36 hours from spec to demo. An incomplete build at the deadline scores as incomplete.
- Explicit build phase: code freeze at roughly 70% of elapsed build time; remaining time is reserved for demo rehearsal and a recorded fallback walkthrough of the complete flow.
- No infrastructure budget: local SQLite, local Streamlit, no hosting. Only cost incurred is Anthropic API usage at the volume described under Non-Functional.
- Client-named technology constraints, recorded as stated (not expanded into architecture, which is a later agent's job): Python for the deterministic forecasting/risk/waste-cost layer, SQLite for storage, Streamlit for the web app, Claude Sonnet for the LLM layer.
- LLM expected volume is low: invoked only on explicit user action, estimated ceiling of a few hundred requests for the demo period. No spend cap is enforced in v1.

## Success Metrics

- v1 success is defined qualitatively: the kitchen manager reviews the dashboard/chat output during the demo walkthrough and acts on at least one flag (e.g., accepts a reorder timing suggestion or sends a drafted PO). No numeric waste-reduction or stockout-reduction target is set for v1 (see OQ-2).

## Glossary

- **kitchen-manager** — the persona who reviews flags and makes the reorder call; the only user role in v1.
- **dish** — a menu item with a fixed recipe.
- **ingredient** — a raw stock item consumed by one or more dishes, tracked at the base-unit level.
- **recipe/BOM mapping** — the bill-of-materials linking each dish to its component ingredients and the quantity of each required per serving.
- **base unit** — the single unit of measure (e.g., kg, L, each) in which a given ingredient's recipe quantity and supplier unit_cost are both expressed; v1 has no unit conversion.
- **shelf_life_days** — the number of days after receipt that a perishable ingredient remains usable.
- **perishable** — a boolean ingredient attribute indicating it is subject to a spoilage risk check.
- **stockout risk** — the flag raised when projected consumption of an ingredient will exhaust on-hand stock before the next feasible reorder can arrive.
- **spoilage risk** — the flag raised when a perishable ingredient's projected time-to-consumption exceeds its shelf_life_days.
- **waste cost** — the estimated monetary cost attached to a spoilage risk flag, computed from projected unconsumed quantity and unit_cost.
- **lead time** — the number of days a supplier takes to deliver an ingredient after an order is placed.
- **order-by date** — the latest date an order can be placed for a flagged ingredient and still arrive before it is needed, computed from the supplier's lead time.
- **what-if scenario** — a user-supplied hypothetical (e.g., adding a dish on a date) used to recompute risk, waste-cost, and order-by dates against an in-memory overlay, without altering the seed/history data.
- **overlay** — the temporary, in-memory recomputation state produced by a what-if scenario; it resets on reload and is never persisted.
- **forecast horizon** — the forward-looking window, starting at the pinned current-date constant, over which demand and risk are projected.
- **current-date constant** — the fixed, pinned date used in place of the system clock to separate historical seed records from the forecast horizon, making every run deterministic.
- **draft purchase order (draft PO)** — the ready-to-send, text/email-style order line generated for a flagged ingredient's supplier; not an integration with a procurement system.
- **risk severity** — the dashboard's primary signal distinguishing how urgent a flag is; conveyed via label/icon in addition to color.

## Open Questions

- **OQ-1** — No response-time target has been set for dashboard load or chat/what-if answers; the client declined to set one rather than have a number invented. Blocks: no currently numbered requirement, but blocks adding any future latency/performance requirement until a target is given. Owner: client.
- **OQ-2** — The current waste/stockout cost baseline is unquantified; the client declined to estimate one. Blocks: any future measurable-success requirement or numeric goal (see Success Metrics). Owner: client.

## Change Log

| Version | Date | Added | Changed | Retired |
|---|---|---|---|---|
| 1.0 | 2026-09-17 | REQ-001–REQ-034 | — | — |
