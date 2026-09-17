---
description: Generate or update Terraform infrastructure code via infra-terraform-coding-agent
argument-hint: "<project-name-or-confluence-url> [local-fallback-path]"
---

# Terraform Code Generation

Dispatch `infra-terraform-coding-agent` (`.claude/agents/infra-terraform-coding-agent.md`) to generate/update the `/infra` Terraform tree from the project's architecture documents.

Input given: `$ARGUMENTS`

## Step 0 — Infrastructure Architecture is a hard prerequisite

`infra-terraform-coding-agent` requires an **Infrastructure Architecture** document as its primary source (resource inventory, sizing, network topology, environment specs — its `resource_inventory` / `cloud_platform_standards` / `environment_config` canonical structure). Without it, the agent's Input Validation step stops with missing required fields.

Check whether `artifacts/architecture/infrastructure-architecture.md` exists and is `APPROVED`:
- **Missing** → stop and run `/generate-architecture` first (it dispatches `infra-architecture-agent` for whichever architecture docs, including this one, don't exist yet), then retry this command.
- **Exists but only `DRAFT`** → flag it to the user; proceeding with an unapproved draft as ground truth for generated infrastructure code is a judgment call the human should confirm, not one to make silently.
- **Exists and `APPROVED`** → continue to Step 0.5.

## Step 0.5 — Optional: resolve remaining `[TBD]`s via DevOps-expert defaults

`infrastructure-architecture.md` is written to never invent sizing/region/tooling — in most real runs it will still contain `[TBD]` fields that block `infra-terraform-coding-agent`'s Input Validation (missing `resource_inventory[].size`, `cloud_platform_standards.naming_convention`, `environment_config[].region`, etc.). There are two ways to clear these; ask the user which one applies rather than assuming:

1. **The user (or a prior gate) has already answered them directly** in `infrastructure-architecture.md` itself (its own `[TBD]` markers were resolved via the Architecture Suite Approval gate's mandatory-question rule) → nothing to do here, continue to Step 1.
2. **They're still open** → offer to dispatch `infra-devops-expert-agent` (`.claude/agents/infra-devops-expert-agent.md`). It proposes concrete defaults (region, instance sizing, IaC tool, naming convention, branching strategy, etc.) for every engineering-judgment gap, but explicitly cannot invent organizational facts (account ID, real cost-center code, named owner) — those remain `[TBD]` regardless.
   - It writes `artifacts/architecture/tf-coding-inputs.md` (`Status: DRAFT`).
   - **Gate — DevOps Defaults Approval.** Present every assumption individually (field, proposed value, rationale) and every remaining organizational-fact gap individually. Require one of: `APPROVE`, `REQUEST_CHANGES` (route back to `infra-devops-expert-agent`, re-present), or `STOP`. Same hard rule as every other gate in this repo: a blanket "approve" that doesn't address each flagged assumption/gap by name does not clear it. Any remaining organizational-fact gap must be either answered by the human or explicitly deferred with a stated reason (recorded in `workflow/decisions.md`) — it cannot silently pass through as if it were an assumption already resolved.
   - On `APPROVE`, update `tf-coding-inputs.md`'s metadata to `Human approval status: APPROVED`. This file — not the raw `infrastructure-architecture.md` — becomes the source for Step 1.
   - If the user declines this step, continue to Step 1 with `infrastructure-architecture.md` as-is; `infra-terraform-coding-agent` will stop on its own Input Validation if fields are still missing, per its existing hard rule.

## Step 1 — Resolve source

- If `artifacts/architecture/tf-coding-inputs.md` exists and is `APPROVED` (Step 0.5 was run), use it as the local `yaml_json`-style source — it's already normalized to the canonical structure and takes priority over re-resolving from Confluence/`infrastructure-architecture.md`.
- Otherwise, if `$ARGUMENTS` is a Confluence URL or a bare project/document name, use `atlassian` as the source. The agent reads, under `AI SDLC - Architecture >> Architecture >> {Project-Name} Solution Architecture`:
  - `{Project-Name} Infrastructure Architecture`
  - `{Project-Name} Security Architecture`
- If the document hasn't been published to Confluence yet (still local-only from `infra-architecture-agent`/`solution-security-architecture-agent`), pass the local files directly as the fallback source: `artifacts/architecture/infrastructure-architecture.md` and `artifacts/architecture/security-architecture.md`.
- If a different local fallback path (YAML/JSON or PDF) is given instead, or Atlassian is unreachable, use that as the source — never silently prefer a local file over a reachable Confluence source when both could apply.
- If neither a project name nor a fallback path was given, ask for one before dispatching.

## Step 2 — Dispatch

Invoke `infra-terraform-coding-agent` with the resolved source. Let it run its own Invocation Behavior check (empty workspace → full generation; existing `.tf` files → drift report and STOP for approval before changing anything).

## Step 3 — Report

Summarize: which documents were resolved (including whether `tf-coding-inputs.md` was used), empty-workspace generation vs. drift report, and (if drift) wait for explicit user approval before the agent applies any changes. On successful generation, report the plan preview, generated structure, and `iam-policy.json` placeholders that still need real values (`{{ACCOUNT_ID}}`, `{{PROJECT_NAME}}`).
