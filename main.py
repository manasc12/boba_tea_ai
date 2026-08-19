from dotenv import load_dotenv
from langgraph.types import Command

from app.schema import ApprovalStatus, OrderResponse

load_dotenv()

from app.graph import graph
from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def main() -> None:
    """Run the interactive Boba Tea AI assistant."""
    console.print(
        Panel.fit(
            "[bold magenta]Boba Tea AI[/bold magenta]",
            title="Welcome",
            border_style="magenta",
        )
    )

    config = {"configurable": {"thread_id": "1"}}

    while True:
        query = console.input("[bold green]User:[/bold green] ")
        if query.lower().strip() in {"exit", "quit"}:
            console.print("[yellow]Exiting the application.[/yellow]")
            break

        with console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
            state = graph.invoke(
                {"messages": [HumanMessage(content=query)]},
                config=config,
            )
        # PRINT LAST MESSAGE
        last_message = state["messages"][-1]
        content = getattr(last_message, "content", str(last_message))
        console.print(Panel(Markdown(content), title="Assistant", title_align="left", border_style="blue"))

        # HUMAN INPUT LOOP FOR APPROVAL OR REJECTION OF ORDER
        if state.get("approval_status") == ApprovalStatus.PENDING and state.get("order_response") is not None:
            order_response: OrderResponse = state["order_response"]
            console.print(f"[bold cyan]Order ID: {order_response.order_id}[/bold cyan]")
            console.print(f"[bold cyan]Order Status: {order_response.status.value}[/bold cyan]")
            console.print(f"[bold cyan]Total Price: {order_response.total_price} EUR[/bold cyan]")
            console.print("[bold cyan]Please review the order details above.[/bold cyan]")

            console.print("[bold cyan] \n⚠️ Your Order requires approval.[/bold cyan]")
            user_input: str | None = None
            while user_input is None or user_input.lower() not in {"yes", "no", "y", "n","exit", "quit", "approve", "reject"}:
                user_input = console.input(
                    "[bold cyan]Approve order? (yes/no): [/bold cyan]"
                )
                if user_input.lower() in {"exit", "quit"}:
                    console.print("[yellow]Exiting the application.[/yellow]")
                    return
                elif user_input.lower() in {"approve", "yes", "y"}:
                    user_input = "yes"
                elif user_input.lower() in {"reject", "no", "n"}:
                    user_input = "no"
                else:
                    console.print("[bold red]Invalid input. Please enter 'yes' or 'no'.[/bold red]")

            # HITL RESUME
            print("DEBUG Command:", Command)
            print("DEBUG Command type:", type(Command))
            print("DEBUG ApprovalStatus:", ApprovalStatus)
            print("DEBUG ApprovalStatus type:", type(ApprovalStatus))
            print("DEBUG Approved:", ApprovalStatus.APPROVED)

            with console.status("[bold blue]Resuming...[/bold blue]", spinner="dots"):
                if user_input.lower() == "yes":
                    state = graph.invoke(
                        Command(resume=ApprovalStatus.APPROVED),
                        config=config
                    )

                else:

                    state = graph.invoke(
                        Command(resume=ApprovalStatus.REJECTED),
                        config=config
                    )

            # PRINT LAST MESSAGE
            last_message = state["messages"][-1]
            content = getattr(last_message, "content", str(last_message))
            console.print(Panel(Markdown(content), title="Assistant", title_align="left", border_style="blue"))
            break # After Order is successfully placed or cancelled we can break the loop and exit the application. 


if __name__ == "__main__":
    main()
