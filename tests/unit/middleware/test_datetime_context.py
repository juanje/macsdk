"""Tests for DateTime Context Middleware."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast
from unittest.mock import MagicMock

from langchain_core.messages import HumanMessage, SystemMessage

from macsdk.middleware import DatetimeContextMiddleware, format_datetime_context
from macsdk.middleware.datetime_context import _calculate_date_references

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


class TestCalculateDateReferences:
    """Tests for _calculate_date_references function."""

    def test_returns_dict_with_expected_keys(self) -> None:
        """Test that function returns dict with all expected keys."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        expected_keys = [
            "yesterday",
            "last_24h",
            "last_7_days",
            "last_30_days",
            "start_of_week",
            "start_of_month",
            "start_of_prev_month",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_all_values_are_iso8601_strings(self) -> None:
        """Test that all returned values are ISO 8601 formatted strings."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        for key, value in result.items():
            assert isinstance(value, str), f"{key} is not a string"
            assert value.endswith("Z"), f"{key} doesn't end with Z"
            assert "T" in value, f"{key} doesn't contain T separator"

    def test_yesterday_calculation(self) -> None:
        """Test yesterday is calculated correctly."""
        # Saturday June 15, 2024
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["yesterday"] == "2024-06-14T00:00:00Z"

    def test_last_24h_calculation(self) -> None:
        """Test last 24 hours is calculated correctly."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["last_24h"] == "2024-06-14T10:30:00Z"

    def test_last_7_days_calculation(self) -> None:
        """Test last 7 days is calculated correctly."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["last_7_days"] == "2024-06-08T00:00:00Z"

    def test_last_30_days_calculation(self) -> None:
        """Test last 30 days is calculated correctly."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["last_30_days"] == "2024-05-16T00:00:00Z"

    def test_start_of_week_monday(self) -> None:
        """Test start of week is Monday at 00:00:00."""
        # Saturday June 15, 2024 -> Monday June 10, 2024
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["start_of_week"] == "2024-06-10T00:00:00Z"

    def test_start_of_week_on_monday(self) -> None:
        """Test start of week when current day is Monday."""
        # Monday June 10, 2024 should return same day
        test_dt = datetime(2024, 6, 10, 14, 0, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["start_of_week"] == "2024-06-10T00:00:00Z"

    def test_start_of_month_calculation(self) -> None:
        """Test start of current month is calculated correctly."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["start_of_month"] == "2024-06-01T00:00:00Z"

    def test_start_of_prev_month_calculation(self) -> None:
        """Test start of previous month is calculated correctly."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["start_of_prev_month"] == "2024-05-01T00:00:00Z"

    def test_start_of_prev_month_january(self) -> None:
        """Test start of previous month when current month is January."""
        # January 15, 2024 -> December 1, 2023
        test_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _calculate_date_references(test_dt)

        assert result["start_of_prev_month"] == "2023-12-01T00:00:00Z"

    def test_format_datetime_context_includes_references(self) -> None:
        """Test that format_datetime_context includes date references."""
        test_dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = format_datetime_context(test_dt)

        # Check pre-calculated dates table is included
        assert "Pre-calculated dates" in result
        assert "Last 7 days" in result
        assert "Last 30 days" in result
        assert "Start of this week" in result
        assert "Start of this month" in result
        assert "Start of last month" in result

        # Check specific dates are in output
        assert "2024-06-08T00:00:00Z" in result  # 7 days ago
        assert "2024-06-10T00:00:00Z" in result  # Monday
        assert "2024-06-01T00:00:00Z" in result  # Start of June
        assert "2024-05-01T00:00:00Z" in result  # Start of May
