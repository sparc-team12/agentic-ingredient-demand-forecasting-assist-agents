# PRD: Agentic Ingredient Demand Forecasting Assistant

**Version:** 1.1 | **Status:** Approved | **Last Updated:** 2026-09-17

> Synced from Confluence page "PRD - Agentic Ingredient Demand Forecasting Assistant" (id 5883461703, space `~712020c78d0510dbf248218881c00989970857`), resolved via `confluence-doc-resolver` Mode `keyword_status` (keyword "PRD", required status Approved). This supersedes the earlier v1.0 content (Confluence page id 5884510209, `Status: Confirmed`), which that page itself states is pending deletion as a duplicate.

## Problem Statement

Food cost is one of the largest controllable line items in a restaurant or hotel kitchen, and it leaks two symmetrical ways: ingredients bought too late cause stockouts and lost covers; ingredients bought too early spoil before use. The kitchen manager currently absorbs both risks through experience — memory of last week's covers, a walk through the walk-in, a general sense of supplier lead times. This holds until the menu changes, a special is added, or a supplier's lead time shifts, at which point the error surfaces as an 86'd dish or a bin of discarded produce. Existing inventory tools report stock on hand; they do not project what will be needed, and they attach no cost to the decision to wait. The gap this product fills is the step between knowing the stock level and knowing what to do about it.

## Goals

- A kitchen manager can answer, in under a minute and without a spreadsheet: what am I about to run out of and by when must I order it; what am I about to throw away and what is it worth; why is this item flagged; what happens if I change the menu.
- Every spoilage warning carries a rupee figure so the manager can tell a small problem from a large one.
- Every warning is interrogable in plain language, and the answer is consistent with the figure shown.
- A menu change (special, banquet booking) can be tested against the risk picture before an order is placed.
- Success is defined by the client as: the manager trusts the system's order-by dates enough to act on them without re-checking by hand. The product fails if it produces a list of warnings the manager still has to triage themselves.

## Non-Goals

- Procurement integration — no connection to any supplier portal, EDI channel or ordering system. Orders are drafted as text only.
- Live POS integration — no connection to Toast, Square or any till system. Sales history is a fixed, supplied dataset.
- Ongoing data entry — no screens for logging daily sales, receiving deliveries, or recording stock counts.
- Unit conversion — units are guaranteed consistent as supplied; the system does not convert between them.
- Scenario persistence — what-if results are transient; no saving, naming or comparing of scenarios.
- Accounts and permissions — single user, no login, no roles.
- Multi-site operation — one kitchen only.
- Mobile-specific interface — desktop or tablet browser is sufficient.
- Compliance controls — no personal, customer or payment data is involved.

## Target Users

- **kitchen-manager** — kitchen manager or head chef (primary user): reviews the tool two or three times a week, typically before placing orders. Comfortable with numbers, not with spreadsheets or dashboards requiring configuration. Needs a fast, decision-driven answer, not a monitoring screen.
- **fb-manager** — F&B manager or owner (secondary user): interested in the aggregate — total waste exposure across the menu and which ingredients recur as problems. Uses the same dashboard, reads the top of it rather than the detail.

## Input Data

All data below is supplied to the system as a fixed dataset for this build; the system does not source, infer or estimate any of it.

- **Sales history** — Daily units sold per dish, 12 weeks. Sufficient for day-of-week patterns and a recent trend.
- **Menu** — 15–20 active dishes, stable over the period covered by the sales history.
- **Recipes** — Ingredient quantities per serving, for every dish. 30–40 distinct ingredients across the menu.
- **Ingredients** — Unit, unit cost, perishable flag, and shelf life in days (spoilage risk) per ingredient. Shelf life is given, never inferred.
- **Current stock** — Quantity on hand and use-by date, per ingredient. The basis for spoilage assessment.
- **Suppliers** — 3–5 suppliers, each with a lead time in days. Each ingredient maps to exactly one supplier.

Unit consistency is guaranteed by the client: for any given ingredient, recipe quantities and supplier pricing are expressed in the same unit — no conversion is required.

## Requirements

### Must Have (v1)

**Ingredient demand projection**

- [ ] **REQ-001** — The system projects demand for every ingredient over a forward horizon of at least 14 days.
- [ ] **REQ-002** — Demand projections reflect day-of-week patterns (e.g., a Saturday is projected from Saturday history, not a flat daily average).
- [ ] **REQ-003** — Demand projections weight recent trend movement more heavily than older history, rather than treating the full 12-week history as equally current.
- [ ] **REQ-004** — Ingredient demand projection is computed by mapping each dish's projected demand through its recipe and summing across every dish containing that ingredient.

**Stockout risk**

- [ ] **REQ-005** — The system determines, for each ingredient, whether projected consumption will exhaust current stock within the forward horizon.
- [ ] **REQ-006** — For each ingredient flagged at stockout risk, the system computes the date stock is expected to run out.
- [ ] **REQ-007** — For each ingredient flagged at stockout risk, the system computes an order-by date, earlier than the projected stockout date by the ingredient's supplier lead time plus a safety margin.
- [ ] **REQ-008** — For each ingredient flagged at stockout risk, the system computes a suggested order quantity covering projected consumption across the lead-time gap.
- [ ] **REQ-009** — For each ingredient flagged at stockout risk, the system assigns a severity driven by how soon the order-by date falls.

**Spoilage risk**

- [ ] **REQ-010** — For each perishable ingredient, the system determines whether stock on hand is unlikely to be consumed before its use-by date, given projected consumption.
- [ ] **REQ-011** — For each ingredient flagged at spoilage risk, the system computes an estimated waste cost in INR, equal to the unconsumed quantity valued at unit cost.
- [ ] **REQ-012** — Spoilage warnings whose estimated waste cost falls below a configurable materiality threshold are suppressed from view.

**Explanation on demand (Chat Agent)**

- [ ] **REQ-013** — Any warning shown on the dashboard can be interrogated with a natural-language question posed to the Chat Agent (e.g., "why is this flagged?").
- [ ] **REQ-014** — The explanation for a flagged ingredient names the contributing dishes and each one's relative contribution to the demand driving the flag.
- [ ] **REQ-015** — The explanation for a flagged ingredient states the relevant dates driving the flag.
- [ ] **REQ-016** — The explanation for a stockout-flagged ingredient states the supplier lead time that set its order-by date.

**What-if scenarios (Chat Agent)**

- [ ] **REQ-017** — The manager can pose a hypothetical demand change — a named dish, an additional or altered serving count, and a date or date range — in natural language to the Chat Agent, rather than through numeric form fields.
- [ ] **REQ-018** — Posing a what-if scenario recomputes and surfaces which ingredients newly become at-risk as a result.
- [ ] **REQ-019** — Posing a what-if scenario recomputes and surfaces which order-by dates move as a result.
- [ ] **REQ-020** — Posing a what-if scenario recomputes and surfaces how total waste exposure changes as a result.
- [ ] **REQ-036** — The explanation capability (REQ-013) and the what-if scenario capability (REQ-017) are both accessible through the same Chat Agent interface, not two disconnected inputs.

**Purchase order drafting**

- [ ] **REQ-021** — For any ingredient flagged at stockout risk, the system drafts a purchase order containing the supplier's name, the item, the suggested quantity, and the required delivery date.
- [ ] **REQ-022** — The purchase order draft is presented as editable text that the manager can review and modify before sending through their own channel; it is never sent automatically.

**Risk dashboard**

- [ ] **REQ-023** — A single view lists every at-risk ingredient across the menu, ordered by severity.
- [ ] **REQ-024** — The dashboard shows the risk type (stockout or spoilage) for each listed ingredient.
- [ ] **REQ-025** — The dashboard shows the order-by date for each ingredient with stockout risk.
- [ ] **REQ-026** — The dashboard shows the estimated waste cost for each ingredient with spoilage risk.
- [ ] **REQ-027** — The dashboard shows a single aggregate figure for total waste exposure across the menu.

### Should Have

None identified — the client specified the full requirement set above as required for v1 acceptance, with no should/could tier. The client's own framing (§9 of the intake document) treats this list as a ceiling, not a starting point: under time pressure, the six-step acceptance sequence (see Success Metrics) defines the minimum that must work.

### Could Have (later)

None identified — see note under Should Have.

### Non-Functional

- [ ] **REQ-028** — Given the same input data, the system produces identical figures on every run (deterministic computation).
- [ ] **REQ-029** — Every figure shown to the manager (stockout date, order-by date, order quantity, waste cost, aggregate exposure) is reconstructible as an explicit arithmetic trace back to the underlying input data.
- [ ] **REQ-030** — Any generated explanation or scenario narrative describes figures already computed elsewhere in the system; it must never independently estimate a quantity that is not otherwise computed and shown.
- [ ] **REQ-031** — An explanation returned for a given warning is numerically consistent with the figures shown for that same warning on the dashboard.
- [ ] **REQ-032** — The risk dashboard loads and its risk figures are available in a time materially faster than the response time allowed for a natural-language question (i.e., fast enough to check in passing, not a multi-second wait).
- [ ] **REQ-033** — A natural-language question (explanation or what-if scenario) returns a response within a few seconds.
- [ ] **REQ-034** — Severity on the dashboard is communicated by a text label in addition to colour, so it remains legible on kitchen tablets, under overhead light, and on projected screens where colour distinctions collapse.
- [ ] **REQ-035** — All monetary figures shown to the user (waste cost, aggregate exposure) are denominated in INR.

## Constraints

- **Fixed-deadline build.** This is a fixed-deadline delivery per the client's own requirements document (§9). Scope as written is a ceiling, not a starting point. Where time is short, the six-step acceptance sequence (see Success Metrics) defines what must work; anything not serving those six steps should be cut rather than partially built.
- Supplier lead times are treated as fixed, an accepted simplification — lead-time variability is explicitly not modelled, even though the client notes a late delivery against a tight order-by date is exactly the failure this product exists to prevent.
- The menu is assumed stable across the 12-week period covered by the sales history.
- The projection is expected to be directionally useful, not precise to the gram; value lies in flagging the right ingredients with the right urgency.
- Platform: desktop or tablet browser only.
- Single user, no login, no roles.
- Data is supplied, not sourced — see Input Data for the full itemized breakdown per input. The build does not source, infer or estimate any of it.
- Currency is INR throughout.

## Success Metrics

A reviewer, working only from the interface, can complete the following sequence unaided (client acceptance criteria, §8 of the intake document):

1. Open the dashboard — at-risk ingredients listed by severity, each with risk type, order-by date or waste cost, and a visible total waste exposure figure.
2. Select a flagged perishable ingredient — a rupee waste estimate and the use-by date driving it.
3. Ask why that ingredient is flagged — an answer naming the contributing dishes, the relevant dates, and the supplier lead time, consistent with the figures on screen.
4. Select a flagged fast-moving ingredient — an order-by date earlier than the projected stockout date by at least the supplier's lead time.
5. Pose a menu change in plain language — the risk table updates; at least one ingredient changes state or date as a result.
6. Request a purchase order for a flagged item — a complete draft naming supplier, item, quantity and required date.

Steps 3 and 5 are the ones that distinguish this product from a reorder report, per the client. A vague or inconsistent answer at either step fails acceptance regardless of how the dashboard looks.

Stated qualitative signal of success: the manager acts on order-by dates without re-checking them by hand, rather than treating the dashboard as a list to triage.

## Glossary

- **Ingredient** — a distinct raw material used in one or more dishes; the level at which demand, stock and risk are tracked (not the dish level).
- **Dish** — a menu item composed of ingredients per its recipe.
- **Recipe** — the mapping of ingredient quantities per serving for a given dish.
- **Forward horizon** — the forward-looking window (minimum 14 days) over which demand is projected.
- **Stockout risk** — an ingredient whose projected consumption is expected to exhaust current stock within the forward horizon.
- **Order-by date** — the date by which an order must be placed for a stockout-risk ingredient, computed as the projected stockout date minus the supplier's lead time minus a safety margin.
- **Safety margin** — additional buffer time added to a supplier's lead time when computing an order-by date. Value and configurability not yet defined — see OQ-1.
- **Suggested order quantity** — the quantity recommended to order to cover projected consumption across the lead-time gap.
- **Severity** — the urgency ranking assigned to a risk warning. Exact bands/thresholds not yet defined — see OQ-4, OQ-5.
- **Spoilage risk** — a perishable ingredient's on-hand stock unlikely to be consumed before its use-by date, given projected consumption.
- **Waste cost** — the estimated rupee value of stock expected to spoil, computed as unconsumed quantity × unit cost.
- **Materiality threshold** — the configurable minimum waste cost below which a spoilage warning is suppressed from view. Value and owner not yet defined — see OQ-2.
- **Total waste exposure** — the aggregate rupee figure summing waste cost across spoilage warnings shown on the dashboard.
- **Risk dashboard** — the single view listing every at-risk ingredient, ordered by severity.
- **Chat Agent** — the single conversational interface through which the manager both interrogates warnings in natural language (explanation) and poses what-if scenarios. One surface serves both capabilities; it is not two separate inputs.
- **What-if scenario** — a hypothetical demand change (e.g., a special or banquet booking) posed in natural language, used to preview its effect on the risk picture without committing to it.
- **Purchase order draft** — the editable, ready-to-send text artifact naming a supplier, item, quantity and required delivery date for a stockout-risk ingredient.
- **Lead time** — the number of days a supplier takes to deliver an ingredient after an order is placed.
- **Use-by date** — the date by which a specific batch of stock on hand must be consumed.
- **Shelf life** — the number of days an ingredient remains usable from receipt, provided as input data and never inferred.
- **Perishable ingredient** — an ingredient flagged with a shelf life, subject to spoilage-risk assessment.

## Open Questions

- **OQ-1** — What is the safety margin (in days) added to supplier lead time when computing the order-by date — a fixed value, the same for every ingredient, or configurable per ingredient/supplier? No value or owner is stated in the client's requirements. (Blocks: REQ-007, REQ-009, REQ-019, REQ-021, REQ-025 | Owner: client)
- **OQ-2** — What is the default value and unit (a rupee amount, or a percentage) for the configurable materiality threshold that suppresses spoilage warnings, and who is expected to set or adjust it? (Blocks: REQ-012 | Owner: client)
- **OQ-3** — Does the "total waste exposure" aggregate figure include the value of spoilage warnings suppressed by the materiality threshold, or only the value of warnings actually displayed? (Blocks: REQ-027 | Owner: client)
- **OQ-4** — What are the severity levels (how many bands, what labels) and the day-based thresholds that map "how soon the order-by date falls" onto each severity level for stockout risk? (Blocks: REQ-009, REQ-023, REQ-034 | Owner: client)
- **OQ-5** — What determines severity for a spoilage-flagged ingredient (e.g., proximity to use-by date, or size of the waste cost), and how do stockout severity and spoilage severity rank against each other on the single, combined, severity-ordered dashboard? (Blocks: REQ-023, REQ-026 | Owner: client)

## Change Log

| Version | Date | Added | Changed | Retired |
|---|---|---|---|---|
| 1.0 | 2026-09-17 | REQ-001–REQ-035, OQ-1–OQ-5 | — | — |
| 1.1 | 2026-09-17 | REQ-036 | REQ-013, REQ-017 (name Chat Agent explicitly) | — |

Also in 1.1: added Glossary term "Chat Agent"; added top-level "Input Data" section (itemized breakdown of the six supplied inputs); consolidated the two data/unit-consistency bullets in Constraints into a pointer to Input Data; renamed "Explanation on demand" and "What-if scenarios" subsection headers to "(Chat Agent)" for traceability to the client's own FR-4 label. No ids retired.
