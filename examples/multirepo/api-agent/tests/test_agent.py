"""Tests for api-agent.

These tests verify that the agent implements the
SpecialistAgent protocol correctly and that tools work.
"""

from api_agent import CAPABILITIES, ApiAgent
from api_agent.tools import get_tools


class TestApiAgent:
    """Tests for ApiAgent."""

    def test_has_required_attributes(self) -> None:
        """Agent has required protocol attributes."""
        agent = ApiAgent()
        assert hasattr(agent, "name")
        assert hasattr(agent, "capabilities")
        assert agent.name == "api_agent"

    def test_capabilities_not_empty(self) -> None:
        """Capabilities description is not empty."""
        assert CAPABILITIES
        assert len(CAPABILITIES) > 0

    def test_has_run_method(self) -> None:
        """Agent has async run method."""
        agent = ApiAgent()
        assert hasattr(agent, "run")
        assert callable(agent.run)

    def test_has_as_tool_method(self) -> None:
        """Agent has as_tool method."""
        agent = ApiAgent()
        assert hasattr(agent, "as_tool")
        assert callable(agent.as_tool)


class TestTools:
    """Tests for agent tools."""

    def test_get_tools_returns_list(self) -> None:
        """get_tools returns a list of tools."""
        tools = get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_names(self) -> None:
        """All tools have name attribute."""
        tools = get_tools()
        for tool in tools:
            assert hasattr(tool, "name"), f"Tool missing name: {tool}"

    def test_tools_are_invokable(self) -> None:
        """All tools have invoke or ainvoke method."""
        tools = get_tools()
        for tool in tools:
            has_invoke = hasattr(tool, "invoke") or hasattr(tool, "ainvoke")
            assert has_invoke, f"Tool not invokable: {tool.name}"
