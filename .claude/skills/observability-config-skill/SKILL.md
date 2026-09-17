---
name: observability-config-skill
description: Creates or updates dashboards and alert thresholds against whatever monitoring/observability platform the repo/team already uses (Datadog, Grafana, CloudWatch, Azure Monitor, etc.), and never invents a new observability stack. Used by ops-observability-agent.
---

# Observability Config Skill

Configures real dashboards and alerts against the team's actual monitoring platform — the execution layer behind `ops-observability-agent`'s signal/threshold definitions.

## Used by

`ops-observability-agent`.

## Input

| Parameter | Required | Description |
|---|---|---|
| `Platform` | Yes | Detected from existing repo/infra config (e.g. Terraform `aws_cloudwatch_*` resources, a `datadog.yaml`, a Grafana provisioning folder) — never assumed if not already present |
| `Signal` | Yes | The metric/signal to monitor (error rate, latency, saturation, business metric) |
| `Threshold` | Yes | The alert condition, sourced from the architecture doc's non-functional requirements or an explicit human-provided SLO — never invented |
| `Feature` | Yes | The feature/component this signal traces back to, for traceability in the output artifact |

## Steps

1. Detect the platform already in use. If none is detected and the team has no existing observability stack, **stop** and report the gap rather than standing up a new tool unprompted.
2. Check whether a dashboard/alert for this exact signal already exists (search by name/tag convention already used in the platform) — never create a duplicate.
3. Create or update the dashboard panel / alert rule via the platform's actual API or IaC mechanism (e.g. a Terraform resource, a platform API call, a config file the platform reads) — matching however the rest of the team's dashboards/alerts are already defined.
4. Confirm the alert/dashboard is actually live (e.g. read it back, or confirm the IaC apply succeeded) before reporting success.

## Output

| Field | Description |
|---|---|
| `Status` | `Configured` \| `AlreadyExists` \| `Gap` (platform/threshold basis missing) \| `Failed` |
| `DashboardUrl` / `AlertId` | Present on `Configured`/`AlreadyExists` |
| `Error` | Populated only on `Failed` |

## Error Handling

- Never report `Configured` unless the dashboard/alert was actually created/updated and confirmed live — a described-but-unconfigured alert is a `Gap`, not a success.
- Never fabricate an SLO/threshold number — if none is documented, report `Gap` and ask, don't invent one.
- Do not stand up a new observability platform on the agent's own initiative — that's a team decision, not something to default into.
