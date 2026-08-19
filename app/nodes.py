from dotenv import load_dotenv

load_dotenv()

from app.state import AgentState
from langchain_openai import ChatOpenAI
from app.prompts import SYSTEM_PROMPT
from app.database import DATABASE_PATH, init_database
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from app.schema import Order, OrderResponse, ApprovalStatus
from langgraph.types import interrupt, Command

@tool
def search_menu() -> list[dict]:
    """Returns the available boba tea menu items from the database.

    Fetches products from the Product table and joins with ProductPriceSize
    to collect each product's available sizes and prices.

    Returns:
        list[dict]: A list of menu items, each containing the product's name,
            category, description, and a list of size/price options.
    """
    products: dict[int, dict] = {}
    with init_database(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
                """
                SELECT DISTINCT
                    p.product_id,
                    p.name,
                    p.category,
                    p.description,
                    pps.size,
                    pps.price
                FROM Product p
                JOIN ProductPriceSize pps ON p.product_id = pps.product_id
                ORDER BY p.product_id, pps.price
                """
            )
        
        for row in cursor.fetchall():
            product_id, name, category, description, size, price = row
            if product_id not in products:
                products[product_id] = {
                    "product_id": product_id,
                    "name": name,
                    "category": category,
                    "description": description,
                    "options": [],
                }
            products[product_id]["options"].append({"size": size, "price": price})
    return list(products.values())

@tool
def create_order(orders: list[Order]) -> OrderResponse:
    """Creates a new order with the given details.

    Args:
        orders (list[Order]): A list of orders, each containing the
            product ID, price, size, and quantity of the item to order.

    Returns:
        OrderResponse: The created order's response, including order ID,
            status, and total price.
    """
    with init_database(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        total_price=0
        orders_list: list[dict] = []
        max_order_id = cursor.execute(
                    """ SELECT MAX(order_id) FROM OrderResponse"""
                ).fetchone()[0]
        current_order_id = max_order_id + 1 if max_order_id is not None else 1
        for order in orders:
            total_price += order.price * order.quantity
            order_details = {
                "order_id": current_order_id,  # OrderDetails table Will be populated with these information
            }
            order_details.update(order.model_dump()) # OrderDetails table Will be populated with these information
            orders_list.append(order_details) # OrderDetails table Will be populated with these information
        
        orderResponse=OrderResponse(order_id=current_order_id, status=ApprovalStatus.PENDING, total_price=total_price)
        cursor.execute(
            """
            INSERT INTO OrderResponse (order_id, status, total_price)
            VALUES (?, ?, ?)
            """,
            (orderResponse.order_id, orderResponse.status.value, orderResponse.total_price),
        )
        cursor.executemany(
            """
            INSERT INTO OrderDetails (order_id, product_id, price, size, quantity)
            VALUES (:order_id, :product_id, :price, :size, :quantity)
            """,
            orders_list
        )

        conn.commit()

    return orderResponse

# @tool
# def order_api(order_details: dict) -> dict:
#     """Placeholder API tool for external order processing.

#     Args:
#         order_details (dict): Details of the order to process.

#     Returns:
#         dict: An empty response placeholder.
#     """
#     return {}

# @tool
# def recommend_drinks() -> list[dict]:
#     """Returns drink recommendations.

#     Returns:
#         list[dict]: A list of recommended drink items.
#     """
#     return []

llm = ChatOpenAI(model="gpt-5.6-luna", temperature=0, max_tokens=300, timeout=30, reasoning_effort="none",)

llm_with_tools = llm.bind_tools([search_menu, create_order])

def agent_node(state: AgentState) -> AgentState:
    """Invokes the LLM with the current conversation messages.

    The LLM is bound to the `search_menu` tool, so it can decide whether to
    call the tool based on the user's input.

    Args:
        state (AgentState): The current agent state, containing at least
            a "messages" key with the conversation history.

    Returns:
        AgentState: The updated state with the LLM's response appended to
            "messages". This may be a plain assistant message or a tool call.
    """
    if state.get("order_response", None) is None:
        print("Agent node executed")
        agent_node_execution_count = state.get("agent_node_execution_count", 0) + 1
        system_prompt = [{"role": "system", "content": SYSTEM_PROMPT}]
        response = llm_with_tools.invoke(system_prompt + state["messages"]) 
        # to-do: Once the order is created below things has to be implemented:
        # 1. llm_invokation won't happen in this case - Done
        # 2. include appropriate fields in the graph state to capture order details (This should be done at tool_node) Done
        # 3. We can then easily check if the Order has been created or not here and then we can totally avoid llm_model_invokation (This should be done at agent_node) Done
        # 4. We can then literally do nothing here and just add an AI Message that Order has been created, rerouting to HITL Node for approval or cancellation of the order. (This should be done at agent_node) Done
        # 5. At HITL Node we can present the Order Details to the user with different colors and ask for approval or cancellation of the order in the main code in different colors. (This should be done at hitl_node and main.py respectively) Done
        # 6. Based on Approval or Cancellation, we can then update the Order Status in the database and then return the final response to the user(This can be done at order_api_node - We can just add another Nicely formatted AI Message in the end to the state["messages"] regarding the Order Status and then we can end the graph execution) Done
        # 7. update the route_tools conditional edge function to check if the order has been created or not and then route to HITL Node for approval or cancellation of the order. (This should be done at route_tools) Done
        # 8. Extend the graph and Connect the edges to hitl_node, order_api_node and END Done
        # 9. Then the graph will END Done
    else:
        print("Agent node executed but without LLM invokation as Order already created!")
        agent_node_execution_count = state.get("agent_node_execution_count", 0)
        response = AIMessage(content="Your order has been created! Please proceed to the next step for approval or cancellation.")

    return {
        "messages": [response],
        "agent_node_execution_count": agent_node_execution_count
    }


def tool_node(state: AgentState) -> AgentState:
    """Executes tool calls requested by the agent.

    Iterates over the last message's tool calls, invokes the matching
    tools by name, and returns the results as ToolMessages.

    Args:
        state (AgentState): The current agent state, containing at least
            a "messages" key. The last message is expected to contain
            tool_calls.

    Returns:
        AgentState: The updated state with tool result messages appended
            to "messages".
    """
    tool_node_execution_count = state.get("tool_node_execution_count", 0)
    available_tools = {
        "search_menu": search_menu,
        "create_order": create_order,
    }

    last_message = state["messages"][-1]
    tool_outputs = []
    order_response: OrderResponse | None = None
    approval_status: ApprovalStatus | None = None
    
    for tool_call in last_message.tool_calls:
        print("Tool node executed")
        tool_node_execution_count += 1
        tool_name = tool_call["name"]
        tool_id = tool_call["id"]
        tool_args = tool_call.get("args", {})

        if tool_name not in available_tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_result = available_tools[tool_name].invoke(tool_args)
        tool_outputs.append(
            ToolMessage(content=str(tool_result), tool_call_id=tool_id)
        )
        if tool_name == "create_order":
            order_response = tool_result
            approval_status = ApprovalStatus.PENDING

    return {
        "messages": tool_outputs,
        "tool_node_execution_count": tool_node_execution_count,
        "order_response": order_response,
        "approval_status": approval_status
    }

def hitl_node(state: AgentState) -> AgentState:
    """Handles human-in-the-loop (HITL) interactions.

    Args:
        state (AgentState): The current agent state

    Returns:
        AgentState: The updated state after HITL processing.
    """
    print("HITL node executed")
    hitl_node_execution_count = state.get("hitl_node_execution_count", 0) + 1
    approval_status: ApprovalStatus = interrupt(
        {
            "message": "Your Order is created! Do you approve of this order?",
            "order_id": getattr(state.get("order_response", None), "order_id", None),
            "total_price": getattr(state.get("order_response",None),"total_price",None),
            "items": ["Items in the order will be displayed here."],
        }
    )
    human_msg_content = (
        f"Human approval status of this order: {'Approved' if approval_status==ApprovalStatus.APPROVED else 'Rejected'}"
    )
    return {
        "messages": [HumanMessage(content=human_msg_content)],
        "hitl_node_execution_count": hitl_node_execution_count,
        "approval_status": approval_status,  # Placeholder for actual approval logic
    }

def order_api_node(state: AgentState) -> AgentState:
    """Handles the final order processing based on human approval.

    Args:
        state (AgentState): The current agent state, containing the
            approval status and order response.

    Returns:
        AgentState: The updated state after order processing.
    """
    print("Order API node executed")
    approval_status = state.get("approval_status")
    order_response = state.get("order_response")

    if approval_status == ApprovalStatus.APPROVED and order_response:
        # Update the order status in the database to APPROVED
        with init_database(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE OrderResponse
                SET status = ?
                WHERE order_id = ?
                """,
                (ApprovalStatus.APPROVED.value, order_response.order_id),
            )
            conn.commit()
        final_message_content = (
            f"Your order is placed Order ID: {order_response.order_id} \n\n---\n\n"
            f"You will need this Order ID to collect your Order! \n\n"
            f"Total Price: {order_response.total_price} EUR \n\n"
            f"Please have patience, your order will be ready soon! \n\n"
            f"Thank you for choosing our Boba Tea AI service! Enjoy your drink!"
        )
    elif approval_status == ApprovalStatus.REJECTED and order_response:
        # Update the order status in the database to REJECTED
        with init_database(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE OrderResponse
                SET status = ?
                WHERE order_id = ?
                """,
                (ApprovalStatus.REJECTED.value, order_response.order_id),
            )
            conn.commit()
        final_message_content = (
            f"Your order Order ID: {order_response.order_id} of Price {order_response.total_price} EUR has been cancelled, you will not be charged.\n\n"
            f"Thank you for choosing our Boba Tea AI service!"
        )
    else:
        final_message_content = "No valid order to process."

    return {
        "messages": [AIMessage(content=final_message_content)],
    }

def route_tools(state: AgentState) -> str:
    """Routes back to the agent if the last message contains tool calls.

    Otherwise, ends the loop so the final assistant response is returned.

    Args:
        state (AgentState): The current agent state.

    Returns:
        str: The next node name ("tool_node" or END).
    """
    last_message = state["messages"][-1]
    if state.get("approval_status") is not None and state.get("order_response") is not None:
        return "hitl_node"
    elif last_message.tool_calls:
        return "tool_node"
    return "END"