"""Utility functions for the MACSDK framework.

This module provides common utilities used across the framework,
including logging, agent execution helpers, and streaming utilities.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable

from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig


# Key used to store stream writer in config's configurable dict
STREAM_WRITER_KEY = "stream_writer_func"


def log_progress(message: str, config: "RunnableConfig | None" = None) -> None:
    """Log a progress message to the stream writer if available, otherwise print.

    This function attempts to use LangGraph's stream writer for real-time
    progress updates. It can receive the config from a tool or node context
    to access the stream writer. If no stream writer is available (e.g.,
    when running outside of a graph context), it falls back to stdout.

    Args:
        message: The progress message to log.
        config: Optional RunnableConfig that may contain a stream writer.
    """
    # Try to get writer from config's configurable dict (for tools context)
    if config is not None:
        configurable = config.get("configurable", {})
        writer_func = configurable.get(STREAM_WRITER_KEY)
        if writer_func is not None and callable(writer_func):
            try:
                writer_func(message)
                return
            except Exception:  # nosec B110
                pass  # Fall through to other logging methods

    # Try to use LangGraph's context stream writer (for node context)
    try:
        writer = get_stream_writer()
        if writer is not None:
            writer(message)
            return
    except (RuntimeError, Exception):
        pass

    # Fallback to stdout
    sys.stdout.write(message)
    sys.stdout.flush()


def create_config_with_writer(writer: Callable[[str], None]) -> "RunnableConfig":
    """Create a RunnableConfig with a stream writer function.

    This is useful for passing the stream writer to tools and nested agents.

    Args:
        writer: A callable that accepts a string message.

    Returns:
        A RunnableConfig with the writer in configurable.
    """
    return {"configurable": {STREAM_WRITER_KEY: writer}}


async def run_agent_with_tools(
    agent: Any,
    query: str,
    system_prompt: str,
    agent_name: str,
    context: dict | None = None,
    config: "RunnableConfig | None" = None,
) -> dict:
    """Run a specialist agent with tools and return structured results.

    This is the generic function used to execute specialist agents.
    It handles prompt construction, agent invocation, and result extraction.

    Args:
        agent: The agent instance to run (must have ainvoke method).
        query: User query string.
        system_prompt: System prompt for the agent.
        agent_name: Name identifier for the agent.
        context: Optional context dict to include in the prompt.
        config: Optional RunnableConfig for streaming support.

    Returns:
        Dict with at minimum:
            - 'response': The agent's response text
            - 'agent_name': The name of the agent
            - 'tools_used': List of tools that were called
    """
    from .callbacks import ToolProgressCallback

    log_progress(f"[{agent_name}] Processing query...\n", config)

    messages = [HumanMessage(content=query)]

    if context:
        system_context = f"\nContext: {context}"
        messages[0].content = system_prompt + system_context + "\n\n" + query
    else:
        messages[0].content = system_prompt + "\n\n" + query

    # Create callback for real-time tool progress
    tool_callback = ToolProgressCallback(agent_name=agent_name, config=config)

    # Merge callbacks with existing config
    invoke_config: dict = dict(config) if config else {}
    existing_callbacks = invoke_config.get("callbacks")
    if existing_callbacks is None:
        invoke_config["callbacks"] = [tool_callback]
    elif isinstance(existing_callbacks, list):
        invoke_config["callbacks"] = existing_callbacks + [tool_callback]
    else:
        invoke_config["callbacks"] = [tool_callback]

    result = await agent.ainvoke({"messages": messages}, config=invoke_config)

    # Extract tools used from messages (if available)
    tools_used = []
    if "messages" in result:
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if isinstance(tc, dict) and tc.get("name"):
                        tools_used.append(tc["name"])

    structured_response = result.get("structured_response")

    if structured_response:
        # Prefer tools from messages (actual tool calls) over structured response
        # because the LLM can confuse service names with tool names
        final_tools = tools_used or structured_response.tools_used or []

        # Log tools used for transparency (only if not already logged in real-time)
        if final_tools:
            unique_tools = list(dict.fromkeys(final_tools))
            tools_str = ", ".join(unique_tools)
            log_progress(f"[{agent_name}] Tools used: {tools_str}\n", config)

        response_dict = {
            "response": structured_response.response_text,
            "agent_name": agent_name,
            "tools_used": final_tools,
        }

        for field_name, field_value in structured_response.model_dump().items():
            if field_name not in ["response_text", "tools_used"]:
                response_dict[field_name] = field_value

        return response_dict

    # Log tools used for transparency
    if tools_used:
        unique_tools = list(dict.fromkeys(tools_used))
        tools_str = ", ".join(unique_tools)
        log_progress(f"[{agent_name}] Tools used: {tools_str}\n", config)

    response_message = result["messages"][-1]

    return {
        "response": response_message.content
        if hasattr(response_message, "content")
        else str(response_message),
        "agent_name": agent_name,
        "tools_used": tools_used,
    }
