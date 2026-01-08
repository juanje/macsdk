"""Tests for deprecated TodoListMiddleware."""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock

import pytest

from macsdk.middleware import TodoListMiddleware


def test_import_todo_middleware() -> None:
    """Test that TodoListMiddleware can be imported."""
    assert TodoListMiddleware is not None


def test_todo_middleware_deprecation_warning() -> None:
    """Test that TodoListMiddleware raises a deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        middleware = TodoListMiddleware()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
        assert "CoT prompts" in str(w[0].message)
        assert middleware.enabled is True


def test_todo_middleware_initialization_disabled() -> None:
    """Test TodoListMiddleware initialization with enabled=False."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        middleware = TodoListMiddleware(enabled=False)
        assert middleware.enabled is False


def test_todo_middleware_wrap_model_call_is_noop() -> None:
    """Test that wrap_model_call just passes through to handler."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        middleware = TodoListMiddleware()

    # Create mock request and handler
    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_handler = MagicMock(return_value=mock_response)

    # Call wrap_model_call
    result = middleware.wrap_model_call(mock_request, mock_handler)

    # Verify it just passes through
    mock_handler.assert_called_once_with(mock_request)
    assert result == mock_response


@pytest.mark.asyncio
async def test_todo_middleware_awrap_model_call_is_noop() -> None:
    """Test that awrap_model_call just passes through to handler."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        middleware = TodoListMiddleware()

    # Create mock request and handler
    mock_request = MagicMock()
    mock_response = MagicMock()

    async def mock_handler(request):  # type: ignore[no-untyped-def]
        return mock_response

    # Call awrap_model_call
    result = await middleware.awrap_model_call(mock_request, mock_handler)

    # Verify it just passes through
    assert result == mock_response
