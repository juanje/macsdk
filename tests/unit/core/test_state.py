"""Tests for ChatbotState."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage

from macsdk.core import ChatbotState

if TYPE_CHECKING:
    from macsdk.core import ChatbotState as ChatbotStateType

# Test constants for this module
TEST_USER_QUERY = "test query"
TEST_WORKFLOW_STEP_QUERY = "query"
TEST_WORKFLOW_STEP_COMPLETE = "complete"
TEST_HUMAN_MESSAGE = "Hello"
TEST_AI_MESSAGE = "Hi there!"
TEST_FOLLOWUP_MESSAGE = "How are you?"

# Valid workflow steps
WORKFLOW_STEPS = ["query", "processing", "complete", "error"]


class TestChatbotState:
    """Tests for the ChatbotState TypedDict."""

    def test_state_has_required_fields(self, sample_state: "ChatbotStateType") -> None:
        """State has all required fields."""
        assert "messages" in sample_state
        assert "user_query" in sample_state
        assert "chatbot_response" in sample_state
        assert "workflow_step" in sample_state

    def test_state_messages_can_hold_human_messages(self) -> None:
        """Messages field can hold HumanMessage objects."""
        state: ChatbotState = {
            "messages": [HumanMessage(content=TEST_HUMAN_MESSAGE)],
            "user_query": TEST_HUMAN_MESSAGE,
            "chatbot_response": "",
            "workflow_step": TEST_WORKFLOW_STEP_QUERY,
        }
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)

    def test_state_messages_can_hold_ai_messages(self) -> None:
        """Messages field can hold AIMessage objects."""
        state: ChatbotState = {
            "messages": [AIMessage(content=TEST_AI_MESSAGE)],
            "user_query": "",
            "chatbot_response": TEST_AI_MESSAGE,
            "workflow_step": TEST_WORKFLOW_STEP_COMPLETE,
        }
        assert isinstance(state["messages"][0], AIMessage)

    def test_state_messages_can_hold_mixed_messages(self) -> None:
        """Messages field can hold mixed message types."""
        state: ChatbotState = {
            "messages": [
                HumanMessage(content=TEST_HUMAN_MESSAGE),
                AIMessage(content=TEST_AI_MESSAGE),
                HumanMessage(content=TEST_FOLLOWUP_MESSAGE),
            ],
            "user_query": TEST_FOLLOWUP_MESSAGE,
            "chatbot_response": "",
            "workflow_step": "processing",
        }
        assert len(state["messages"]) == 3

    def test_state_workflow_steps(self) -> None:
        """Workflow step can be any valid value."""
        for step in WORKFLOW_STEPS:
            state: ChatbotState = {
                "messages": [],
                "user_query": "",
                "chatbot_response": "",
                "workflow_step": step,
            }
            assert state["workflow_step"] == step
