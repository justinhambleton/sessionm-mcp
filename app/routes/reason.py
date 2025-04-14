from fastapi import APIRouter, Header, Query, HTTPException
from app.auth import verify_jwt_token
from app.services.session_memory import ChatSessionManager
from app.services.agent_reasoner import run_reasoning_agent

router = APIRouter()

@router.post("/context/reason")
async def reasoning_chat(
    prompt: str = Query(...),
    session_id: str = Header(..., alias="Session-Id"),
    authorization: str = Header(...)
):
    print("REASON prompt:", prompt)
    print("Session ID:", session_id)

    token = authorization.split(" ")[-1]
    agent_info = verify_jwt_token(token)

    if "read_context" not in agent_info.get("scopes", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    context = ChatSessionManager.get_context(session_id)
    if not context:
        raise HTTPException(status_code=400, detail="User not identified in session.")

    try:
        result = await run_reasoning_agent(prompt, context)
        return {
            "response": {
                "summary": result["summary"],
                "steps": result["steps"]
            },
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent reasoning failed: {str(e)}")
