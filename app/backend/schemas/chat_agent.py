"""Pydantic schemas for the Chat Agent HTTP contract (ACRI-45 US-...
explanation-on-demand, ACRI-49..52 what-if scenarios).

Mirrors `services/chat_agent_service.py::ChatAgentResult` one-to-one for
the response; the request is the one shape both entry points (ACRI-45's
"ask why flagged" and ACRI-49's free what-if conversation) share.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatAgentRequest(BaseModel):
    """Request body for `POST /chat-agent/ask`.

    `ingredient_id` is set when the Chat Agent is opened via "ask why
    flagged" from Ingredient Detail with an ingredient already in focus
    (ACRI-45 AC1/AC2); `None` when opened directly for a free what-if
    conversation (ACRI-49) — the frontend distinguishes these two entry
    points, not this schema.
    """

    message: str = Field(min_length=1)
    ingredient_id: int | None = None


class ChatAgentResponse(BaseModel):
    """Response body for `POST /chat-agent/ask`: the phrased natural-
    language reply plus the classified intent (`"explanation"`,
    `"what_if"`, or `"unparseable"`), so the frontend can show which mode
    the agent understood without re-parsing the reply text."""

    reply: str
    intent: str
