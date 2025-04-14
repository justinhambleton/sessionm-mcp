import os
import re
import json
from pydantic import BaseModel
from app.models import MemberContext
from fastapi import APIRouter, Header, Query, HTTPException
from app.auth import verify_jwt_token
from app.services.session_memory import ChatSessionManager
from app.services.sessionm import generate_summary, resolve_user_context
from openai import OpenAI

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/context/freeform")
async def freeform_chat(
    prompt: str = Query(...),
    session_id: str = Header(..., alias="Session-Id"),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[-1]
    agent_info = verify_jwt_token(token)

    if "read_context" not in agent_info.get("scopes", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    context = ChatSessionManager.get_context(session_id)

    try:
        if not context:
            print("🟡 No context found, checking if prompt is an identifier...")
            if re.search(r"@|^\d{6,}$", prompt):
                id_type = "email" if "@" in prompt else "phone"
                print(f"🔍 Attempting to resolve via {id_type}: {prompt}")
                context = await resolve_user_context(prompt, id_type)
                ChatSessionManager.set_user(session_id, context.member_id, context.dict())
            else:
                raise HTTPException(status_code=400, detail="User not identified in session.")

        system_prompt = (
            "You are a helpful assistant specializing in loyalty program data.\n"
            "You have access to the following member profile.\n"
            "Only use this data to answer questions. If information is missing, say so.\n"
        )
        if isinstance(context, MemberContext):
            context_dict = context.dict()
        else:
            context_dict = context

        user_prompt = f"Prompt: {prompt}\n\nMemberContext:\n{json.dumps(context_dict, indent=2)}"

        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return {
            "response": {
                "summary": response.choices[0].message.content.strip(),
                "context": context,
                "mode": "freeform"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Freeform reasoning failed: {str(e)}")
