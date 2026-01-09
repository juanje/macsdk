"""Tests for the Supervisor Agent."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from macsdk.agents.supervisor.agent import supervisor_agent_node
from macsdk.core.exceptions import SpecialistTimeoutError
from macsdk.core.state import ChatbotState


class TestSupervisorNode:
    """Tests for the supervisor_agent_node function."""

    @pytest.mark.asyncio
    async def test_supervisor_handles_timeout(self) -> None:
        """Supervisor handles timeout gracefully and returns error state."""
        state: ChatbotState = {
            "messages": [HumanMessage(content="What is the weather?")],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "supervisor",
            "agent_results": "",
        }

        # Mock the supervisor to simulate a timeout
        with (
            patch(
                "macsdk.agents.supervisor.agent.create_supervisor_agent"
            ) as mock_create,
            patch("macsdk.agents.supervisor.agent.get_stream_writer") as mock_writer,
            patch("macsdk.agents.supervisor.agent.config") as mock_config,
        ):
            # Use a very short timeout for testing (0.1 seconds)
            mock_config.supervisor_timeout = 0.1

            mock_supervisor = AsyncMock()

            # Simulate a long-running operation (longer than test timeout)
            async def slow_invoke(*args, **kwargs):
                await asyncio.sleep(1)  # 1 second > 0.1s test timeout
                return {"messages": [AIMessage(content="Response")]}

            mock_supervisor.ainvoke = slow_invoke
            mock_create.return_value = mock_supervisor
            mock_writer.return_value = None

            # Should handle timeout gracefully and return error state
            result = await supervisor_agent_node(state)

            # Verify error state is returned with user-friendly message
            assert result["workflow_step"] == "error"
            assert "took too long" in result["chatbot_response"].lower()
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)

    @pytest.mark.asyncio
    async def test_supervisor_successful_execution(self) -> None:
        """Supervisor completes successfully within timeout."""
        state: ChatbotState = {
            "messages": [HumanMessage(content="What is the weather?")],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "supervisor",
            "agent_results": "",
        }

        with (
            patch(
                "macsdk.agents.supervisor.agent.create_supervisor_agent"
            ) as mock_create,
            patch("macsdk.agents.supervisor.agent.get_stream_writer") as mock_writer,
        ):
            mock_supervisor = AsyncMock()
            mock_supervisor.ainvoke = AsyncMock(
                return_value={
                    "messages": [
                        HumanMessage(content="What is the weather?"),
                        AIMessage(content="It's sunny and 25°C."),
                    ]
                }
            )
            mock_create.return_value = mock_supervisor
            mock_writer.return_value = None

            result = await supervisor_agent_node(state)

            assert result["agent_results"] == "It's sunny and 25°C."
            assert result["workflow_step"] == "format"
            mock_supervisor.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_supervisor_handles_generic_error(self) -> None:
        """Supervisor handles errors gracefully with user-friendly messages."""
        state: ChatbotState = {
            "messages": [HumanMessage(content="What is the weather?")],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "supervisor",
            "agent_results": "",
        }

        with (
            patch(
                "macsdk.agents.supervisor.agent.create_supervisor_agent"
            ) as mock_create,
            patch("macsdk.agents.supervisor.agent.get_stream_writer") as mock_writer,
        ):
            mock_supervisor = AsyncMock()
            mock_supervisor.ainvoke = AsyncMock(side_effect=ValueError("Test error"))
            mock_create.return_value = mock_supervisor
            mock_writer.return_value = None

            result = await supervisor_agent_node(state)

            # Should return error state with user-friendly message
            assert result["workflow_step"] == "error"
            assert "error" in result["chatbot_response"].lower()
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)

    @pytest.mark.asyncio
    async def test_supervisor_handles_timeout_error_message(self) -> None:
        """Supervisor provides specific message for timeout-related errors."""
        state: ChatbotState = {
            "messages": [HumanMessage(content="What is the weather?")],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "supervisor",
            "agent_results": "",
        }

        with (
            patch(
                "macsdk.agents.supervisor.agent.create_supervisor_agent"
            ) as mock_create,
            patch("macsdk.agents.supervisor.agent.get_stream_writer") as mock_writer,
        ):
            mock_supervisor = AsyncMock()
            mock_supervisor.ainvoke = AsyncMock(
                side_effect=SpecialistTimeoutError(
                    agent_name="test_specialist", timeout=90.0
                )
            )
            mock_create.return_value = mock_supervisor
            mock_writer.return_value = None

            result = await supervisor_agent_node(state)

            # Should preserve the specific specialist timeout message
            assert result["workflow_step"] == "error"
            assert "took too long" in result["chatbot_response"].lower()
            assert "Agent 'test_specialist' timed out" in result["chatbot_response"]
            assert "90" in result["chatbot_response"]  # Timeout value
            # Should NOT have the generic supervisor timeout message
            assert "exceeded 120" not in result["chatbot_response"]
