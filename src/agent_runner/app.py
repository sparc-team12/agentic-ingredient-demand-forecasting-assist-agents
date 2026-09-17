"""Streamlit control panel for running this project's Claude Code agent commands
without typing them into a chat session.

Run with:
    streamlit run src/agent_runner/app.py

This is a developer tool, separate from the product's own Streamlit dashboard
(the kitchen-manager-facing app described in the PRD, REQ-026). It only ever
shells out to the `claude` CLI with an explicit --allowedTools list and
--permission-prompts none -- it never uses --dangerously-skip-permissions, so
anything outside the chosen profile's allowlist is denied, not bypassed.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from commands import PROFILES  # noqa: E402
from runner import RunEvent, run_claude_command  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(page_title="Agent Runner", page_icon="\U0001F916", layout="wide")

st.title("Agent Runner")
st.caption(f"Project root: `{PROJECT_ROOT}`")

if "history" not in st.session_state:
    st.session_state.history = []  # list of {profile, prompt, started_at, events: [...]}

with st.sidebar:
    st.header("Settings")
    claude_bin = st.text_input(
        "claude executable",
        value="claude",
        help=(
            "If 'claude' isn't found, give the full path "
            "(e.g. C:\\Users\\<you>\\.local\\bin\\claude or its .cmd/.exe wrapper)."
        ),
    )
    st.markdown("---")
    st.markdown(
        "**Safety note:** every run uses an explicit tool allowlist "
        "(`--allowedTools`) plus `--permission-prompts none`. Anything not "
        "in the allowlist is **denied**, never silently bypassed. "
        "`--dangerously-skip-permissions` is never used by this tool."
    )

profile_key = st.selectbox(
    "Run profile",
    options=list(PROFILES.keys()),
    format_func=lambda k: PROFILES[k].label,
)
profile = PROFILES[profile_key]

st.info(profile.description)

if profile.key == "custom":
    prompt = st.text_area(
        "Prompt / command",
        value="",
        placeholder="e.g. /architecture WF-2026-001, or 'Dispatch solution-tech-stack-agent'",
    )
    extra_tools_raw = st.text_input(
        "Additional allowed tools (space-separated, optional)",
        value="",
        help="Only add what this specific run genuinely needs -- e.g. a single MCP tool name.",
    )
    allowed_tools = list(profile.allowed_tools)
    if extra_tools_raw.strip():
        allowed_tools += extra_tools_raw.split()
else:
    prompt = profile.prompt
    allowed_tools = list(profile.allowed_tools)

with st.expander("Tool allowlist for this run"):
    st.code("\n".join(sorted(allowed_tools)), language="text")

confirmed = True
if profile.requires_confirmation:
    confirmed = st.checkbox(profile.confirmation_text)

run_clicked = st.button(
    "Run",
    type="primary",
    disabled=not confirmed or not prompt.strip(),
)

log_container = st.container()

if run_clicked:
    run_record = {
        "profile": profile.label,
        "prompt": prompt,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "events": [],
    }

    log_placeholder = log_container.empty()
    status_placeholder = log_container.empty()
    lines: list[str] = []

    def render() -> None:
        log_placeholder.code("\n".join(lines[-500:]) or "(waiting for output...)", language="text")

    status_placeholder.info("Running...")
    render()

    final_result: dict | None = None
    had_error = False

    for event in run_claude_command(
        claude_bin=claude_bin,
        prompt=prompt,
        cwd=PROJECT_ROOT,
        allowed_tools=allowed_tools,
        permission_mode=profile.permission_mode,
    ):
        run_record["events"].append({"kind": event.kind, "payload": str(event.payload)[:2000]})

        if event.kind == "system":
            lines.append(f"[session] {event.payload.get('subtype', '')}")
        elif event.kind == "assistant_text":
            lines.append(event.payload["text"])
        elif event.kind == "tool_use":
            for t in event.payload["tools"]:
                lines.append(f"[tool call] {t.get('name')}  input={t.get('input')}")
        elif event.kind == "tool_result":
            for r in event.payload["results"]:
                content = r.get("content")
                is_error = r.get("is_error", False)
                tag = "tool error" if is_error else "tool result"
                lines.append(f"[{tag}] {str(content)[:1000]}")
                if is_error:
                    had_error = True
        elif event.kind == "result":
            final_result = event.payload
            lines.append(f"[result] {event.payload.get('subtype')}: {event.payload.get('result', '')}")
        elif event.kind == "stderr":
            had_error = True
            lines.append(f"[stderr] {event.payload}")
        elif event.kind == "process_error":
            had_error = True
            lines.append(f"[error] {event.payload}")
        else:
            lines.append(f"[raw] {str(event.payload)[:500]}")

        render()

    if final_result is not None and final_result.get("is_error"):
        had_error = True

    if had_error:
        status_placeholder.error("Run finished with errors or denied tool calls -- review the log above.")
    else:
        status_placeholder.success("Run finished.")

    st.session_state.history.insert(0, run_record)

if st.session_state.history:
    st.markdown("---")
    st.subheader("Run history (this session)")
    for i, record in enumerate(st.session_state.history):
        with st.expander(f"{record['started_at']} -- {record['profile']}"):
            st.text(record["prompt"])
            st.caption(f"{len(record['events'])} events")
