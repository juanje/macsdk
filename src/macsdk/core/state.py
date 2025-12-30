"""State definitions for MACSDK chatbots.

This module defines the state schema used throughout the chatbot
graph execution.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    """State for the multi-agent chatbot graph.

    This state flows through all nodes in the graph and maintains
    the conversation context and current processing status.

    Attributes:
        messages: Conversation history with automatic message accumulation.
            Uses the add_messages reducer to properly accumulate messages.
        user_query: The current user query being processed.
        chatbot_response: The final response to send to the user.
        workflow_step: Current step in the workflow (query, processing, complete, error).
        agent_results: Raw results from specialist agents before formatting.
            Used by formatter_node to synthesize the final response.
    """

    messages: Annotated[list, add_messages]
    user_query: str
    chatbot_response: str
    workflow_step: str
    agent_results: str
