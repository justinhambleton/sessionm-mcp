import os
from typing import Optional

def get_jwt_secret() -> str:
    # Load JWT secret from environment variable or fallback file
    secret = os.getenv("JWT_SECRET")
    if not secret:
        # Optionally, load from a .env or config file
        raise RuntimeError("JWT_SECRET environment variable not set!")
    return secret

def get_jwt_algorithm() -> str:
    # Default to HS256
    return os.getenv("JWT_ALGORITHM", "HS256")

def get_jwt_audience() -> Optional[str]:
    return os.getenv("JWT_AUDIENCE")
