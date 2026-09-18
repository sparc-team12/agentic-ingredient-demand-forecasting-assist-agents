"""Thin wrapper around the Google Gemini API (DEC-006), used exclusively by
`services/chat_agent_service.py` (ACRI-45..52).

Responsibility: a single `generate` function that calls
`gemini-2.5-flash` once, either for structured JSON extraction
(`response_schema` given) or for plain-text narration (`response_schema`
omitted). No business logic, no grounding rules, no prompt content lives
here — that all lives in `chat_agent_service.py`; this module only knows
how to talk to the Gemini API.

`GEMINI_API_KEY` is read from the environment (never hardcoded/committed —
see `.env.example`). When it is unset, `generate` raises a `503` *before*
constructing a client or making any network call, so a missing key never
crashes the server — the route this bubbles up to (`routes/chat_agent.py`)
lets FastAPI's normal `HTTPException` handling turn it into a clean JSON
503 response.
"""

from __future__ import annotations

import json
import os
from typing import Any

from fastapi import HTTPException, status
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.6-flash"


def _require_api_key() -> None:
    """Checked up front, before touching the SDK at all (per the explicit
    "check os.environ.get up front" direction) — a missing key must never
    surface as an unhandled crash."""
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat Agent is not configured (GEMINI_API_KEY missing)",
        )


def generate(
    system_prompt: str,
    user_content: str,
    response_schema: dict[str, Any] | None = None,
) -> str | dict[str, Any]:
    """Calls Gemini `gemini-2.5-flash` once with `system_prompt` as the
    system instruction and `user_content` as the sole user turn.

    When `response_schema` is given, requests structured JSON output
    (`response_mime_type="application/json"`) constrained to that schema
    and returns the parsed `dict`. Otherwise returns the model's plain-text
    reply as a `str`.

    Raises `HTTPException(503)` when `GEMINI_API_KEY` is not set (see
    `_require_api_key`) — callers do not need their own try/except for this
    case; FastAPI's default exception handling turns it into a clean 503
    response.
    """
    _require_api_key()
    client = genai.Client()
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json" if response_schema is not None else None,
        response_schema=response_schema,
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_content,
        config=config,
    )
    text = response.text or ""
    if response_schema is not None:
        parsed: dict[str, Any] = json.loads(text)
        return parsed
    return text
