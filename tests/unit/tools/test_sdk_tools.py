"""Tests for SDK internal tools (get_sdk_tools, get_sdk_middleware)."""

from __future__ import annotations

from macsdk.tools.sdk_tools import get_sdk_middleware, get_sdk_tools


def test_get_sdk_tools_always_includes_calculate() -> None:
    """Test that calculate is always included."""
    tools = get_sdk_tools(None)

    assert len(tools) == 1
    assert tools[0].name == "calculate"


def test_get_sdk_tools_returns_list() -> None:
    """Test that get_sdk_tools returns a list."""
    tools = get_sdk_tools(None)
    assert isinstance(tools, list)
    assert len(tools) >= 1  # At least calculate


def test_get_sdk_middleware_returns_empty_without_package() -> None:
    """Test that get_sdk_middleware returns empty list without package."""
    middleware = get_sdk_middleware(None)
    assert middleware == []
    assert isinstance(middleware, list)


def test_get_sdk_tools_with_package() -> None:
    """Test that get_sdk_tools includes knowledge tools when package provided."""
    from unittest.mock import MagicMock, patch

    with patch("macsdk.tools.knowledge.get_knowledge_bundle") as mock_get:
        mock_tool = MagicMock()
        mock_tool.name = "read_skill"
        mock_get.return_value = ([mock_tool], [])

        tools = get_sdk_tools("dummy_package")

        assert len(tools) == 2  # calculate + mock_tool
        assert tools[0].name == "calculate"
        assert tools[1] == mock_tool
        mock_get.assert_called_once_with("dummy_package")


def test_get_sdk_middleware_with_package() -> None:
    """Test get_sdk_middleware includes knowledge middleware with package."""
    from unittest.mock import MagicMock, patch

    with patch("macsdk.tools.knowledge.get_knowledge_bundle") as mock_get:
        mock_middleware = MagicMock()
        mock_get.return_value = ([], [mock_middleware])

        middleware = get_sdk_middleware("dummy_package")

        assert len(middleware) == 1
        assert middleware[0] == mock_middleware
        mock_get.assert_called_once_with("dummy_package")
