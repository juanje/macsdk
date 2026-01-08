"""Intelligent Supervisor Agent implementation.

This module provides the supervisor agent that orchestrates
specialist agents using them as tools.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.config import get_stream_writer

from ...core.config import config
from ...core.llm import get_answer_model
from ...core.registry import get_all_agent_tools, get_all_capabilities
from ...core.utils import STREAM_WRITER_KEY, extract_text_content, log_progress
from ...middleware import (
    DatetimeContextMiddleware,
    SummarizationMiddleware,
)
from ...middleware.debug_prompts import PromptDebugMiddleware
from .prompts import SUPERVISOR_PROMPT

logger = logging.getLogger(__name__)  # noqa: E402

if TYPE_CHECKING:
    from ...core.state import ChatbotState


def _build_supervisor_prompt() -> str:
    """Build the supervisor prompt with agent capabilities.

    Returns:
        The formatted supervisor prompt with all agent capabilities.
    """
    capabilities = get_all_capabilities()

    capabilities_text = ""
    for agent_name, agent_caps in capabilities.items():
        # Format capabilities nicely
        caps_lines = agent_caps.strip().split("\n")
        formatted_caps = "\n  ".join(caps_lines)
        capabilities_text += f"- {agent_name}:\n  {formatted_caps}\n\n"

    return SUPERVISOR_PROMPT.format(agent_capabilities=capabilities_text)


def create_supervisor_agent(
    include_datetime: bool | None = None,
    debug: bool | None = None,
) -> Any:
    """Create the intelligent supervisor agent.

    The supervisor uses specialist agents as tools to handle
    user queries by routing to the appropriate agent.

    Args:
        include_datetime: Whether to include datetime context middleware.
            If None, uses the config value (default: True).
        debug: Whether to enable debug middleware that shows prompts.
            If None, uses the config value (default: False).

    Returns:
        The configured supervisor agent.
    """
    # Get all registered agents as tools
    agent_tools = get_all_agent_tools()

    # Build dynamic prompt with capabilities and planning guidance
    system_prompt = _build_supervisor_prompt()

    # Build middleware list
    middleware: list[Any] = []

    # Add debug middleware if enabled (via parameter or config)
    debug_enabled = debug if debug is not None else config.debug
    if debug_enabled:
        middleware.append(
            PromptDebugMiddleware(
                enabled=True,
                show_response=True,
                max_length=int(config.debug_prompt_max_length),
            )
        )

    # Add datetime middleware if enabled
    datetime_enabled = (
        include_datetime if include_datetime is not None else config.include_datetime
    )
    if datetime_enabled:
        middleware.append(DatetimeContextMiddleware(enabled=True))

    # Add summarization middleware if enabled
    if config.summarization_enabled:
        middleware.append(
            SummarizationMiddleware(
                enabled=True,
                trigger_tokens=config.summarization_trigger_tokens,
                keep_messages=config.summarization_keep_messages,
            )
        )

    # Create agent with lazy model initialization
    agent: Any = create_agent(
        model=get_answer_model(),
        tools=agent_tools,
        middleware=middleware,
        system_prompt=system_prompt,
    )

    return agent


def _build_conversation_context(messages: list, max_messages: int = 10) -> list:
    """Build conversation context from recent messages.

    Args:
        messages: List of conversation messages.
        max_messages: Maximum number of messages to include.

    Returns:
        List of recent messages for context.
    """
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages


async def supervisor_agent_node(
    state: "ChatbotState",
    register_agents_func: Callable[[], None] | None = None,
    debug: bool | None = None,
) -> "ChatbotState":
    """Execute the supervisor agent node.

    This node runs the intelligent supervisor that:
    1. Analyzes the user query with conversation context
    2. Decides whether to respond directly or use agent tools
    3. Orchestrates agent calls for complex queries
    4. Returns a natural, formatted response

    Args:
        state: The current chatbot state.
        register_agents_func: Optional function to register agents before processing.
        debug: Whether to enable debug mode (shows prompts). If None, uses config.

    Returns:
        Updated state with the supervisor's response.
    """
    # Register agents if a function is provided
    if register_agents_func is not None:
        register_agents_func()

    log_progress("Analyzing query and processing...\n")

    user_query = state.get("user_query", "")
    messages = state.get("messages", [])

    # Build conversation context
    context_messages = _build_conversation_context(messages)

    # Add the current query to messages for the supervisor
    input_messages = list(context_messages)
    if not input_messages or input_messages[-1].content != user_query:
        input_messages.append(HumanMessage(content=user_query))

    try:
        # Create and run the supervisor (with optional debug)
        supervisor = create_supervisor_agent(debug=debug)

        # Get current stream writer and pass it through config for tools
        # Use configurable recursion limit for complex multi-agent workflows
        run_config: dict = {"recursion_limit": config.recursion_limit}

        # Initialize configurable dict for tools
        run_config["configurable"] = {}

        # Add stream writer if available
        try:
            writer = get_stream_writer()
            if writer is not None:
                run_config["configurable"][STREAM_WRITER_KEY] = writer
        except (RuntimeError, Exception):
            pass

        result = await supervisor.ainvoke(
            {"messages": input_messages},
            config=run_config,
        )

        # Extract the response
        response_message = result["messages"][-1]
        raw_content = (
            response_message.content
            if hasattr(response_message, "content")
            else str(response_message)
        )
        response_text = extract_text_content(raw_content)

        log_progress("Response ready.\n")

        # Update state with raw results for formatter
        # NOTE: Don't update 'messages' here - the formatter will append the
        # polished response to maintain conversation history consistency
        state.update(
            {
                "agent_results": response_text,
                "workflow_step": "format",
            }
        )

    except Exception as e:
        import traceback

        error_type = type(e).__name__
        error_msg = str(e)

        # Log the full error for debugging
        log_progress(f"\n⚠️ Error in supervisor ({error_type}): {error_msg}\n")

        # Log traceback for developers (only show in debug mode)
        if config.debug:
            # In debug mode, show full traceback
            tb = traceback.format_exc()
            logger.error(f"Supervisor error: {error_type}: {error_msg}\n{tb}")
        else:
            # In normal mode, just log the error without full traceback
            logger.warning(f"Supervisor error: {error_type}: {error_msg}")

        # Provide more specific error messages when possible
        if "recursion" in error_msg.lower() or "maximum" in error_msg.lower():
            error_response = (
                "The request required too many steps to complete. "
                "Try asking a more specific question."
            )
        elif "timeout" in error_msg.lower() or "deadline" in error_msg.lower():
            error_response = (
                "The request took too long to process. "
                "Try asking about fewer items at once."
            )
        elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
            error_response = (
                "API rate limit reached. Please wait a moment and try again."
            )
        else:
            error_response = (
                f"I encountered an error: {error_type}. "
                "Please try rephrasing your question or check the logs for details."
            )

        state.update(
            {
                "chatbot_response": error_response,
                "messages": [AIMessage(content=error_response)],
                "workflow_step": "error",
            }
        )

    return state
