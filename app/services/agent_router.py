from app.services.session_memory import ChatSessionManager
from app.services.sessionm import resolve_user_context, generate_summary

async def refresh_user_context(session_id: str):
    user_id = ChatSessionManager.get_user_id(session_id)
    if not user_id:
        return None
    ctx = await resolve_user_context(identifier=user_id, type="user_id")
    ChatSessionManager.set_user(session_id, ctx.member_id, ctx.model_dump())
    return ctx.model_dump()

async def handle_agent_prompt(session_id: str, intent: str, value: str = None) -> dict:
    if intent == "identify_user":
        ctx = await resolve_user_context(identifier=value, type="email" if "@" in value else "phone")
        ChatSessionManager.set_user(session_id, ctx.member_id, ctx.model_dump())
        return {"summary": generate_summary(ctx), "context": ctx}

    context = await refresh_user_context(session_id)

    if not context:
        return {"error": "User not identified. Please provide an email or phone."}

    if intent == "get_point_balance":
        return {"summary": f"You have {int(context['total_points']):,} points."}

    elif intent == "get_active_campaigns":
        campaigns = context.get("campaigns", [])
        return {
            "summary": f"You are enrolled in {len(campaigns)} campaign(s).",
            "campaigns": campaigns
        }

    elif intent == "get_active_offers":
        offers = context.get("offers", [])
        return {
            "summary": f"You have {len(offers)} active offer{'s' if len(offers) != 1 else ''}.",
            "offers": offers
        }

    elif intent == "get_offer_expiry":
        offers = context.get("offers", [])
        if not offers:
            return { "summary": "You have no active offers to check expiration for." }
        offer = offers[0]
        expires = offer.get("expiration_date") or "an unknown time"
        return {
            "summary": f'Your offer "{offer["name"]}" expires on {expires}.'
        }

    elif intent == "show_offers":
        offers = context.get("offers", [])
        if not offers:
            return { "summary": "You don't have any active offers to display." }

        summary = "Here are your active offers:\n\n"
        for offer in offers:
            summary += f'• {offer["name"]} – {offer["description"]}\n'
            if offer.get("start_date") or offer.get("expiration_date"):
                summary += f'  ⏱ {offer.get("start_date") or ""} → {offer.get("expiration_date") or "no end date"}\n'

        return { "summary": summary.strip(), "offers": offers }

    elif intent == "show_campaigns":
        campaigns = context.get("campaigns", [])
        if not campaigns:
            return { "summary": "You don't have any active campaigns to display." }

        summary = "Here are your active campaigns:\n\n"
        for c in campaigns:
            summary += f'• {c["name"]} – {c["description"]}\n'
            if c.get("start_date") or c.get("end_date"):
                summary += f'  📅 {c.get("start_date") or ""} → {c.get("end_date") or "no end date"}\n'

        return { "summary": summary.strip(), "campaigns": campaigns }

    return {"error": f"Unknown intent: {intent}"}
