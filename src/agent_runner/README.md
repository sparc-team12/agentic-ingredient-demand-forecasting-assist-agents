# Agent Runner

A small Streamlit control panel for running this project's Claude Code agent
commands (e.g. `/generate-architecture`) without typing them into a chat
session each time. This is a **developer tool**, unrelated to the actual
product's own Streamlit dashboard described in the PRD (REQ-026).

## Setup

```bash
pip install -r src/agent_runner/requirements.txt
```

Requires the `claude` CLI to be installed and already authenticated (same
account/session you use normally).

## Run

From the project root:

```bash
streamlit run src/agent_runner/app.py
```

## How it decides what agents are allowed to do

Every run shells out to `claude -p "<prompt>"` with an **explicit**
`--allowedTools` list and `--permission-prompts none`. Anything not in that
list is automatically **denied** — this tool never passes
`--dangerously-skip-permissions` / `bypassPermissions`, so it can't silently
bypass the human-approval gates built into `.claude/agents/` and
`.claude/skills/` (PRD confirmation, ARCH-XXX approval, the
`[SECURITY REVIEW REQUIRED]` gate, Confluence publish confirmation).

Two built-in profiles, see `commands.py`:

- **Generate Architecture (local only)** — can read/write local files and
  fetch (read-only) from Confluence, but has no Confluence *write* tools, so
  it will run PRD resolution → `ARCH-XXX` → the three architecture doc drafts
  → `validation-review`, then cleanly stop at the publish step (denied, not
  silently skipped) so you can review before publishing.
- **Publish Architecture Suite to Confluence** — adds the Confluence write
  tools, gated behind an explicit in-UI checkbox confirming you've reviewed
  the drafts and findings. That checkbox *is* the human-approval gate, moved
  from chat into this UI.

A **Custom** profile lets you run any other prompt/command (e.g. a single
named agent) with the same local-file-only default allowlist, plus an
optional field to add specific extra tools a particular run genuinely needs.

## Output

Streams `claude`'s `--output-format stream-json` events live: assistant text,
tool calls (with their input), tool results (errors highlighted), and the
final result summary. Full run history for the session is kept below the log.
