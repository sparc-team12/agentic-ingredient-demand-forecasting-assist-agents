# PRD: Ingredient Demand Forecasting Assistant

**Version:** 1.6 | **Status:** Confirmed | **Last Updated:** 2026-09-17

> Synced from Confluence page "PRD - Agentic Ingredient Demand Forecasting Assistant" (id 5883461703, space `~712020c78d0510dbf248218881c00989970857`), resolved via `confluence-doc-resolver` Mode `keyword_status` (keyword "PRD", required status Confirmed/Approved). This supersedes the local v1.1 copy previously synced in this checkout.

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
- Ongoing data entry — no screens for logging daily sales, receiving deliveries, or recording stock counts. (Clarified in v1.2: a one-time initial load of the six Input Data categories is in scope — see REQ-037–REQ-041 and the "Data setup" requirements subsection. This Non-Goal excludes only recurring/day-to-day entry after that initial load.)
- Unit conversion — units are guaranteed consistent as supplied; the system does not convert between them.
- Scenario persistence — what-if results are transient; no saving, naming or comparing of scenarios.
- Additional roles or permission tiers beyond the two named personas — kitchen-manager and fb-manager each authenticate individually with their own email/password (REQ-043, REQ-044); the system adds no further roles, admin tiers, or granular permissions beyond those two personas. The two personas have identical access once authenticated — no restricted or aggregate-only view for fb-manager (resolved OQ-9, v1.6). (This Non-Goal previously read "single user, no login, no roles" in v1.3, then, briefly and incorrectly, "single shared login credential set" in v1.4, then hedged on per-persona access in v1.5 — all superseded by the per-user login requirement and the identical-access resolution.)
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

- **REQ-001** — The system projects demand for every ingredient over a forward horizon of at least 14 days.
- **REQ-002** — Demand projections reflect day-of-week patterns (e.g., a Saturday is projected from Saturday history, not a flat daily average).
- **REQ-003** — Demand projections weight recent trend movement more heavily than older history, rather than treating the full 12-week history as equally current.
- **REQ-004** — Ingredient demand projection is computed by mapping each dish's projected demand through its recipe and summing across every dish containing that ingredient.

**Stockout risk**

- **REQ-005** — The system determines, for each ingredient, whether projected consumption will exhaust current stock within the forward horizon.
- **REQ-006** — For each ingredient flagged at stockout risk, the system computes the date stock is expected to run out.
- **REQ-007** — For each ingredient flagged at stockout risk, the system computes an order-by date, earlier than the projected stockout date by the ingredient's supplier lead time plus a safety margin, where the safety margin is a configurable value looked up per ingredient or per supplier (captured during Ingredients & Suppliers data setup, REQ-039) rather than a single fixed global value.
- **REQ-008** — For each ingredient flagged at stockout risk, the system computes a suggested order quantity covering projected consumption across the lead-time gap.
- **REQ-009** — For each ingredient flagged at stockout risk, the system assigns a severity band — Critical (order-by date ≤2 days away), High (order-by date 3–7 days away), or Low (order-by date more than 7 days away) — driven by how soon the order-by date falls.

**Spoilage risk**

- **REQ-010** — For each perishable ingredient, the system determines whether stock on hand is unlikely to be consumed before its use-by date, given projected consumption.
- **REQ-011** — For each ingredient flagged at spoilage risk, the system computes an estimated waste cost in INR, equal to the unconsumed quantity valued at unit cost.
- **REQ-012** — Spoilage warnings whose estimated waste cost falls below a materiality threshold are suppressed from view. The threshold defaults to ₹500 (INR, consistent with REQ-035) and is user-adjustable by the kitchen manager.
- **REQ-042** — For each ingredient flagged at spoilage risk, the system assigns a severity band — Critical (estimated waste cost ≥ ₹2000), High (₹500–1999), or Low (under ₹500) — driven by the size of the estimated waste cost.

**Explanation on demand (Chat Agent)**

- **REQ-013** — Any warning shown on the dashboard can be interrogated with a natural-language question posed to the Chat Agent (e.g., "why is this flagged?").
- **REQ-014** — The explanation for a flagged ingredient names the contributing dishes and each one's relative contribution to the demand driving the flag.
- **REQ-015** — The explanation for a flagged ingredient states the relevant dates driving the flag.
- **REQ-016** — The explanation for a stockout-flagged ingredient states the supplier lead time that set its order-by date.

**What-if scenarios (Chat Agent)**

- **REQ-017** — The manager can pose a hypothetical demand change — a named dish, an additional or altered serving count, and a date or date range — in natural language to the Chat Agent, rather than through numeric form fields.
- **REQ-018** — Posing a what-if scenario recomputes and surfaces which ingredients newly become at-risk as a result.
- **REQ-019** — Posing a what-if scenario recomputes and surfaces which order-by dates move as a result.
- **REQ-020** — Posing a what-if scenario recomputes and surfaces how total waste exposure changes as a result.
- **REQ-036** — The explanation capability (REQ-013) and the what-if scenario capability (REQ-017) are both accessible through the same Chat Agent interface, not two disconnected inputs.

**Purchase order drafting**

- **REQ-021** — For any ingredient flagged at stockout risk, the system drafts a purchase order containing the supplier's name, the item, the suggested quantity, and the required delivery date.
- **REQ-022** — The purchase order draft is presented as editable text that the manager can review and modify before sending through their own channel; it is never sent automatically.

**Risk dashboard**

- **REQ-023** — A single view lists every at-risk ingredient across the menu — stockout and spoilage interleaved — ordered by severity band first, then within a band by proximity to the order-by date (stockout) or estimated waste cost (spoilage); a Critical spoilage item outranks a High stockout item.
- **REQ-024** — The dashboard shows the risk type (stockout or spoilage) for each listed ingredient.
- **REQ-025** — The dashboard shows the order-by date for each ingredient with stockout risk.
- **REQ-026** — The dashboard shows the estimated waste cost and the assigned severity band (REQ-042) for each ingredient with spoilage risk.
- **REQ-027** — The dashboard shows a single aggregate figure for total waste exposure across the menu, including spoilage warnings suppressed by the materiality threshold (REQ-012).

**Authentication** *(added v1.4, corrected v1.5, resolved v1.6)*

- **REQ-043** — At the start of every session, the system requires the user to authenticate with a valid email and password before the risk dashboard, ingredient detail, Chat Agent, or purchase-order-draft screens become reachable.
- **REQ-044** — Authentication is per-user: kitchen-manager and fb-manager each hold their own distinct email/password credential set; the system does not use a single credential shared across both personas.

**Data setup** *(added v1.2)*

- **REQ-037** — A Data Setup hub screen lists the five data-setup screens and each one's load status, as a single entry point for the one-time initial data load.
- **REQ-038** — A Menu & Recipe Setup screen lets the manager load and view the menu and each dish's recipe.
- **REQ-039** — An Ingredients & Suppliers Setup screen lets the manager load and view ingredient master data and the supplier list, including each ingredient's mapped supplier and a safety-margin value.
- **REQ-040** — A Current Stock Setup screen lets the manager load and view current stock on hand and use-by date per ingredient (snapshot only, not ongoing entry).
- **REQ-041** — A Sales History Import screen lets the manager load and view 12 weeks of daily units-sold history per dish.

### Should Have

None identified — the client specified the full requirement set above as required for v1 acceptance, with no should/could tier.

### Could Have (later)

None identified — see note under Should Have.

### Non-Functional

- **REQ-028** — Given the same input data, the system produces identical figures on every run (deterministic computation).
- **REQ-029** — Every figure shown to the manager is reconstructible as an explicit arithmetic trace back to the underlying input data.
- **REQ-030** — Any generated explanation or scenario narrative describes figures already computed elsewhere; it must never independently estimate an unshown quantity.
- **REQ-031** — An explanation returned for a given warning is numerically consistent with the figures shown for that same warning on the dashboard.
- **REQ-032** — The risk dashboard loads materially faster than the response time allowed for a natural-language question.
- **REQ-033** — A natural-language question (explanation or what-if scenario) returns a response within a few seconds.
- **REQ-034** — Severity on the dashboard is communicated by a text label (Critical, High, or Low) in addition to colour.
- **REQ-035** — All monetary figures shown to the user are denominated in INR.

## Constraints

- **Fixed-deadline build.** Scope as written is a ceiling, not a starting point; the six-step acceptance sequence (Success Metrics) defines what must work under time pressure.
- Supplier lead times are treated as fixed, an accepted simplification.
- The menu is assumed stable across the 12-week period covered by the sales history.
- The projection is expected to be directionally useful, not precise to the gram.
- Platform: desktop or tablet browser only.
- Per-user login for the two named personas (kitchen-manager, fb-manager), each with their own email/password (REQ-043/REQ-044); no additional roles or permission tiers beyond those two personas.
- Data is supplied, not sourced — see Input Data.
- Currency is INR throughout.

## Success Metrics

1. Open the dashboard — at-risk ingredients listed by severity, each with risk type, order-by date or waste cost, and a visible total waste exposure figure.
2. Select a flagged perishable ingredient — a rupee waste estimate and the use-by date driving it.
3. Ask why that ingredient is flagged — an answer naming the contributing dishes, the relevant dates, and the supplier lead time, consistent with the figures on screen.
4. Select a flagged fast-moving ingredient — an order-by date earlier than the projected stockout date by at least the supplier's lead time.
5. Pose a menu change in plain language — the risk table updates; at least one ingredient changes state or date as a result.
6. Request a purchase order for a flagged item — a complete draft naming supplier, item, quantity and required date.

Steps 3 and 5 distinguish this product from a reorder report. Stated qualitative signal of success: the manager acts on order-by dates without re-checking them by hand.

## Glossary

| Term | Definition |
| --- | --- |
| Ingredient | a distinct raw material used in one or more dishes; the level at which demand, stock and risk are tracked. |
| Dish | a menu item composed of ingredients per its recipe. |
| Recipe | the mapping of ingredient quantities per serving for a given dish. |
| Forward horizon | the forward-looking window (minimum 14 days) over which demand is projected. |
| Stockout risk | an ingredient whose projected consumption is expected to exhaust current stock within the forward horizon. |
| Order-by date | the date by which an order must be placed, computed as projected stockout date minus lead time minus safety margin. |
| Safety margin | buffer time added to lead time (REQ-007); configurable per ingredient or supplier during data setup (REQ-039). |
| Suggested order quantity | the quantity recommended to order to cover projected consumption across the lead-time gap. |
| Severity | the urgency ranking (Critical/High/Low) shared by stockout and spoilage risk; ranked band-first, then by proximity/cost within band (REQ-023). |
| Spoilage risk | a perishable ingredient's on-hand stock unlikely to be consumed before its use-by date. |
| Waste cost | the estimated rupee value of stock expected to spoil (unconsumed quantity × unit cost). |
| Materiality threshold | the configurable minimum waste cost below which a spoilage warning is suppressed (REQ-012). Defaults to ₹500. |
| Total waste exposure | the aggregate rupee figure summing estimated waste cost across every spoilage warning, including suppressed ones (REQ-027). |
| Risk dashboard | the single view listing every at-risk ingredient, ordered by severity. |
| Chat Agent | the single conversational interface for both explanation and what-if scenarios. |
| What-if scenario | a hypothetical demand change posed in natural language, previewed without committing to it. |
| Purchase order draft | the editable, ready-to-send text artifact naming supplier, item, quantity and required delivery date. |
| Lead time | days a supplier takes to deliver an ingredient after an order is placed. |
| Use-by date | the date by which a specific batch of stock on hand must be consumed. |
| Shelf life | days an ingredient remains usable from receipt, provided as input, never inferred. |
| Perishable ingredient | an ingredient flagged with a shelf life, subject to spoilage-risk assessment. |
| Data setup | the one-time initial load of the six Input Data categories through the five dedicated screens (REQ-037–REQ-041). |
| Per-user login | the individual email/password credential each of the two named personas (kitchen-manager, fb-manager) uses to authenticate independently (REQ-043, REQ-044). Each persona's credential set is distinct; none is shared. Corrects the rejected v1.4 "Shared login" concept. |

## Open Questions

- **OQ-1** — RESOLVED (v1.3). Safety margin: configurable per ingredient/supplier, no fixed default, captured during data setup (REQ-039), used by REQ-007.
- **OQ-2** — RESOLVED (v1.3). Materiality threshold: flat ₹500 default, adjustable by the kitchen manager.
- **OQ-3** — RESOLVED (v1.3). Total waste exposure includes materiality-suppressed warnings, not only displayed ones.
- **OQ-4** — RESOLVED (v1.3). Stockout severity bands: Critical ≤2 days, High 3–7 days, Low \>7 days.
- **OQ-5** — RESOLVED (v1.3). Spoilage severity bands: Critical ≥₹2000, High ₹500–1999, Low \<₹500 (REQ-042); combined dashboard ranking is band-first, then proximity/cost.
- **OQ-6** — RESOLVED (v1.5). MFA is deferred to a later phase; not in scope for v1. No REQ added.
- **OQ-7** — RESOLVED (v1.5). Manager/support-assisted password reset only; no self-service reset flow in v1.
- **OQ-8** — RESOLVED (v1.5). No automatic session idle-timeout in v1.
- **OQ-9** — RESOLVED (v1.6). Kitchen-manager and fb-manager have identical access once authenticated — no restricted or aggregate-only view for fb-manager.

## Change Log

| Version | Date | Added | Changed | Retired |
| --- | --- | --- | --- | --- |
| 1.0 | 2026-09-17 | REQ-001–REQ-035, OQ-1–OQ-5 | — | — |
| 1.1 | 2026-09-17 | REQ-036 | REQ-013, REQ-017 (name Chat Agent explicitly) | — |
| 1.2 | 2026-09-17 | REQ-037–REQ-041 | Non-Goals "Ongoing data entry" clarified | — |
| 1.3 | 2026-09-17 | REQ-042 | REQ-007, REQ-009, REQ-012, REQ-023, REQ-026, REQ-027, REQ-034, REQ-039 | — |
| 1.4 | 2026-09-17 | REQ-043, REQ-044, OQ-6, OQ-7, OQ-8 | Non-Goals/Constraints reworded to permit a login (single shared credential, per ARCH-016) | — |
| 1.5 | 2026-09-17 | OQ-9 | REQ-044 (single shared credential → per-user login); Non-Goals/Constraints/Glossary reworded to per-user login | — |
| 1.6 | 2026-09-17 | — | OQ-9 resolved (identical access, no restriction for fb-manager); Non-Goals hedge removed | — |
