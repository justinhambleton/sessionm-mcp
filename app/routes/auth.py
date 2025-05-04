from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from app.auth_settings import get_jwt_secret, get_jwt_algorithm, get_jwt_audience

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
def login(data: LoginRequest):
    # TODO: Replace this with your actual authentication logic
    # For demonstration, accept any username/password where username == password
    if data.username != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": data.username,
        "scopes": ["read_context"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    aud = get_jwt_audience()
    if aud:
        payload["aud"] = aud
    token = jwt.encode(payload, get_jwt_secret(), algorithm=get_jwt_algorithm())
    return {"access_token": token}
