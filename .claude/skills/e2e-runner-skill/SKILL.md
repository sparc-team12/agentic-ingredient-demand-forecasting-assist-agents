---
name: e2e-runner-skill
description: Runs the repository's existing end-to-end/integration test framework (Playwright, Cypress, Postman/Newman, or a service-level integration harness) against a real or realistic environment, distinguishing environment/infrastructure flakiness from genuine regressions. Never introduces a new e2e framework the repo doesn't already use. Used by test-e2e-agent.
---

# E2E Runner Skill

Runs and interprets end-to-end test results — the execution layer behind `test-e2e-agent`'s scenario coverage.

## Used by

`test-e2e-agent`.

## Input

| Parameter | Required | Description |
|---|---|---|
| `Framework` | Yes | Detected from the repo (e.g. `playwright.config.ts`, `cypress.config.js`, a Postman collection, or a custom integration-test runner) — never introduce a new one unprompted |
| `Environment` | Yes | Where the suite runs — staging, a local docker-compose stack, or an explicitly sanctioned sandbox. Never production. |
| `Scenarios` | Yes | The scenario list to run/extend, sourced from the feature spec or the approved plan's Test Scenarios section |

## Steps

1. Confirm `Environment` is not production and is actually reachable/runnable in this session. If neither holds, report `Status: Blocked` with the reason — do not attempt to run against an unreachable or disallowed target.
2. Run the existing suite (or the new/extended scenarios) via `Framework`'s own CLI/runner.
3. On any failure, distinguish:
   - **Environment/infrastructure flakiness** — intermittent network/timing issues unrelated to the change under test (retry once to confirm before classifying as flaky; do not retry indefinitely).
   - **Genuine regression** — a real behavior mismatch caused by the change.
4. Never mark a scenario `PASS` without an actual run and an actual passing result in this session.

## Output

| Field | Description |
|---|---|
| `Status` | `AllPassed` \| `RegressionsFound` \| `Blocked` (environment unavailable) |
| `Results` | Per scenario: `{scenario, result: PASS/FAIL/FLAKY, evidence}` |
| `BlockedReason` | Present only on `Blocked` |

## Error Handling

- Never claim a scenario passed without an actual, observed run in this session.
- Never run against production or an environment without explicit authorization for this test activity.
- A scenario classified `FLAKY` still gets reported, not silently dropped — the calling agent decides whether to re-run, quarantine, or escalate it.
