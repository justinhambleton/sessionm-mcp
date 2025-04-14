from fastapi import APIRouter, HTTPException, Header, Query
from app.auth import verify_jwt_token
from app.models import MemberContext
from app.services.langchain_resolver import extract_intent_and_value
from app.services.sessionm import resolve_user_context, generate_summary
from app.services.agent_router import handle_agent_prompt

router = APIRouter()

@router.post("/context/chat")
async def chat_lookup(
    prompt: str = Query(...),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[-1]
    agent_info = verify_jwt_token(token)
    if "read_context" not in agent_info.get("scopes", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await extract_intent_and_value(prompt)

    if not result.get("type") or not result.get("value"):
        raise HTTPException(status_code=400, detail="Could not extract identifier.")

    context = await resolve_user_context(identifier=result["value"], type=result["type"])
    summary = generate_summary(context)

    return {
        "summary": summary,
        "context": context
    }

@router.post("/context/agent")
async def agent_chat(
    prompt: str = Query(...),
    session_id: str = Header(...),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[-1]
    agent_info = verify_jwt_token(token)

    if "read_context" not in agent_info.get("scopes", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    parsed = await extract_intent_and_value(prompt)

    if not parsed.get("intent"):
        raise HTTPException(status_code=400, detail="Could not parse intent")

    result = await handle_agent_prompt(session_id, parsed["intent"], parsed.get("value"))
    return {
        "intent": parsed["intent"],
        "response": result
    }
