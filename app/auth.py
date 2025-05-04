import jwt
from fastapi import HTTPException, status
from jwt import PyJWTError, ExpiredSignatureError
from app.auth_settings import get_jwt_secret, get_jwt_algorithm, get_jwt_audience

def verify_jwt_token(token: str) -> dict:
    """
    Verifies a JWT Bearer token and returns agent info dict if valid.
    Raises HTTPException if invalid or missing required claims.
    """
    try:
        options = {"verify_aud": get_jwt_audience() is not None}
        decoded = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[get_jwt_algorithm()],
            audience=get_jwt_audience(),
            options=options
        )
        agent_id = decoded.get("sub") or decoded.get("agent_id")
        scopes = decoded.get("scopes") or decoded.get("scope")
        if isinstance(scopes, str):
            scopes = scopes.split()
        if not agent_id or not scopes:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT missing required claims")
        return {"agent_id": agent_id, "scopes": scopes}
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT token expired")
    except PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"JWT validation error: {str(e)}")