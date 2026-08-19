from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from app.state import AgentState
from app.nodes import agent_node, tool_node, route_tools, hitl_node, order_api_node

checkpointer = InMemorySaver()

builder = StateGraph(AgentState)

builder.add_node("agent_node", agent_node)
builder.add_node("tool_node", tool_node)
builder.add_node("hitl_node", hitl_node)
builder.add_node("order_api_node", order_api_node)

builder.add_edge(START, "agent_node")
builder.add_conditional_edges("agent_node", route_tools, {"tool_node": "tool_node", "hitl_node": "hitl_node", "END": END})
builder.add_edge("tool_node", "agent_node")
builder.add_edge("hitl_node", "order_api_node")
builder.add_edge("order_api_node", END)

graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    # Generate PNG
    png_bytes = graph.get_graph().draw_mermaid_png()

    with open("boba_tea_graph.png", "wb") as f:
        f.write(png_bytes)