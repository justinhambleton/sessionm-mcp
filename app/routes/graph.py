# === In app/routes/graph.py ===

from fastapi import APIRouter, Response
from app.services.agent_reasoner import compiled_graph

router = APIRouter()

@router.get("/graph/state", response_class=Response)
def get_state_graph():
    dot = compiled_graph.get_graph().to_dot()
    return Response(content=dot, media_type="text/plain")