---
name: product-analytics-skill
description: Queries whatever product analytics/telemetry source the team already has (product analytics tool, application logs, or the signals observability-config-skill defined) to pull real usage/outcome numbers for a shipped feature, against the original PRD/feature success criteria. Never fabricates a number when the source isn't reachable. Used by ops-product-metrics-agent.
---

# Product Analytics Skill

Pulls real, evidenced usage/outcome data — the execution layer behind `ops-product-metrics-agent`'s PRD-goal-to-outcome comparison.

## Used by

`ops-product-metrics-agent`.

## Input

| Parameter | Required | Description |
|---|---|---|
| `Metric` | Yes | The specific metric implied by a PRD/feature success criterion (e.g. adoption rate, conversion, error rate, time-to-completion) |
| `DataSource` | Yes | Detected from what's actually available (product analytics tool API, application/query logs, an existing dashboard from `observability-config-skill`) — never assumed if not already configured |
| `Timeframe` | Yes | The window to measure against (e.g. since the feature's release date) |
| `Feature` | Yes | The `FEAT-XXX`/`US-XXX` this metric traces back to, for traceability in the output |

## Steps

1. Confirm `DataSource` is actually reachable in this session (API credentials/connector configured, logs accessible, dashboard queryable). If not, **stop** and report `Status: NotReachable` — do not estimate or fabricate a plausible-looking number.
2. Query `DataSource` for `Metric` over `Timeframe`.
3. Compare the actual result against the original PRD/feature-spec success criterion for `Feature`.
4. Note whether the comparison shows correlation only, or whether causation can reasonably be inferred (e.g. via a controlled rollout/A-B test) — never assert causation from a bare before/after comparison.

## Output

| Field | Description |
|---|---|
| `Status` | `Measured` \| `NotReachable` \| `NotYetMeasurable` (insufficient time/data since release) |
| `Value` | The actual measured value/trend, present on `Measured` |
| `Comparison` | `Met` \| `PartiallyMet` \| `NotMet`, relative to the stated success criterion |
| `CausalConfidence` | `Correlation only` \| `Reasonable causal inference` \| `Not applicable` |

## Error Handling

- Never fabricate a usage number, conversion rate, or adoption figure — a `NotReachable`/`NotYetMeasurable` result must be reported plainly, with the reason.
- Never silently redefine the original success criterion to make an outcome look better — if the original criterion turns out to be unmeasurable with the available data source, report that as a finding, not as a passing result.
