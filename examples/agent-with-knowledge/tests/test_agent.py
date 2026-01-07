"""Tests for DevOps Specialist agent."""

from __future__ import annotations

from devops_specialist import DevOpsSpecialist


class TestDevOpsSpecialist:
    """Test suite for DevOps Specialist agent."""

    def test_agent_initialization(self) -> None:
        """Test that agent can be initialized."""
        agent = DevOpsSpecialist()
        assert agent.name == "devops_specialist"
        assert len(agent.tools) > 0

    def test_agent_has_knowledge_tools(self) -> None:
        """Test that agent includes knowledge tools."""
        agent = DevOpsSpecialist()
        tool_names = {tool.name for tool in agent.tools}

        # Should have knowledge tools
        assert "list_skills" in tool_names
        assert "read_skill" in tool_names
        assert "list_facts" in tool_names
        assert "read_fact" in tool_names

    def test_agent_has_calculate_tool(self) -> None:
        """Test that agent includes calculate tool."""
        agent = DevOpsSpecialist()
        tool_names = {tool.name for tool in agent.tools}

        assert "calculate" in tool_names

    def test_agent_capabilities(self) -> None:
        """Test that agent capabilities are defined."""
        agent = DevOpsSpecialist()
        assert "specialist" in agent.capabilities.lower()
        assert "knowledge" in agent.capabilities.lower()

    def test_agent_as_tool(self) -> None:
        """Test that agent can be converted to a tool."""
        agent = DevOpsSpecialist()
        tool = agent.as_tool()

        assert tool.name == "devops_specialist"
        assert callable(tool)
