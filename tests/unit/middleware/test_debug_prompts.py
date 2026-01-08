"""Tests for Debug Prompts Middleware."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from macsdk.middleware import PromptDebugMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import ModelRequest
    from langchain.agents.middleware.types import ModelResponse


@dataclass
class MockModelRequest:
    """Mock ModelRequest for testing."""

    messages: list = field(default_factory=list)
    system_message: SystemMessage | None = None
    state: dict = field(default_factory=dict)


@dataclass
class MockModelResponse:
    """Mock ModelResponse for testing (old structure)."""

    message: AIMessage | None = None


@dataclass
class MockModelResponseNew:
    """Mock ModelResponse for testing (new structure with result)."""

    result: AIMessage | list[AIMessage] | None = None


@dataclass
class MockModelResponseEmpty:
    """Mock ModelResponse with no message or result attributes."""

    some_other_attr: str = "value"


class TestPromptDebugMiddlewareInit:
    """Tests for PromptDebugMiddleware initialization."""

    def test_default_initialization(self) -> None:
        """Test default initialization."""
        middleware = PromptDebugMiddleware()
        assert middleware.enabled is True
        assert middleware.show_system is True
        assert middleware.show_user is True
        assert middleware.show_response is True

    def test_can_be_disabled(self) -> None:
        """Test that middleware can be disabled."""
        middleware = PromptDebugMiddleware(enabled=False)
        assert middleware.enabled is False

    def test_custom_max_length(self) -> None:
        """Test custom max_length setting."""
        middleware = PromptDebugMiddleware(max_length=500)
        assert middleware.max_length == 500


class TestLogResponse:
    """Tests for _log_response method."""

    def test_old_response_structure_with_message(self) -> None:
        """Test handling old LangChain structure (response.message)."""
        middleware = PromptDebugMiddleware()
        msg = AIMessage(content="Hello, how can I help?")
        response = MockModelResponse(message=msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(cast("ModelResponse", response), agent_context="")

            # Check that response was logged
            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "After Model Call" in output_text
            assert "MODEL RESPONSE" in output_text
            assert "Hello, how can I help?" in output_text

    def test_new_response_structure_with_single_result(self) -> None:
        """Test new LangChain structure (response.result with single message)."""
        middleware = PromptDebugMiddleware()
        msg = AIMessage(content="Response from new structure")
        response = MockModelResponseNew(result=msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(cast("ModelResponse", response), agent_context="")

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "After Model Call" in output_text
            assert "MODEL RESPONSE" in output_text
            assert "Response from new structure" in output_text

    def test_new_response_structure_with_list_result(self) -> None:
        """Test handling new LangChain structure (response.result with list)."""
        middleware = PromptDebugMiddleware()
        messages: list[Any] = [
            HumanMessage(content="User query"),
            AIMessage(content="Final AI response"),
        ]
        response = MockModelResponseNew(result=messages)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(cast("ModelResponse", response), agent_context="")

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "After Model Call" in output_text
            # Should show the last message (AI response)
            assert "Final AI response" in output_text

    def test_response_with_tool_calls(self) -> None:
        """Test logging response with tool calls."""
        middleware = PromptDebugMiddleware()
        msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_1",
                    "name": "calculator",
                    "args": {"operation": "add", "a": 1, "b": 2},
                },
                {"id": "call_2", "name": "search", "args": {"query": "python"}},
            ],
        )
        response = MockModelResponse(message=msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(cast("ModelResponse", response), agent_context="")

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "MODEL REQUESTING TOOL CALLS (2)" in output_text
            assert "calculator" in output_text
            assert "search" in output_text

    def test_response_with_no_extractable_message(self) -> None:
        """Test handling response with neither message nor result."""
        middleware = PromptDebugMiddleware()
        response = MockModelResponseEmpty()

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(cast("ModelResponse", response), agent_context="")

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "Could not extract response content" in output_text
            assert "MockModelResponseEmpty" in output_text
            assert "Available attributes" in output_text

    def test_response_with_token_usage(self) -> None:
        """Test logging token usage from response_metadata."""
        middleware = PromptDebugMiddleware()
        msg = AIMessage(
            content="Response with tokens",
            response_metadata={
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                }
            },
        )
        response = MockModelResponse(message=msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(cast("ModelResponse", response), agent_context="")

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "TOKEN USAGE" in output_text
            assert "prompt_tokens" in output_text

    def test_response_with_agent_context(self) -> None:
        """Test that agent context is included in output."""
        middleware = PromptDebugMiddleware()
        msg = AIMessage(content="Test")
        response = MockModelResponse(message=msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_response(
                cast("ModelResponse", response), agent_context=" [supervisor]"
            )

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "[supervisor]" in output_text


class TestLogRequest:
    """Tests for _log_request method."""

    def test_logs_system_prompt(self) -> None:
        """Test that system prompt is logged."""
        middleware = PromptDebugMiddleware()
        system_msg = SystemMessage(content="You are a helpful assistant.")
        request = MockModelRequest(system_message=system_msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_request(cast("ModelRequest", request))

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "SYSTEM PROMPT" in output_text
            assert "You are a helpful assistant" in output_text

    def test_logs_user_messages(self) -> None:
        """Test that user messages are logged."""
        middleware = PromptDebugMiddleware()
        messages = [HumanMessage(content="Hello, can you help me?")]
        request = MockModelRequest(messages=messages)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_request(cast("ModelRequest", request))

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "USER MESSAGE" in output_text
            assert "Hello, can you help me?" in output_text

    def test_logs_tool_results(self) -> None:
        """Test that tool results are logged."""
        middleware = PromptDebugMiddleware()
        messages = [
            ToolMessage(
                content="Result: 42",
                tool_call_id="call_123",
                name="calculator",
            )
        ]
        request = MockModelRequest(messages=messages)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_request(cast("ModelRequest", request))

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "TOOL RESULT" in output_text
            assert "calculator" in output_text
            assert "Result: 42" in output_text

    def test_can_disable_system_logging(self) -> None:
        """Test that system prompt logging can be disabled."""
        middleware = PromptDebugMiddleware(show_system=False)
        system_msg = SystemMessage(content="System prompt")
        request = MockModelRequest(system_message=system_msg)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_request(cast("ModelRequest", request))

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "SYSTEM PROMPT" not in output_text

    def test_can_disable_user_logging(self) -> None:
        """Test that user message logging can be disabled."""
        middleware = PromptDebugMiddleware(show_user=False)
        messages = [HumanMessage(content="User message")]
        request = MockModelRequest(messages=messages)

        with patch.object(middleware, "_output") as mock_output:
            middleware._log_request(cast("ModelRequest", request))

            calls = [str(call) for call in mock_output.call_args_list]
            output_text = " ".join(calls)
            assert "USER MESSAGE" not in output_text


class TestWrapModelCall:
    """Tests for wrap_model_call method."""

    def test_disabled_middleware_passes_through(self) -> None:
        """Test that disabled middleware doesn't interfere."""
        middleware = PromptDebugMiddleware(enabled=False)
        request = MockModelRequest()
        mock_response = MockModelResponse(message=AIMessage(content="Test"))

        handler = MagicMock(return_value=mock_response)

        result = middleware.wrap_model_call(cast("ModelRequest", request), handler)

        # Should call handler and return result without logging
        handler.assert_called_once_with(request)
        assert result == mock_response

    def test_enabled_middleware_logs_and_returns(self) -> None:
        """Test that enabled middleware logs and returns response."""
        middleware = PromptDebugMiddleware(enabled=True)
        request = MockModelRequest()
        mock_response = MockModelResponse(message=AIMessage(content="Test"))

        handler = MagicMock(return_value=mock_response)

        with (
            patch.object(middleware, "_log_request"),
            patch.object(middleware, "_log_response"),
        ):
            result = middleware.wrap_model_call(cast("ModelRequest", request), handler)

        handler.assert_called_once_with(request)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_async_wrap_model_call(self) -> None:
        """Test async version of wrap_model_call."""
        middleware = PromptDebugMiddleware(enabled=True)
        request = MockModelRequest()
        mock_response = MockModelResponse(message=AIMessage(content="Test"))

        async def async_handler(req: Any) -> Any:
            return mock_response

        with (
            patch.object(middleware, "_log_request"),
            patch.object(middleware, "_log_response"),
        ):
            result = await middleware.awrap_model_call(
                cast("ModelRequest", request), async_handler
            )

        assert result == mock_response


class TestTruncation:
    """Tests for message truncation."""

    def test_truncates_long_messages(self) -> None:
        """Test that long messages are truncated."""
        middleware = PromptDebugMiddleware(max_length=50)
        long_text = "A" * 100

        truncated = middleware._truncate(long_text)

        assert len(truncated) < 100
        assert "truncated" in truncated
        assert "100 chars" in truncated

    def test_does_not_truncate_short_messages(self) -> None:
        """Test that short messages are not truncated."""
        middleware = PromptDebugMiddleware(max_length=100)
        short_text = "Short message"

        truncated = middleware._truncate(short_text)

        assert truncated == short_text
        assert "truncated" not in truncated


class TestAgentContext:
    """Tests for agent context detection."""

    def test_detects_supervisor_context(self) -> None:
        """Test that supervisor context is detected."""
        middleware = PromptDebugMiddleware()
        system_msg = SystemMessage(
            content="You are a supervisor that orchestrates multiple agents."
        )
        request = MockModelRequest(system_message=system_msg)

        context = middleware._get_agent_context(cast("ModelRequest", request))

        assert "supervisor" in context.lower()

    def test_detects_agent_from_state(self) -> None:
        """Test that agent name is extracted from state."""
        middleware = PromptDebugMiddleware()
        request = MockModelRequest(state={"agent_name": "toolbox"})

        context = middleware._get_agent_context(cast("ModelRequest", request))

        assert "toolbox" in context
