"""Chat Agent HTTP route (ACRI-45 explanation-on-demand, ACRI-49..52
what-if scenarios).

One `APIRouter` (`chat_agent_router`), depending on
`middleware.auth.get_current_user` — reused verbatim, the identical
gating pattern used by every other route in this codebase. No
persona-based branching.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db
from middleware.auth import get_current_user
from schemas.chat_agent import ChatAgentRequest, ChatAgentResponse
from services import chat_agent_service

chat_agent_router = APIRouter(prefix="/chat-agent", tags=["chat-agent"])


@chat_agent_router.post("/ask", response_model=ChatAgentResponse)
def post_chat_agent_ask(
    payload: ChatAgentRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ChatAgentResponse:
    """`POST /chat-agent/ask` (ACRI-45..52). Raises `503` when
    `GEMINI_API_KEY` is not configured (see `services/llm_client.py`) and
    `404` for an unknown `ingredient_id` — both propagated as ordinary
    `HTTPException`s FastAPI already turns into clean JSON error responses."""
    result = chat_agent_service.handle_chat_agent_request(
        payload.message, payload.ingredient_id, db
    )
    return ChatAgentResponse(reply=result.reply, intent=result.intent)
