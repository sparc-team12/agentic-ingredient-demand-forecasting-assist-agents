"""Business logic for the Chat Agent (ACRI-45 explanation-on-demand,
ACRI-49..52 what-if scenarios), backed by Google Gemini (DEC-006) via
`services/llm_client.py`.

Responsibility: one entry point, `handle_chat_agent_request`, covering
both conversation flows behind a single `POST /chat-agent/ask` (REQ-036 —
one Chat Agent interface, not two disconnected inputs):

1. Classify the free-text `message` into `intent: "explanation" |
   "what_if" | "unparseable"` via one Gemini call with structured JSON
   output (`_classify_intent`). `"unparseable"` (no AC written for this
   path — ACRI-45 AC5/ACRI-49 AC3 anticipate it without specifying exact
   wording) returns a plain "couldn't understand" message; nothing below
   this ever silently guesses at an intent.
2. **Explanation** (ACRI-45): builds a structured, deterministic
   "explanation data" dict in Python — contributing dishes and their
   share of an ingredient's projected demand (from
   `demand_projection_service.project_ingredient_demand`), the relevant
   date (`stockout_date`/`use_by_date`), and the supplier's
   `lead_time_days` for stockout specifically. Never fabricates a flag:
   if neither risk is present, the data says so plainly.
3. **What-if** (ACRI-49..52): resolves the dish name (case-insensitive),
   evaluates every ingredient's risk twice — once at baseline, once with
   the scenario's extra demand layered in via
   `demand_projection_service.ScenarioAdjustment` — and diffs the two
   snapshots in Python: newly-at-risk ingredients (ACRI-50), order-by-date
   shifts with direction (ACRI-51), and the total waste-exposure change in
   INR, including materiality-suppressed items in the sum (ACRI-52, same
   "never filter the sum" rule as `dashboard_service.py`). States plainly
   when nothing changed.

Grounding rule (DEC-006, ARCH-009): the *second* Gemini call in either
flow only ever phrases a reply from a structured JSON blob this module
already computed — `GROUNDING_SYSTEM_PROMPT` instructs it never to
compute, estimate, or invent a number. No HTTP concerns here — those live
in `routes/chat_agent.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Dish, Ingredient
from services import (
    demand_projection_service,
    llm_client,
    spoilage_risk_service,
    stockout_risk_service,
)

UNPARSEABLE_MESSAGE = "I couldn't quite understand that — could you rephrase?"

NO_INGREDIENT_IN_FOCUS_MESSAGE = (
    "I need an ingredient in focus to explain that — open the Chat Agent from an "
    'ingredient\'s flagged risk ("Ask why flagged").'
)

DISH_NOT_RECOGNIZED_MESSAGE = "I don't recognize that dish."

GROUNDING_SYSTEM_PROMPT = (
    "You are the Chat Agent for a kitchen manager's ingredient demand forecasting "
    "tool. You may ONLY state figures given to you in the JSON below. Never compute, "
    "estimate, or add any number not present in that JSON. If asked about something "
    "not present in the data, say plainly that you don't have that information. Reply "
    "in short, plain prose suitable for a busy kitchen manager — no markdown, no code "
    "blocks, no repeating the raw JSON back verbatim."
)

_INTENT_SYSTEM_PROMPT_TEMPLATE = (
    "You are the intent classifier for a kitchen manager's Chat Agent. Today's date is "
    "{today}. Classify the user's message into exactly one intent:\n"
    '- "explanation": the user is asking why an ingredient is flagged as at-risk '
    '(e.g. "why is this flagged?", "why is this at risk?").\n'
    '- "what_if": the user is posing a hypothetical demand change — a dish, an extra '
    'or altered serving count, and a date (e.g. "what if we sell 20 more butter '
    'chicken next Saturday?").\n'
    '- "unparseable": you cannot confidently determine either of the above.\n\n'
    'When intent is "what_if", also extract:\n'
    "- dish_name: the dish name exactly as the user wrote it.\n"
    "- extra_servings: an integer, the additional number of servings implied.\n"
    '- date: resolve any relative date phrase ("next Saturday", "tomorrow") to an '
    "absolute ISO date (YYYY-MM-DD), using today's date above as the anchor.\n"
    'When intent is "explanation" or "unparseable", omit dish_name/extra_servings/date '
    "or leave them null.\n\n"
    "Respond with ONLY the structured JSON described by the response schema — no other "
    "commentary."
)

_INTENT_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["explanation", "what_if", "unparseable"]},
        # Gemini's `response_schema` (google.genai.types.Schema) requires a
        # single `type` value, not a JSON-Schema-style `["string", "null"]`
        # union — `nullable: True` is the correct way to allow these
        # optional what-if fields to come back as null.
        "dish_name": {"type": "string", "nullable": True},
        "extra_servings": {"type": "integer", "nullable": True},
        "date": {"type": "string", "nullable": True},
    },
    "required": ["intent"],
}


@dataclass(frozen=True)
class ChatAgentResult:
    """`handle_chat_agent_request`'s return shape — mirrored one-to-one by
    `schemas/chat_agent.py::ChatAgentResponse`."""

    reply: str
    intent: str


def _classify_intent(message: str, today: date) -> dict[str, Any]:
    """One Gemini call, structured JSON output. A non-dict/unexpected
    response is treated as `"unparseable"` rather than raising — the LLM
    is untrusted input from this module's perspective."""
    system_prompt = _INTENT_SYSTEM_PROMPT_TEMPLATE.format(today=today.isoformat())
    result = llm_client.generate(system_prompt, message, response_schema=_INTENT_RESPONSE_SCHEMA)
    if isinstance(result, dict) and isinstance(result.get("intent"), str):
        return result
    return {"intent": "unparseable"}


def _narrate(question: str, data: dict[str, Any]) -> str:
    """The grounded narration call shared by both the explanation and
    what-if flows: phrases `data` (already fully computed) into a
    natural-language reply, never inventing a figure not present in it."""
    payload = json.dumps({"question": question, "data": data})
    reply = llm_client.generate(GROUNDING_SYSTEM_PROMPT, payload)
    return reply if isinstance(reply, str) else json.dumps(reply)


def _contributing_dish_shares(
    ingredient_id: int, target_date: date, db: Session
) -> list[dict[str, Any]]:
    """Each contributing dish's share of an ingredient's projected demand
    on `target_date` (ACRI-45/46/47/48): `share = contribution / total`,
    computed here in Python from
    `demand_projection_service.project_ingredient_demand`'s per-dish
    breakdown — never estimated by the LLM."""
    projection = demand_projection_service.project_ingredient_demand(ingredient_id, target_date, db)
    total = projection.total
    return [
        {
            "dish_name": dish.dish_name,
            # Rounded for display only — the underlying `dish.contribution`
            # (unrounded) is what actually drove every upstream risk
            # computation; this dict only ever reaches the LLM narration
            # step, never a computation, so rounding here doesn't violate
            # the grounding rule.
            "contribution": round(dish.contribution, 2),
            "share_of_demand_percent": round(
                (dish.contribution / total) * 100 if total > 0 else 0.0, 1
            ),
        }
        for dish in projection.contributing_dishes
    ]


def _build_explanation_data(ingredient_id: int, db: Session, today: date) -> dict[str, Any]:
    """The deterministic "explanation data" dict (ACRI-45/46/47/48) —
    built entirely in Python from the already-approved risk services,
    never via the LLM. Raises `404` (propagated from
    `evaluate_stockout_risk`) for an unknown `ingredient_id`."""
    stockout = stockout_risk_service.evaluate_stockout_risk(ingredient_id, db, anchor=today)
    spoilage = spoilage_risk_service.evaluate_spoilage_risk(ingredient_id, db, anchor=today)

    ingredient = db.get(Ingredient, ingredient_id)
    # `evaluate_stockout_risk` above already raised 404 for an unknown
    # ingredient, so this row is guaranteed to exist here.
    assert ingredient is not None

    if stockout is None and spoilage is None:
        return {
            "ingredient_name": ingredient.name,
            "flagged": False,
            "note": "This ingredient currently has neither a stockout nor a spoilage risk flagged.",
        }

    data: dict[str, Any] = {"ingredient_name": ingredient.name, "flagged": True}

    if stockout is not None:
        data["stockout"] = {
            "stockout_date": stockout.stockout_date.isoformat(),
            "order_by_date": stockout.order_by_date.isoformat(),
            "severity": stockout.severity,
            "supplier_lead_time_days": stockout.trace.get("lead_time_days"),
            "lead_time_gap": stockout.lead_time_gap,
            "safety_margin_gap": stockout.safety_margin_gap,
            "contributing_dishes": _contributing_dish_shares(
                ingredient_id, stockout.stockout_date, db
            ),
        }

    if spoilage is not None:
        data["spoilage"] = {
            "use_by_date": spoilage.use_by_date.isoformat(),
            "waste_cost_inr": round(spoilage.waste_cost_inr, 2),
            "severity": spoilage.severity,
            "suppressed": spoilage.suppressed,
            "contributing_dishes": _contributing_dish_shares(
                ingredient_id, spoilage.use_by_date, db
            ),
        }

    return data


def _resolve_dish(db: Session, dish_name: str) -> Dish | None:
    """Case-insensitive exact match against `Dish.name` (ACRI-49 AC/"I
    don't recognize that dish" path)."""
    return db.execute(
        select(Dish).where(func.lower(Dish.name) == dish_name.strip().lower())
    ).scalar_one_or_none()


def _evaluate_all_risks(
    db: Session,
    *,
    anchor: date,
    scenario_adjustments: list[demand_projection_service.ScenarioAdjustment] | None = None,
) -> dict[int, dict[str, Any]]:
    """A snapshot of every ingredient's stockout+spoilage risk (ACRI-50..52
    "before"/"after" comparison), same per-ingredient iteration shape as
    `dashboard_service.get_risk_summary`, kept local here rather than
    imported from there so this batch's what-if evaluation doesn't need to
    also build/sort `dashboard_service`'s ranked row list — this only needs
    the raw per-ingredient results."""
    ingredients = db.execute(select(Ingredient)).scalars().all()
    snapshot: dict[int, dict[str, Any]] = {}
    for ingredient in ingredients:
        snapshot[ingredient.id] = {
            "ingredient_name": ingredient.name,
            "stockout": stockout_risk_service.evaluate_stockout_risk(
                ingredient.id, db, anchor=anchor, scenario_adjustments=scenario_adjustments
            ),
            "spoilage": spoilage_risk_service.evaluate_spoilage_risk(
                ingredient.id, db, anchor=anchor, scenario_adjustments=scenario_adjustments
            ),
        }
    return snapshot


def _diff_risk_snapshots(
    baseline: dict[int, dict[str, Any]], scenario: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    """Deterministic baseline-vs-scenario diff (ACRI-50/51/52). Never
    filters the waste-exposure sum (ACRI-52, mirroring
    `dashboard_service`'s "never filter the sum" rule) — suppressed
    spoilage rows are still counted."""
    newly_at_risk: list[dict[str, Any]] = []
    order_by_date_changes: list[dict[str, Any]] = []
    baseline_waste_total = 0.0
    scenario_waste_total = 0.0

    for ingredient_id, base_entry in baseline.items():
        scenario_entry = scenario[ingredient_id]
        ingredient_name = base_entry["ingredient_name"]

        base_stockout = base_entry["stockout"]
        scenario_stockout = scenario_entry["stockout"]
        base_spoilage = base_entry["spoilage"]
        scenario_spoilage = scenario_entry["spoilage"]

        if base_spoilage is not None:
            baseline_waste_total += base_spoilage.waste_cost_inr
        if scenario_spoilage is not None:
            scenario_waste_total += scenario_spoilage.waste_cost_inr

        if base_stockout is None and scenario_stockout is not None:
            newly_at_risk.append({"ingredient_name": ingredient_name, "risk_type": "stockout"})
        if base_spoilage is None and scenario_spoilage is not None:
            newly_at_risk.append({"ingredient_name": ingredient_name, "risk_type": "spoilage"})

        if (
            base_stockout is not None
            and scenario_stockout is not None
            and base_stockout.order_by_date != scenario_stockout.order_by_date
        ):
            order_by_date_changes.append(
                {
                    "ingredient_name": ingredient_name,
                    "old_order_by_date": base_stockout.order_by_date.isoformat(),
                    "new_order_by_date": scenario_stockout.order_by_date.isoformat(),
                    "direction": (
                        "earlier"
                        if scenario_stockout.order_by_date < base_stockout.order_by_date
                        else "later"
                    ),
                }
            )

    total_waste_exposure_change_inr = scenario_waste_total - baseline_waste_total

    return {
        "newly_at_risk_ingredients": newly_at_risk,
        "order_by_date_changes": order_by_date_changes,
        # Rounded for display only (same rationale as `_contributing_dish_shares`
        # above) — `nothing_changed` below is computed from the unrounded
        # `total_waste_exposure_change_inr` so a sub-paisa float artifact can
        # never be misread as "changed" after rounding.
        "baseline_total_waste_exposure_inr": round(baseline_waste_total, 2),
        "scenario_total_waste_exposure_inr": round(scenario_waste_total, 2),
        "total_waste_exposure_change_inr": round(total_waste_exposure_change_inr, 2),
        "nothing_changed": (
            not newly_at_risk
            and not order_by_date_changes
            and total_waste_exposure_change_inr == 0.0
        ),
    }


def _handle_what_if(
    message: str, params: dict[str, Any], db: Session, today: date
) -> ChatAgentResult:
    """ACRI-49..52. Falls back to unparseable/"don't recognize" messages
    without ever calling the narration LLM when the extracted params
    don't resolve to something computable."""
    dish_name = params.get("dish_name")
    extra_servings_raw = params.get("extra_servings")
    date_str = params.get("date")

    if not isinstance(dish_name, str) or not dish_name.strip():
        return ChatAgentResult(reply=UNPARSEABLE_MESSAGE, intent="unparseable")
    if extra_servings_raw is None or not isinstance(date_str, str) or not date_str.strip():
        return ChatAgentResult(reply=UNPARSEABLE_MESSAGE, intent="unparseable")

    try:
        extra_servings = int(extra_servings_raw)
        scenario_date = date.fromisoformat(date_str.strip())
    except (TypeError, ValueError):
        return ChatAgentResult(reply=UNPARSEABLE_MESSAGE, intent="unparseable")

    dish = _resolve_dish(db, dish_name)
    if dish is None:
        return ChatAgentResult(reply=DISH_NOT_RECOGNIZED_MESSAGE, intent="what_if")

    baseline = _evaluate_all_risks(db, anchor=today)
    adjustment = demand_projection_service.ScenarioAdjustment(
        dish_id=dish.id, date=scenario_date, extra_servings=extra_servings
    )
    scenario = _evaluate_all_risks(db, anchor=today, scenario_adjustments=[adjustment])
    diff = _diff_risk_snapshots(baseline, scenario)

    narration_data = {
        "scenario": {
            "dish_name": dish.name,
            "extra_servings": extra_servings,
            "date": scenario_date.isoformat(),
        },
        "diff": diff,
    }
    reply = _narrate(message, narration_data)
    return ChatAgentResult(reply=reply, intent="what_if")


def handle_chat_agent_request(
    message: str, ingredient_id: int | None, db: Session
) -> ChatAgentResult:
    """`POST /chat-agent/ask`'s single entry point (REQ-036). Raises
    `HTTPException(503)` (propagated from `llm_client.generate`) when
    `GEMINI_API_KEY` is not configured, and `HTTPException(404)`
    (propagated from the risk services) for an unknown `ingredient_id`."""
    today = date.today()
    classification = _classify_intent(message, today)
    intent = classification.get("intent")
    if intent not in ("explanation", "what_if", "unparseable"):
        intent = "unparseable"

    if intent == "unparseable":
        return ChatAgentResult(reply=UNPARSEABLE_MESSAGE, intent="unparseable")

    if intent == "explanation":
        if ingredient_id is None:
            return ChatAgentResult(reply=NO_INGREDIENT_IN_FOCUS_MESSAGE, intent="explanation")
        data = _build_explanation_data(ingredient_id, db, today)
        reply = _narrate(message, data)
        return ChatAgentResult(reply=reply, intent="explanation")

    return _handle_what_if(message, classification, db, today)
