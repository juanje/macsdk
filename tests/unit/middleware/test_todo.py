"""Tests for TodoListMiddleware."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from macsdk.middleware import TodoListMiddleware


def test_import_todo_middleware() -> None:
    """Test that TodoListMiddleware can be imported."""
    assert TodoListMiddleware is not None


def test_todo_middleware_initialization() -> None:
    """Test TodoListMiddleware initialization with default parameters."""
    middleware = TodoListMiddleware()
    assert middleware.enabled is True


def test_todo_middleware_initialization_disabled() -> None:
    """Test TodoListMiddleware initialization with enabled=False."""
    middleware = TodoListMiddleware(enabled=False)
    assert middleware.enabled is False


def test_todo_middleware_initialization_enabled() -> None:
    """Test TodoListMiddleware initialization with enabled=True."""
    middleware = TodoListMiddleware(enabled=True)
    assert middleware.enabled is True


def test_todo_middleware_is_langchain_subclass() -> None:
    """Test that TodoListMiddleware inherits from LangChain's TodoListMiddleware."""
    from langchain.agents.middleware import TodoListMiddleware as LCTodoListMiddleware

    middleware = TodoListMiddleware()
    assert isinstance(middleware, LCTodoListMiddleware)


@pytest.mark.asyncio
async def test_todo_middleware_with_supervisor() -> None:
    """Test that TodoListMiddleware is always integrated with supervisor agent."""
    from macsdk.agents.supervisor import create_supervisor_agent

    # Mock the LLM model to avoid requiring API key
    mock_model = MagicMock()
    with patch(
        "macsdk.agents.supervisor.agent.get_answer_model", return_value=mock_model
    ):
        # Should not raise any errors - TODO is always enabled
        agent = create_supervisor_agent()
        assert agent is not None
