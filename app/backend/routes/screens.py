"""Protected stub screen routes (ACRI-66).

Four placeholder routes, one per gated screen named in the approved Design
Document (risk dashboard, ingredient detail, Chat Agent, purchase-order
draft). Each requires authentication only (`get_current_user`) — there is no
persona-based branching anywhere in this module, so both personas receive an
identical response shape (AC5). Real business logic for each screen lands in
later, dedicated stories.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from db.models import User
from middleware.auth import get_current_user
from schemas.auth import ScreenPlaceholderResponse, UserOut

router = APIRouter(prefix="/screens", tags=["screens"])

_PLACEHOLDER_MESSAGE = "Authenticated placeholder — business logic not yet implemented"


def _placeholder_response(screen: str, current_user: User) -> ScreenPlaceholderResponse:
    return ScreenPlaceholderResponse(
        screen=screen,
        message=_PLACEHOLDER_MESSAGE,
        user=UserOut(email=current_user.email, persona=current_user.persona),
    )


@router.get("/risk-dashboard", response_model=ScreenPlaceholderResponse)
def risk_dashboard(current_user: User = Depends(get_current_user)) -> ScreenPlaceholderResponse:
    return _placeholder_response("risk-dashboard", current_user)


@router.get("/ingredient-detail", response_model=ScreenPlaceholderResponse)
def ingredient_detail(current_user: User = Depends(get_current_user)) -> ScreenPlaceholderResponse:
    return _placeholder_response("ingredient-detail", current_user)


@router.get("/chat-agent", response_model=ScreenPlaceholderResponse)
def chat_agent(current_user: User = Depends(get_current_user)) -> ScreenPlaceholderResponse:
    return _placeholder_response("chat-agent", current_user)


@router.get("/purchase-order-draft", response_model=ScreenPlaceholderResponse)
def purchase_order_draft(
    current_user: User = Depends(get_current_user),
) -> ScreenPlaceholderResponse:
    return _placeholder_response("purchase-order-draft", current_user)
