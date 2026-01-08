"""Response Formatter Agent implementation.

This module provides the formatter node that synthesizes raw agent results
into a polished final response for the user.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ...core.llm import get_answer_model
from ...core.utils import extract_text_content
from .prompts import FORMATTER_PROMPT

if TYPE_CHECKING:
    from ...core.state import ChatbotState


async def formatter_node(state: ChatbotState) -> dict[str, Any]:
    """Format raw agent results into final user response.

    This node takes the agent_results from the supervisor and formats them
    into a polished, user-friendly response.

    Args:
        state: Current chatbot state with agent_results and user_query.

    Returns:
        Updated state with chatbot_response and workflow_step.
    """
    # Get and ensure string types (TypedDict doesn't guarantee runtime types)
    user_query = state.get("user_query") or ""
    agent_results = state.get("agent_results") or ""

    # Check for empty or whitespace-only results
    if not agent_results.strip():
        fallback_msg = "I don't have enough information to answer that question."
        return {
            "chatbot_response": fallback_msg,
            "messages": [AIMessage(content=fallback_msg)],
            "workflow_step": "complete",
        }

    # Build messages with system instructions and user data
    # SystemMessage for instructions improves LLM instruction adherence
    system_instructions = f"""{FORMATTER_PROMPT}

Now provide a natural, well-formatted response to the user's question \
using the information provided below."""

    user_context = f"""## User's Question

{user_query}

## Information from Specialist Systems

{agent_results}"""

    # Get LLM and format the response
    llm = get_answer_model()
    messages = [
        SystemMessage(content=system_instructions),
        HumanMessage(content=user_context),
    ]

    try:
        response = await llm.ainvoke(messages)
        # Extract text from structured content (handles Gemini's list format)
        formatted_response = extract_text_content(response.content)

        # Update messages with the formatted response (not raw results)
        # This ensures conversation history matches what the user sees
        return {
            "chatbot_response": formatted_response,
            "messages": [AIMessage(content=formatted_response)],
            "workflow_step": "complete",
        }
    except Exception as e:
        # Re-raise cancellation errors for proper async shutdown
        if isinstance(e, (asyncio.CancelledError, KeyboardInterrupt)):
            raise
        # If formatting fails, return the raw results
        return {
            "chatbot_response": agent_results,
            "messages": [AIMessage(content=agent_results)],
            "workflow_step": "complete",
        }
