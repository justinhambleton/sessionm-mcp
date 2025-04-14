from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from app.services.agent_tools import *

class AgentState(dict):
    prompt: str
    context: Dict[str, Any]
    result: str | None
    steps: List[str]

async def route_node(state: AgentState) -> str:
    prompt = state["prompt"].lower()

    if "expired" in prompt:
        return "expired"
    elif "spent" in prompt:
        return "spent"
    elif "earned" in prompt:
        return "earned"
    elif "by account" in prompt or "account" in prompt:
        return "account_summary"
    elif "offer" in prompt and ("most" in prompt or "best" in prompt) and ("valuable" in prompt or "value" in prompt):
        return "most_valuable_offer"
    elif "tier" in prompt or "points" in prompt:
        return "points"
    elif "offers" in prompt:
        return "offers"
    elif "campaign" in prompt and ("end" in prompt or "expires" in prompt):
        return "soonest_campaign"
    elif "purchases" in prompt and "last" in prompt:
        return "recent_purchases"
    elif "points" in prompt and "spent" in prompt and "month" in prompt:
        return "points_spent_this_month"
    else:
        return "fallback"

def make_node(tool_func, label: str):
    async def node(state: AgentState) -> AgentState:
        result = tool_func(state["context"])
        return {
            **state,
            "result": result,
            "steps": state.get("steps", []) + [label]
        }
    return node

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("points", RunnableLambda(make_node(get_point_summary, "get_point_summary")))
    graph.add_node("earned", RunnableLambda(make_node(get_total_earned_points, "get_total_earned_points")))
    graph.add_node("spent", RunnableLambda(make_node(get_total_spent_points, "get_total_spent_points")))
    graph.add_node("expired", RunnableLambda(make_node(get_total_points_expired, "get_total_points_expired")))
    graph.add_node("account_summary", RunnableLambda(make_node(get_points_by_account, "get_points_by_account")))
    graph.add_node("offers", RunnableLambda(make_node(summarize_offers, "summarize_offers")))
    graph.add_node("most_valuable_offer", RunnableLambda(make_node(get_most_valuable_offer, "get_most_valuable_offer")))
    graph.add_node("soonest_campaign", RunnableLambda(make_node(get_soonest_campaign, "get_soonest_campaign")))
    graph.add_node("fallback", RunnableLambda(lambda s: {**s, "result": "Sorry, I didn’t understand the request.", "steps": s.get("steps", []) + ["fallback"]}))
    graph.add_node("recent_purchases", RunnableLambda(make_node(get_recent_purchases, "get_recent_purchases")))
    graph.add_node("points_spent_this_month", RunnableLambda(make_node(get_points_spent_this_month, "get_points_spent_this_month")))

    graph.set_conditional_entry_point(route_node)
    for node in [
      "points", "earned", "spent", "expired", "account_summary",
      "offers", "most_valuable_offer", "soonest_campaign", "recent_purchases",
      "points_spent_this_month", "fallback"
    ]:
        graph.add_edge(node, END)

    return graph.compile()

compiled_graph = build_graph()

async def run_reasoning_agent(prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    result_state = await compiled_graph.ainvoke({
        "prompt": prompt,
        "context": context,
        "result": None,
        "steps": []
    })
    return {
        "summary": result_state["result"],
        "steps": result_state["steps"]
    }
