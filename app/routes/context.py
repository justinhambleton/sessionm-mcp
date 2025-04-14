from fastapi import APIRouter, HTTPException, Header, Query
from app.services.sessionm import resolve_user_context
from app.auth import verify_jwt_token
from app.models import MemberContext

router = APIRouter()

@router.get("/user", response_model=MemberContext)
async def get_user_context(
    user_id: str = Query(None),
    email: str = Query(None),
    phone: str = Query(None),
    authorization: str = Header(...)
):
    token = authorization.split(" ")[-1]
    agent_info = verify_jwt_token(token)

    if "read_context" not in agent_info.get("scopes", []):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if user_id:
        lookup_type = "user_id"
        identifier = user_id
    elif email:
        lookup_type = "email"
        identifier = email
    elif phone:
        lookup_type = "phone"
        identifier = phone
    else:
        raise HTTPException(status_code=400, detail="Must provide user_id, email, or phone.")

    try:
        context = await resolve_user_context(identifier=identifier, type=lookup_type)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
