"""Utility functions for the MACSDK framework.

This module provides common utilities used across the framework,
including logging, agent execution helpers, and streaming utilities.
"""

from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING, Any, Callable

from langchain_core.messages import HumanMessage
from langgraph.config import get_stream_writer

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig


# Key used to store stream writer in config's configurable dict
STREAM_WRITER_KEY = "stream_writer_func"


def extract_text_content(content: Any) -> str:
    """Extract text from LLM message content.

    Handles both string content and structured content (list of dicts
    with 'type' and 'text' fields, as returned by some models like Gemini 3).

    This is needed because different LLM providers return content in different
    formats:
    - Claude/GPT/Gemini 2.5: Returns a string directly
    - Gemini 3: Returns a list like [{'type': 'text', 'text': '...', 'extras': {...}}]

    Args:
        content: The message content (string, list, or any other type).

    Returns:
        The extracted text as a string.

    Example:
        >>> # String content (Claude/GPT/Gemini 2.5)
        >>> extract_text_content("Hello world")
        'Hello world'

        >>> # Structured content (Gemini 3)
        >>> extract_text_content([{'type': 'text', 'text': 'Hello world'}])
        'Hello world'
    """
    # Handle None explicitly (cleaner for UI than string "None")
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        # Extract text from structured content blocks (Gemini 3 format)
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                # Use 'or ""' to handle None values safely
                text_parts.append(block.get("text") or "")
            elif isinstance(block, str):
                text_parts.append(block)
        # Return empty string for empty lists (cleaner for UI than "[]")
        return "\n".join(text_parts)

    return str(content)


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
    system_prompt: str | None = None,
    agent_name: str | None = None,
    context: dict | None = None,
    config: "RunnableConfig | None" = None,
) -> dict:
    """Run a specialist agent with tools and return structured results.

    This is the generic function used to execute specialist agents.
    The agent must be created with its system_prompt already configured
    via create_agent(system_prompt=...).

    Args:
        agent: The agent instance to run (must have ainvoke method).
        query: User query string.
        system_prompt: **DEPRECATED**. System prompt should be configured when
                      creating the agent via create_agent(system_prompt=...).
                      For backwards compatibility, if provided, it will be prepended
                      to the query as a HumanMessage. This parameter will be removed
                      in v1.0.0.
        agent_name: Name identifier for the agent. **Required** despite the
                   type hint (type hint is `str | None` only to accommodate
                   deprecated optional parameters before it).
        context: Optional context dict to include in the query.
        config: Optional RunnableConfig for streaming support.

    Returns:
        Dict with at minimum:
            - 'response': The agent's response text
            - 'agent_name': The name of the agent
            - 'tools_used': List of tools that were called
    """
    from .callbacks import ToolProgressCallback

    # Validate agent_name is provided
    if agent_name is None:
        raise TypeError(
            "run_agent_with_tools() missing required argument: 'agent_name'. "
            "Please provide agent_name as a keyword argument."
        )

    # Emit deprecation warning if system_prompt is provided
    if system_prompt is not None:
        warnings.warn(
            "Passing 'system_prompt' to run_agent_with_tools() is deprecated. "
            "Configure the system_prompt when creating the agent with "
            "create_agent(system_prompt=...). "
            "This parameter will be removed in v1.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )

    log_progress(f"[{agent_name}] Processing query...\n", config)

    # Build query with optional context
    query_content = query
    if context:
        query_content = f"Context: {context}\n\n{query}"

    # BACKWARDS COMPATIBILITY: If system_prompt is provided (deprecated pattern),
    # prepend it to the query. This maintains old behavior until v1.0.0.
    if system_prompt:
        query_content = f"{system_prompt}\n\n{query_content}"

    messages = [HumanMessage(content=query_content)]

    # Create callback for real-time tool progress
    tool_callback = ToolProgressCallback(agent_name=agent_name, config=config)

    # Merge callbacks with existing config
    invoke_config: dict = dict(config) if config else {}

    # IMPORTANT: Use independent recursion_limit for specialist agents
    # The supervisor passes its config (with recursion_limit and step counter) to
    # agents as tools. If we share these, internal agent steps count against the
    # supervisor's limit, causing premature GraphRecursionError.
    # Each specialist agent should have its own independent limit and counter.
    from .config import config as macsdk_config

    invoke_config.pop("recursion_limit", None)  # Remove supervisor's limit
    invoke_config["recursion_limit"] = macsdk_config.recursion_limit  # Fresh limit

    # Also clear the step counter from metadata so specialist starts fresh
    if "metadata" in invoke_config and isinstance(invoke_config["metadata"], dict):
        invoke_config["metadata"] = {
            k: v for k, v in invoke_config["metadata"].items() if k != "langgraph_step"
        }

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
    # Extract text content (handles both string and Gemini's structured format)
    raw_content = (
        response_message.content
        if hasattr(response_message, "content")
        else str(response_message)
    )

    return {
        "response": extract_text_content(raw_content),
        "agent_name": agent_name,
        "tools_used": tools_used,
    }
