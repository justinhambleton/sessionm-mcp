def verify_jwt_token(token: str) -> dict:
    # Mocked agent verification for MVP
    return {
        "agent_id": "example-agent",
        "scopes": ["read_context"]
    }