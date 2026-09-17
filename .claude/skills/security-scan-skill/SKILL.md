---
name: security-scan-skill
description: Runs SAST, dependency, and secret scanning using whichever scanner is already configured in the repo (semgrep, npm audit, pip-audit, gitleaks, etc.), triaging findings into exploitable/in-scope vs. noise. Never introduces a new scanning tool the repo hasn't already adopted. Used by ops-security-scan-agent, and available to code-review-agent / code-review-independent-agent as a stronger alternative to ad hoc Grep-based secret checks.
---

# Security Scan Skill

Runs the repository's already-configured security scanning tooling and returns structured, triaged findings — so agents doing code/security review don't each reimplement a weaker Grep-pattern approximation of the same checks.

## Used by

`ops-security-scan-agent` (primary), `code-review-agent`, `code-review-independent-agent` (as an upgrade to their inline hardcoded-secret Grep patterns).

## Input

| Parameter | Required | Description |
|---|---|---|
| `Scope` | Yes | Repository path, changed-files list (for a PR-scoped scan), or a deployed target URL (DAST — only with explicit authorization) |
| `ScanTypes` | No | Subset of `sast`, `dependency`, `secret`, `dast` to run — default: all except `dast` |
| `ExistingTools` | No | Explicit list of already-configured tools to use (e.g. `semgrep`, `npm audit`, `gitleaks`) — if omitted, detect from repo config (`.semgrep.yml`, CI workflow files, lockfiles present) |

## Steps

1. Detect which scanners are already configured in the repo (CI workflow files, config files like `.semgrep.yml`/`.gitleaks.toml`, or manifest-driven tools like `npm audit`/`pip-audit`). Never install or invoke a scanner the repo hasn't already adopted without asking first.
2. Run each applicable scanner against `Scope`, capturing literal output.
3. **DAST only:** confirm explicit authorization for the target before running anything — refuse and report the gap if authorization isn't confirmed by the caller.
4. Triage raw findings:
   - Drop findings in dependencies scoped to dev/test-only that don't ship to production, unless the caller says otherwise.
   - Flag anything already logged as an accepted risk (cross-reference `artifacts/risk/risk-register.md` if the caller provides it) rather than re-raising it as new.
   - Keep everything else, tagged with severity as reported by the scanner (don't re-invent a severity scale).

## Output

| Field | Description |
|---|---|
| `Status` | `PASS` (no Critical/High) \| `FAIL` (unmitigated Critical/High present) \| `PartiallySkipped` |
| `Findings` | List of `{tool, severity, location, description, exploitability_note}` |
| `SkippedScanTypes` | Any requested scan type that couldn't run in this environment, and why |

## Error Handling

- Never claim a scan type ran if the tool wasn't actually available — report it under `SkippedScanTypes` instead of silently omitting it.
- Never suppress or downgrade a finding's severity without the calling agent explicitly stating the justification (and that justification must be carried into the agent's own output, not absorbed here).
- A finding with no confirmed exploitability assessment should say so rather than asserting exploitability it can't demonstrate.
