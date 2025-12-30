"""CLI interface for MACSDK chatbots.

This module provides a ready-to-use command-line interface for
interactive chatbot sessions.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from ..core.state import ChatbotState

if TYPE_CHECKING:
    from langgraph.graph.graph import CompiledGraph


def create_initial_state() -> ChatbotState:
    """Create the initial chatbot state.

    Returns:
        A fresh ChatbotState with empty values.
    """
    return {
        "messages": [],
        "user_query": "",
        "chatbot_response": "",
        "workflow_step": "query",
        "agent_results": "",
    }


def run_cli_chatbot(
    graph: "CompiledGraph",
    title: str = "MACSDK Chatbot",
    example_queries: list[str] | None = None,
) -> None:
    """Run an interactive chatbot CLI.

    This function starts an interactive loop where the user can
    ask questions and receive responses from the multi-agent system.

    Args:
        graph: The compiled chatbot graph to run.
        title: Title to display at startup.
        example_queries: Optional list of example queries to show.
    """
    print(title)
    print("Type 'exit' to quit")

    if example_queries:
        print("Try asking:")
        for query in example_queries:
            print(f"  - '{query}'")
    print()

    async def run_async() -> None:
        state = create_initial_state()

        while True:
            try:
                # Get user input
                user_input = input(">> You: ")

                # Check for exit
                if user_input.strip().lower() == "exit":
                    print("\nBye!")
                    break

                if not user_input.strip():
                    continue

                # Update state with user query
                state["user_query"] = user_input
                state["messages"] = state.get("messages", []) + [
                    HumanMessage(content=user_input)
                ]
                state["workflow_step"] = "processing"

                # Run the graph
                async for chunk in graph.astream(
                    state, stream_mode=["values", "custom"]
                ):
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        stream_mode_type, stream_data = chunk
                        if stream_mode_type == "custom":
                            # Print progress messages
                            if isinstance(stream_data, str):
                                print(stream_data, end="", flush=True)
                            elif isinstance(stream_data, dict):
                                for key, value in stream_data.items():
                                    if isinstance(value, str):
                                        print(value, end="", flush=True)
                        elif stream_mode_type == "values":
                            # Update state with final values
                            if isinstance(stream_data, dict):
                                state.update(stream_data)  # type: ignore[typeddict-item]

                # Print the response
                response = state.get("chatbot_response", "")
                if response:
                    print(f"\n>> Chatbot:\n{response}\n")

            except KeyboardInterrupt:
                print("\n\nBye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")

    try:
        asyncio.run(run_async())
    except KeyboardInterrupt:
        print("\n\nBye!")
    except Exception as e:
        print(f"\nError: {e}\n")
        print("\nBye!")
