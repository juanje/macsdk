"""Tests for utility functions."""

from __future__ import annotations

from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from macsdk.core import STREAM_WRITER_KEY, log_progress

# Test constants for this module
TEST_MESSAGE = "Test message"
TEST_QUERY = "test query"
TEST_SYSTEM_PROMPT = "You are a helpful assistant"
TEST_RESPONSE = "Test response"
TEST_TOOL = "test_tool"
TEST_AGENT_NAME = "test_agent"


class TestLogProgress:
    """Tests for log_progress function."""

    def test_log_progress_uses_stream_writer_when_available(self) -> None:
        """Uses LangGraph stream writer when available."""
        mock_writer = MagicMock()

        with patch("macsdk.core.utils.get_stream_writer", return_value=mock_writer):
            log_progress(TEST_MESSAGE)

        mock_writer.assert_called_once_with(TEST_MESSAGE)

    def test_log_progress_falls_back_to_stdout(self) -> None:
        """Falls back to stdout when no stream writer."""
        with patch(
            "macsdk.core.utils.get_stream_writer",
            side_effect=RuntimeError("No writer"),
        ):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                log_progress(TEST_MESSAGE)
                assert TEST_MESSAGE in mock_stdout.getvalue()

    def test_log_progress_uses_config_writer(self) -> None:
        """Uses writer from config if provided."""
        mock_writer = MagicMock()
        # RunnableConfig is a TypedDict, we create a compatible dict for testing
        config = {"configurable": {STREAM_WRITER_KEY: mock_writer}}

        log_progress(TEST_MESSAGE, config)  # type: ignore[arg-type]

        mock_writer.assert_called_once_with(TEST_MESSAGE)

    def test_log_progress_handles_stream_writer_exception(self) -> None:
        """Handles exceptions from stream writer gracefully."""
        with patch(
            "macsdk.core.utils.get_stream_writer",
            side_effect=RuntimeError("Error"),
        ):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                log_progress(TEST_MESSAGE)
                assert TEST_MESSAGE in mock_stdout.getvalue()


class TestRunAgentWithTools:
    """Tests for run_agent_with_tools function."""

    @pytest.mark.asyncio
    async def test_run_agent_with_structured_response(self) -> None:
        """Handles agents that return structured responses."""
        from macsdk.core import run_agent_with_tools

        mock_response = MagicMock()
        mock_response.response_text = TEST_RESPONSE
        mock_response.tools_used = [TEST_TOOL]
        mock_response.model_dump.return_value = {
            "response_text": TEST_RESPONSE,
            "tools_used": [TEST_TOOL],
        }

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"structured_response": mock_response}

        with patch("macsdk.core.utils.log_progress"):
            result = await run_agent_with_tools(
                agent=mock_agent,
                query=TEST_QUERY,
                agent_name=TEST_AGENT_NAME,
            )

        assert result["response"] == TEST_RESPONSE
        assert result["agent_name"] == TEST_AGENT_NAME
        assert TEST_TOOL in result["tools_used"]

    @pytest.mark.asyncio
    async def test_run_agent_without_structured_response(self) -> None:
        """Handles agents that return plain messages."""
        from macsdk.core import run_agent_with_tools

        plain_response = "Plain response"
        mock_message = MagicMock()
        mock_message.content = plain_response
        mock_message.tool_calls = None

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [mock_message],
        }

        with patch("macsdk.core.utils.log_progress"):
            result = await run_agent_with_tools(
                agent=mock_agent,
                query=TEST_QUERY,
                agent_name=TEST_AGENT_NAME,
            )

        assert result["response"] == plain_response
        assert result["agent_name"] == TEST_AGENT_NAME

    @pytest.mark.asyncio
    async def test_run_agent_with_deprecated_system_prompt(self) -> None:
        """Emits deprecation warning when system_prompt is passed and prepends it."""
        from langchain_core.messages import HumanMessage

        from macsdk.core import run_agent_with_tools

        mock_message = MagicMock()
        mock_message.content = TEST_RESPONSE
        mock_message.tool_calls = None

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [mock_message],
        }

        with patch("macsdk.core.utils.log_progress"):
            with pytest.warns(
                DeprecationWarning,
                match=(
                    "Passing 'system_prompt' to run_agent_with_tools\\(\\) "
                    "is deprecated"
                ),
            ):
                result = await run_agent_with_tools(
                    agent=mock_agent,
                    query=TEST_QUERY,
                    system_prompt=TEST_SYSTEM_PROMPT,  # Deprecated parameter
                    agent_name=TEST_AGENT_NAME,
                )

        # Should still work despite deprecation
        assert result["response"] == TEST_RESPONSE
        assert result["agent_name"] == TEST_AGENT_NAME

        # Verify system_prompt was prepended to query in HumanMessage
        call_args = mock_agent.ainvoke.call_args
        messages = call_args[0][0]["messages"]
        assert len(messages) == 1
        assert isinstance(messages[0], HumanMessage)
        # System prompt should be prepended
        assert TEST_SYSTEM_PROMPT in messages[0].content
        assert TEST_QUERY in messages[0].content
        assert messages[0].content.index(TEST_SYSTEM_PROMPT) < messages[
            0
        ].content.index(TEST_QUERY)

    @pytest.mark.asyncio
    async def test_run_agent_with_positional_args(self) -> None:
        """Ensures positional argument compatibility is maintained."""
        from macsdk.core import run_agent_with_tools

        mock_message = MagicMock()
        mock_message.content = TEST_RESPONSE
        mock_message.tool_calls = None

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [mock_message],
        }

        with patch("macsdk.core.utils.log_progress"):
            with pytest.warns(DeprecationWarning):
                # Old-style positional call (maintains backward compatibility)
                result = await run_agent_with_tools(
                    mock_agent,  # agent (pos 0)
                    TEST_QUERY,  # query (pos 1)
                    TEST_SYSTEM_PROMPT,  # system_prompt (pos 2) - deprecated
                    TEST_AGENT_NAME,  # agent_name (pos 3)
                )

        # Should work correctly despite being deprecated
        assert result["response"] == TEST_RESPONSE
        assert result["agent_name"] == TEST_AGENT_NAME
