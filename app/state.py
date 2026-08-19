from typing import Dict, TypedDict
from typing import Annotated
from app.schema import OrderResponse, ApprovalStatus

def add(left: list[Dict], right: list[Dict]) -> list[Dict]:
    return left + right

class AgentState(TypedDict):
    messages: Annotated[list[Dict], add]
    agent_node_execution_count: int
    tool_node_execution_count: int
    hitl_node_execution_count: int
    approval_status: ApprovalStatus | None
    order_response: OrderResponse | None