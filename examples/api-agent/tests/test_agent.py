"""Tests for api-agent.

These tests verify that the agent implements the
SpecialistAgent protocol correctly and that tools work.
"""

import pytest
from api_agent import CAPABILITIES, ApiAgentAgent
from api_agent.tools import get_service_status, search_logs


class TestApiAgentAgent:
    """Tests for ApiAgentAgent."""

    def test_has_required_attributes(self) -> None:
        """Agent has required protocol attributes."""
        agent = ApiAgentAgent()
        assert hasattr(agent, "name")
        assert hasattr(agent, "capabilities")
        assert agent.name == "api_agent"

    def test_capabilities_not_empty(self) -> None:
        """Capabilities description is not empty."""
        assert CAPABILITIES
        assert len(CAPABILITIES) > 0

    def test_has_run_method(self) -> None:
        """Agent has async run method."""
        agent = ApiAgentAgent()
        assert hasattr(agent, "run")
        assert callable(agent.run)

    def test_has_as_tool_method(self) -> None:
        """Agent has as_tool method."""
        agent = ApiAgentAgent()
        assert hasattr(agent, "as_tool")
        assert callable(agent.as_tool)


class TestTools:
    """Tests for agent tools."""

    @pytest.mark.asyncio
    async def test_get_service_status_known_service(self) -> None:
        """get_service_status returns info for known services."""
        # The tool is decorated, so we call .invoke() or the underlying func
        result = await get_service_status.ainvoke({"service_name": "api-gateway"})
        assert "api-gateway" in result
        assert "healthy" in result

    @pytest.mark.asyncio
    async def test_get_service_status_unknown_service(self) -> None:
        """get_service_status handles unknown services."""
        result = await get_service_status.ainvoke({"service_name": "unknown-service"})
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_search_logs_finds_matches(self) -> None:
        """search_logs finds matching entries."""
        result = await search_logs.ainvoke({"query": "ERROR"})
        assert "ERROR" in result
        assert "Found" in result

    @pytest.mark.asyncio
    async def test_search_logs_no_matches(self) -> None:
        """search_logs handles no matches gracefully."""
        result = await search_logs.ainvoke({"query": "nonexistent-pattern-xyz"})
        assert "No logs found" in result
