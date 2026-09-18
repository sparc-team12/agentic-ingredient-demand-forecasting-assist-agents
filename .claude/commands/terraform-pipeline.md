---
description: Create or update the GitHub Actions Terraform CI/CD pipeline via infra-pipeline-agent
argument-hint: "<project-name-or-confluence-url> [changes: <description>]"
---

# Terraform Pipeline Generation

Dispatch `infra-pipeline-agent` (`.claude/agents/infra-pipeline-agent.md`) to create or update `.github/workflows/terraform.yml`.

Input given: `$ARGUMENTS`

## Step 0 — Infrastructure Architecture is a hard prerequisite

`infra-pipeline-agent`'s `deployment_value` document must contain six required sections (Architecture Overview, CI/CD Pipeline Diagram, Branching Strategy, Environment Strategy, CI/CD Pipeline Stages, Infrastructure as Code) or the agent stops at its section-validation step. In this repo, `infra-architecture-agent`'s output (`artifacts/architecture/infrastructure-architecture.md`) is what supplies those sections — there is no separate "Deployment Architecture" document/agent.

Check whether `artifacts/architecture/infrastructure-architecture.md` exists and is `APPROVED`:
- **Missing** → stop and run `/generate-architecture` first (it dispatches `infra-architecture-agent` for whichever architecture docs, including this one, don't exist yet), then retry this command.
- **Exists but only `DRAFT`** → flag it to the user before proceeding — an unapproved draft driving a CI/CD pipeline is a judgment call the human should confirm.
- **Exists and `APPROVED`** → continue to Step 1, using it as the `deployment_value` source.

## Step 1 — Resolve inputs

From `$ARGUMENTS`, determine:
- `deployment_source` / `deployment_value` — `atlassian` (Confluence URL or document name — the `{Project-Name} Infrastructure Architecture` page) or `pdf` (local fallback: `artifacts/architecture/infrastructure-architecture.md` if not yet published)
- `security_source` / `security_value` — same pattern, for the **Security Architecture** document (`artifacts/architecture/security-architecture.md` as local fallback)
- `changes_requested` *(optional)* — if the user described a specific change to an existing pipeline rather than asking for fresh generation, pass it verbatim

If the deployment or security document reference wasn't given, ask for it before dispatching — do not guess a project name or assume both documents share one source.

## Step 2 — Dispatch

Invoke `infra-pipeline-agent` with the resolved inputs. It will:
- Resolve and read both documents (Confluence primary, PDF fallback)
- Validate required sections in each — STOP and report if any are missing
- Detect operation mode (Create / Architecture update / Change request) from whether `.github/workflows/terraform.yml` already exists and whether `changes_requested` was given
- Generate/update the pipeline YAML and open a PR

## Step 3 — Report

Report the PR URL and branch name on success. If the agent stopped on missing required sections, relay exactly which sections are missing from which document. If `git push`/`gh pr create` failed, relay the exact error and suggested remediation.
