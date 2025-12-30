"""Graph definitions for MACSDK chatbots.

This module defines the LangGraph workflow builder for chatbots,
supporting both CLI (interactive) and web (single-query) modes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal

from langgraph.graph import END, START, StateGraph

from ..agents.formatter import formatter_node
from ..agents.supervisor import supervisor_agent_node
from .state import ChatbotState

if TYPE_CHECKING:
    from langgraph.graph.graph import CompiledGraph


def should_exit(state: ChatbotState) -> Literal["exit", "continue"]:
    """Check if user wants to exit.

    Args:
        state: Current chatbot state.

    Returns:
        "exit" if user typed exit, "continue" otherwise.
    """
    user_query = state.get("user_query", "")
    if user_query.strip().lower() == "exit":
        return "exit"
    return "continue"


def create_chatbot_graph(
    register_agents_func: Callable[[], None] | None = None,
    debug: bool | None = None,
) -> "CompiledGraph":
    """Create chatbot graph for CLI with interactive loop.

    The graph flow is:
    START -> supervisor -> formatter -> END

    Args:
        register_agents_func: Optional function to register agents.
            This function will be called before processing each query.
        debug: Whether to enable debug mode (shows prompts). If None, uses config.

    Returns:
        Compiled graph for CLI usage.
    """
    graph_builder: StateGraph[ChatbotState] = StateGraph(ChatbotState)

    # Create supervisor node with agent registration
    async def supervisor_node(state: ChatbotState) -> ChatbotState:
        return await supervisor_agent_node(state, register_agents_func, debug=debug)

    # Add nodes
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("formatter", formatter_node)

    # Define conditional routing from supervisor
    def route_after_supervisor(state: ChatbotState) -> Literal["formatter", "end"]:
        """Route to formatter only if explicitly requested."""
        step = state.get("workflow_step", "")
        if step == "format":
            return "formatter"
        return "end"

    # Flow: START -> supervisor -> (formatter OR end) -> END
    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"formatter": "formatter", "end": END},
    )
    graph_builder.add_edge("formatter", END)

    return graph_builder.compile()


def create_web_chatbot_graph(
    register_agents_func: Callable[[], None] | None = None,
    debug: bool | None = None,
) -> "CompiledGraph":
    """Create chatbot graph for web interface (single query mode).

    The web graph is simpler - just processes one query and returns.

    Args:
        register_agents_func: Optional function to register agents.
        debug: Whether to enable debug mode (shows prompts). If None, uses config.

    Returns:
        Compiled graph for web usage.
    """
    # Web graph is identical to CLI graph in current implementation
    return create_chatbot_graph(register_agents_func, debug=debug)
