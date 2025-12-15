"""Integration tests for chatbot + agent registration.

These tests verify that:
1. An agent can be registered in a chatbot
2. The registered agent is available to the supervisor
3. The chatbot can route queries to the agent
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import run_uv_command

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestAgentRegistration:
    """Tests for registering agents in chatbots."""

    def test_agent_can_be_imported_in_chatbot(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """Agent can be imported from within the chatbot project."""
        check_code = """
from integration_agent import IntegrationAgent
print('IMPORT_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
        )

        assert "IMPORT_OK" in result.stdout

    def test_agent_registration_works(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """Agent can be registered in the chatbot registry."""
        check_code = """
from macsdk.core import get_registry, register_agent
from integration_agent import IntegrationAgent

# Clear and register
registry = get_registry()
registry.clear()

agent = IntegrationAgent()
register_agent(agent)

# Verify registration
agents = registry.get_all()
assert agent.name in agents, f"Agent not in registry: {list(agents.keys())}"

print('REGISTRATION_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
        )

        assert "REGISTRATION_OK" in result.stdout

    def test_agent_appears_in_capabilities(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """Registered agent capabilities are included in supervisor prompt."""
        check_code = """
from macsdk.core import get_registry, register_agent, get_all_capabilities
from integration_agent import IntegrationAgent

# Clear and register
registry = get_registry()
registry.clear()

agent = IntegrationAgent()
register_agent(agent)

# Get capabilities
capabilities = get_all_capabilities()

caps_keys = list(capabilities.keys())
assert agent.name in capabilities, f"Agent not found: {caps_keys}"
assert len(capabilities[agent.name]) > 0, "Agent capabilities are empty"

print('CAPABILITIES_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
        )

        assert "CAPABILITIES_OK" in result.stdout

    def test_agent_tool_is_created(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """Registered agent generates a valid LangChain tool."""
        check_code = """
from macsdk.core import get_registry, register_agent, get_all_agent_tools
from integration_agent import IntegrationAgent

# Clear and register
registry = get_registry()
registry.clear()

agent = IntegrationAgent()
register_agent(agent)

# Get tools
tools = get_all_agent_tools()

assert len(tools) == 1, f"Expected 1 tool, got {len(tools)}"

tool = tools[0]
assert hasattr(tool, 'name'), "Tool missing 'name'"
assert hasattr(tool, 'invoke') or hasattr(tool, 'ainvoke'), "Tool not invokable"
assert 'integration_agent' in tool.name.lower(), f"Tool name mismatch: {tool.name}"

print('TOOL_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
        )

        assert "TOOL_OK" in result.stdout

    def test_register_agents_function_works(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """The chatbot's register_agents() function works correctly."""
        check_code = """
from macsdk.core import get_registry
from integration_chatbot.agents import register_agents

# Clear registry
registry = get_registry()
registry.clear()

# Call register function
register_agents()

# Verify
agents = registry.get_all()
assert len(agents) > 0, "No agents registered"
assert 'integration_agent' in agents, f"Agent not found: {list(agents.keys())}"

print('REGISTER_FUNC_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
        )

        assert "REGISTER_FUNC_OK" in result.stdout


class TestChatbotWithAgent:
    """Tests for chatbot functionality with registered agent."""

    def test_full_integration_agent_to_supervisor(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """Verify integration: agent registered, tool created, used by supervisor."""
        check_code = """
from macsdk.core import get_registry, get_all_agent_tools, get_all_capabilities
from integration_chatbot.agents import register_agents

# 1. Register agents from chatbot
get_registry().clear()
register_agents()

# 2. Verify agent is registered
agents = get_registry().get_all()
assert 'integration_agent' in agents, f"Agent not registered: {list(agents.keys())}"
print(f"✓ Agent registered: integration_agent")

# 3. Verify capabilities are available (for supervisor prompt)
caps = get_all_capabilities()
assert 'integration_agent' in caps, f"Capabilities missing: {list(caps.keys())}"
assert len(caps['integration_agent']) > 0, "Empty capabilities"
print(f"✓ Capabilities available: {caps['integration_agent'][:50]}...")

# 4. Verify tool is created with correct interface
tools = get_all_agent_tools()
assert len(tools) == 1, f"Expected 1 tool, got {len(tools)}"

tool = tools[0]
assert 'integration_agent' in tool.name.lower()
assert hasattr(tool, 'ainvoke') and callable(tool.ainvoke)
assert hasattr(tool, 'description') and len(tool.description) > 10
print(f"✓ Tool created: {tool.name}")
print(f"✓ Tool description: {tool.description[:60]}...")

# 5. Verify tool schema (what LLM sees)
schema = tool.args_schema.model_json_schema() if tool.args_schema else {}
print(f"✓ Tool has schema: {bool(schema)}")

print('FULL_INTEGRATION_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
            timeout=30,
        )

        assert "FULL_INTEGRATION_OK" in result.stdout, f"Test failed: {result.stderr}"

    def test_graph_creation_with_agent(
        self,
        chatbot_with_agent: Path,
    ) -> None:
        """Chatbot graph can be created with registered agent."""
        check_code = """
from macsdk.core import create_chatbot_graph
from integration_chatbot.agents import register_agents

# This should not raise any errors
graph = create_chatbot_graph(register_agents_func=register_agents)

assert graph is not None, "Graph creation failed"
assert hasattr(graph, 'ainvoke'), "Graph not invokable"

print('GRAPH_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=chatbot_with_agent,
        )

        assert "GRAPH_OK" in result.stdout
