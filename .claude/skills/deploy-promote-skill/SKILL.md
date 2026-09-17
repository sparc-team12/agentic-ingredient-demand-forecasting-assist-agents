---
name: deploy-promote-skill
description: Triggers promotion of a merged build to the next environment in the pipeline (workflow_dispatch, terraform apply, or platform-specific deploy command — detected from the repo's actual tooling, never assumed), runs a post-deploy smoke check, and drives or reports rollback on failure. Used by release-deploy-agent.
---

# Deploy / Promote Skill

Drives one environment-promotion step end to end: trigger → smoke check → pass/fail/rollback. This is the execution layer behind `release-deploy-agent`'s environment-by-environment promotion.

## Used by

`release-deploy-agent`.

## Input

| Parameter | Required | Description |
|---|---|---|
| `Environment` | Yes | Target environment for this promotion (e.g. `dev`, `qa`, `stage`, `prod`) |
| `MergeCommit` | Yes | The commit/PR reference being promoted |
| `TriggerMechanism` | Yes | Detected from the repo: `github-workflow-dispatch`, `terraform-apply`, or a named platform CLI/deploy command — never invent one not already present in the repo's CI config |
| `SmokeCheck` | Yes | The health endpoint, key transaction, or check command defined in the deployment architecture for this environment |
| `RollbackMechanism` | No | If known/documented — e.g. a previous-version redeploy command, a `terraform apply` of the prior state, or a platform rollback command |

## Steps

1. Confirm the merge commit's automated CI run (lint/validate/plan or app-build pipeline) is green before triggering anything. If not confirmed, **stop** — do not trigger a promotion on an unverified commit.
2. Confirm any required environment protection/approval gate for `Environment` has been cleared (e.g. GitHub Environment required reviewers) — if the gate is still pending, report `Status: Blocked` and who must clear it. Never bypass it.
3. Trigger `TriggerMechanism` for `Environment`.
4. Wait for the trigger to complete, capturing its actual result (success/failure) — never assume success from having merely started the trigger.
5. Run `SmokeCheck` against the now-deployed environment. Capture the literal result.
6. On smoke-check failure: **halt** — do not proceed to the next environment. If `RollbackMechanism` is known, execute it and report the outcome; if unknown, report exactly what manual rollback steps are needed and stop.

## Output

| Field | Description |
|---|---|
| `Status` | `Promoted` \| `Blocked` (awaiting approval gate) \| `Failed` \| `RolledBack` |
| `Environment` | The environment acted on |
| `TriggerResult` | Raw result of the trigger mechanism |
| `SmokeCheckResult` | Raw result of the smoke check |
| `RollbackResult` | Present only if a rollback was attempted |

## Error Handling

- Never mark `Status: Promoted` without an actually-observed passing smoke check.
- Never bypass a pending required-reviewer/approval gate, even under explicit instruction to "just deploy it" — report the gate and stop.
- Never fabricate a deployment URL, version tag, or rollback confirmation — every field must reflect a command that was actually run.
- If `RollbackMechanism` is undocumented for a data-bearing or infrastructure change, say so explicitly rather than assuming a generic revert is sufficient.
