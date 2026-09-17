"""Subprocess wrapper around the `claude` CLI in non-interactive print mode.

Streams parsed --output-format stream-json events one at a time so a caller
(e.g. the Streamlit app in app.py) can render progress live instead of waiting
for the whole run to finish. Deliberately never passes
--dangerously-skip-permissions / bypassPermissions: callers pass an explicit
`allowed_tools` list, and --permission-prompts none makes anything outside
that list auto-deny instead of hang or silently pass.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunEvent:
    kind: str  # "system" | "assistant_text" | "tool_use" | "tool_result" | "result" | "raw" | "stderr" | "process_error"
    payload: dict | str


def build_command(
    claude_bin: str,
    prompt: str,
    allowed_tools: list[str],
    permission_mode: str = "acceptEdits",
) -> list[str]:
    return [
        claude_bin,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--include-partial-messages",
        "--permission-mode",
        permission_mode,
        "--permission-prompts",
        "none",
        "--allowedTools",
        " ".join(allowed_tools),
        "--no-session-persistence",
    ]


def _parse_line(line: str) -> RunEvent:
    line = line.strip()
    if not line:
        return RunEvent(kind="raw", payload="")
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return RunEvent(kind="raw", payload=line)

    obj_type = obj.get("type")

    if obj_type == "system":
        return RunEvent(kind="system", payload=obj)

    if obj_type == "result":
        return RunEvent(kind="result", payload=obj)

    if obj_type == "assistant":
        content = (obj.get("message") or {}).get("content") or []
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        tool_uses = [c for c in content if isinstance(c, dict) and c.get("type") == "tool_use"]
        if tool_uses:
            return RunEvent(kind="tool_use", payload={"tools": tool_uses, "raw": obj})
        if texts:
            return RunEvent(kind="assistant_text", payload={"text": "".join(texts), "raw": obj})
        return RunEvent(kind="raw", payload=obj)

    if obj_type == "user":
        content = (obj.get("message") or {}).get("content") or []
        tool_results = [c for c in content if isinstance(c, dict) and c.get("type") == "tool_result"]
        if tool_results:
            return RunEvent(kind="tool_result", payload={"results": tool_results, "raw": obj})
        return RunEvent(kind="raw", payload=obj)

    return RunEvent(kind="raw", payload=obj)


def run_claude_command(
    claude_bin: str,
    prompt: str,
    cwd: Path,
    allowed_tools: list[str],
    permission_mode: str = "acceptEdits",
) -> Iterator[RunEvent]:
    """Launches `claude -p` and yields RunEvent objects as output arrives.

    Raises FileNotFoundError if `claude_bin` can't be found/executed -- callers
    should catch this and surface a clear "claude CLI not found" message rather
    than a raw traceback.
    """
    cmd = build_command(claude_bin, prompt, allowed_tools, permission_mode)

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        yield RunEvent(kind="process_error", payload=f"Could not launch '{claude_bin}': {exc}")
        return

    assert proc.stdout is not None
    for line in proc.stdout:
        yield _parse_line(line)

    stderr_output = proc.stderr.read() if proc.stderr else ""
    proc.wait()

    if stderr_output.strip():
        yield RunEvent(kind="stderr", payload=stderr_output.strip())

    if proc.returncode != 0:
        yield RunEvent(
            kind="process_error",
            payload=f"claude exited with code {proc.returncode}",
        )
