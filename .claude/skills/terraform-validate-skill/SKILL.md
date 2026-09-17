---
name: terraform-validate-skill
description: Runs the standard Terraform validation loop (terraform fmt, terraform validate, tflint, and optionally tfsec/checkov) against a given directory, capturing and returning structured pass/fail results. Extracted from the duplicated validation logic in infra-terraform-coding-agent's Validation Loop and infra-pipeline-agent's lint job — call this instead of reimplementing the command sequence per agent.
---

# Terraform Validate Skill

A single, shared implementation of the Terraform lint/validate/security-scan sequence, so infrastructure agents don't each hand-roll slightly different versions of the same checks.

## Used by

`infra-terraform-coding-agent` (its Validation Loop step), `infra-pipeline-agent` (generating/mirroring the `lint`/`validate` CI jobs), `ops-security-scan-agent` (IaC-specific scanning).

## Input

| Parameter | Required | Description |
|---|---|---|
| `Directory` | Yes | The Terraform root module directory to validate (e.g. `infra/network`, `infra/application`) |
| `RunSecurityScan` | No | `true`/`false` — whether to also run `checkov`/`tfsec` (default `true` if either tool is already present in the repo's tooling, else skip and report as unavailable rather than installing something new) |
| `TflintVersion` | No | Pin version if the repo's CI config specifies one; otherwise use whatever is already installed |

## Steps

1. `terraform fmt -check -recursive` against `Directory` — do not auto-apply formatting fixes unless the caller explicitly asked for a fix pass rather than a check.
2. `terraform init -backend=false` (never touch remote state during validation).
3. `terraform validate`.
4. `tflint --init && tflint --recursive` (only if `tflint` is available in the environment/repo — report as skipped, not failed, if it isn't).
5. If `RunSecurityScan`: run whatever IaC scanner the repo already uses (`checkov -d <Directory>` or `tfsec <Directory>`) — never introduce a new scanner the repo hasn't already adopted without asking first.
6. Capture the literal output and exit code of every command run.

## Output

| Field | Description |
|---|---|
| `Status` | `PASS` \| `FAIL` \| `PartiallySkipped` (some checks unavailable in this environment) |
| `Results` | Per-command: `{command, exitCode, output, status}` |
| `SecurityFindings` | Present if `RunSecurityScan` ran — list of `{severity, resource, description}` |

## Error Handling

- Never report `PASS` unless every command that actually ran returned a clean exit code — a skipped check (tool unavailable) must be reported as `PartiallySkipped`, not folded silently into `PASS`.
- On any `FAIL`, return the exact command output so the calling agent can fix the specific error rather than guessing.
- Do not attempt to auto-fix `terraform validate` errors — that's the calling agent's job; this skill only runs and reports.
