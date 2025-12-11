"""Tests for DateTime Context Middleware."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast
from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage, SystemMessage

from macsdk.middleware import DatetimeContextMiddleware, format_datetime_context

# Type alias for agent state in tests
AgentStateDict = dict[str, Any]


class TestFormatDatetimeContext:
    """Tests for format_datetime_context function."""

    def test_returns_string(self) -> None:
        """Test that format_datetime_context returns a string."""
        result = format_datetime_context()
        assert isinstance(result, str)

    def test_contains_datetime_header(self) -> None:
        """Test that result contains the datetime header."""
        result = format_datetime_context()
        assert "## Current DateTime Context" in result

    def test_contains_utc_time(self) -> None:
        """Test that result contains UTC time."""
        result = format_datetime_context()
        assert "Current UTC time" in result
        assert "UTC" in result

    def test_contains_iso_format(self) -> None:
        """Test that result contains ISO format."""
        result = format_datetime_context()
        assert "ISO format" in result

    def test_custom_datetime(self) -> None:
        """Test with a specific datetime."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = format_datetime_context(test_dt)

        assert "2024-06-15 10:30:00 UTC" in result
        assert "Saturday, June 15, 2024" in result
        assert "2024-06-15T10:30:00+00:00" in result


class TestDatetimeContextMiddleware:
    """Tests for DatetimeContextMiddleware class."""

    def test_init_enabled_by_default(self) -> None:
        """Test that middleware is enabled by default."""
        middleware = DatetimeContextMiddleware()
        assert middleware.enabled is True

    def test_init_can_be_disabled(self) -> None:
        """Test that middleware can be disabled."""
        middleware = DatetimeContextMiddleware(enabled=False)
        assert middleware.enabled is False

    def test_disabled_middleware_returns_none(self) -> None:
        """Test that disabled middleware returns None."""
        middleware = DatetimeContextMiddleware(enabled=False)
        state: AgentStateDict = {"messages": [HumanMessage(content="Hello")]}
        runtime = MagicMock()

        result = middleware.before_model(cast(Any, state), runtime)

        assert result is None

    def test_empty_messages_returns_none(self) -> None:
        """Test that empty message list returns None."""
        middleware = DatetimeContextMiddleware()
        state: AgentStateDict = {"messages": []}
        runtime = MagicMock()

        result = middleware.before_model(cast(Any, state), runtime)

        assert result is None

    def test_injects_into_existing_system_message(self) -> None:
        """Test that datetime is injected into existing system message."""
        middleware = DatetimeContextMiddleware()
        original_system = "You are a helpful assistant."
        state: AgentStateDict = {
            "messages": [
                SystemMessage(content=original_system),
                HumanMessage(content="Hello"),
            ]
        }
        runtime = MagicMock()

        result = middleware.before_model(cast(Any, state), runtime)

        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) == 2
        assert isinstance(result["messages"][0], SystemMessage)
        assert "## Current DateTime Context" in result["messages"][0].content
        assert original_system in result["messages"][0].content
        assert isinstance(result["messages"][1], HumanMessage)

    def test_creates_system_message_if_missing(self) -> None:
        """Test that a system message is created if none exists."""
        middleware = DatetimeContextMiddleware()
        state: AgentStateDict = {"messages": [HumanMessage(content="Hello")]}
        runtime = MagicMock()

        result = middleware.before_model(cast(Any, state), runtime)

        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) == 2
        assert isinstance(result["messages"][0], SystemMessage)
        assert "## Current DateTime Context" in result["messages"][0].content
        assert isinstance(result["messages"][1], HumanMessage)

    def test_preserves_message_order(self) -> None:
        """Test that message order is preserved."""
        middleware = DatetimeContextMiddleware()
        state: AgentStateDict = {
            "messages": [
                SystemMessage(content="System"),
                HumanMessage(content="User 1"),
                HumanMessage(content="User 2"),
            ]
        }
        runtime = MagicMock()

        result = middleware.before_model(cast(Any, state), runtime)

        assert result is not None
        assert len(result["messages"]) == 3
        assert isinstance(result["messages"][0], SystemMessage)
        assert result["messages"][1].content == "User 1"
        assert result["messages"][2].content == "User 2"

    def test_does_not_duplicate_datetime_context(self) -> None:
        """Test that datetime context is not duplicated on repeated calls."""
        middleware = DatetimeContextMiddleware()
        runtime = MagicMock()

        # Simulate a system message that already has datetime context
        existing_context = format_datetime_context()
        state: AgentStateDict = {
            "messages": [
                SystemMessage(content=f"{existing_context}\nOriginal system prompt")
            ]
        }

        # Should return None because context already present
        result = middleware.before_model(cast(Any, state), runtime)
        assert result is None

    def test_missing_messages_key_returns_none(self) -> None:
        """Test that missing messages key returns None."""
        middleware = DatetimeContextMiddleware()
        state: AgentStateDict = {}
        runtime = MagicMock()

        result = middleware.before_model(cast(Any, state), runtime)

        assert result is None
