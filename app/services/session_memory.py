# This is a placeholder - prod will use Redis
session_store = {}

class ChatSessionManager:
    @staticmethod
    def get(session_id: str):
        return session_store.get(session_id, {})

    @staticmethod
    def set_user(session_id: str, user_id: str, context: dict):
        session_store[session_id] = {
            "user_id": user_id,
            "context": context
        }

    @staticmethod
    def get_user_id(session_id: str):
        return session_store.get(session_id, {}).get("user_id")

    @staticmethod
    def get_context(session_id: str):
        return session_store.get(session_id, {}).get("context")
