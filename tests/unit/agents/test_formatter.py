"""Tests for the Response Formatter Agent."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage

from macsdk.agents.formatter import formatter_node
from macsdk.core.state import ChatbotState


class TestFormatterNode:
    """Tests for the formatter_node function."""

    @pytest.mark.asyncio
    async def test_formatter_with_agent_results(self) -> None:
        """Formatter processes agent results into final response."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "format",
            "agent_results": "The weather is sunny with 25°C.",
        }

        with patch("macsdk.agents.formatter.agent.get_answer_model") as mock_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(
                return_value=AIMessage(content="It's sunny and 25°C today!")
            )
            mock_model.return_value = mock_llm

            result = await formatter_node(state)

            assert result["chatbot_response"] == "It's sunny and 25°C today!"
            assert result["workflow_step"] == "complete"
            # Verify formatter updates messages with formatted response
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert result["messages"][0].content == "It's sunny and 25°C today!"
            mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_formatter_with_empty_agent_results(self) -> None:
        """Formatter returns fallback message when no agent results."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "format",
            "agent_results": "",
        }

        result = await formatter_node(state)

        assert "don't have enough information" in result["chatbot_response"]
        assert result["workflow_step"] == "complete"
        # Critical: verify messages is updated even with empty results
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "don't have enough information" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_formatter_handles_llm_error(self) -> None:
        """Formatter returns raw results when LLM fails."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "format",
            "agent_results": "Raw weather data: sunny, 25°C",
        }

        with patch("macsdk.agents.formatter.agent.get_answer_model") as mock_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
            mock_model.return_value = mock_llm

            result = await formatter_node(state)

            # Should return raw results as fallback
            assert result["chatbot_response"] == "Raw weather data: sunny, 25°C"
            assert result["workflow_step"] == "complete"
            # Even on error, messages should be updated (with raw results)
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert result["messages"][0].content == "Raw weather data: sunny, 25°C"

    @pytest.mark.asyncio
    async def test_formatter_handles_timeout(self) -> None:
        """Formatter returns raw results when formatting times out."""
        state: ChatbotState = {
            "messages": [],
            "user_query": "What is the weather?",
            "chatbot_response": "",
            "workflow_step": "format",
            "agent_results": "Raw weather data: sunny, 25°C",
        }

        with (
            patch("macsdk.agents.formatter.agent.get_answer_model") as mock_model,
            patch("macsdk.agents.formatter.agent.config") as mock_config,
        ):
            # Use a very short timeout for testing (0.1 seconds)
            mock_config.formatter_timeout = 0.1

            mock_llm = AsyncMock()

            # Simulate a timeout (longer than test timeout)
            async def slow_invoke(*args, **kwargs):
                await asyncio.sleep(1)  # 1 second > 0.1s test timeout
                return AIMessage(content="Formatted response")

            mock_llm.ainvoke = slow_invoke
            mock_model.return_value = mock_llm

            result = await formatter_node(state)

            # Should return raw results as fallback after timeout
            assert result["chatbot_response"] == "Raw weather data: sunny, 25°C"
            assert result["workflow_step"] == "complete"
            # Messages should be updated with raw results
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert result["messages"][0].content == "Raw weather data: sunny, 25°C"
