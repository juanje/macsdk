"""Tests for AgentRegistry."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from macsdk.core import (
    AgentRegistry,
    get_all_agent_tools,
    get_all_capabilities,
    get_registry,
    register_agent,
)

if TYPE_CHECKING:
    from tests.conftest import MockAgent

# Test constants for this module
AGENT_1_NAME = "agent1"
AGENT_2_NAME = "agent2"
AGENT_1_CAPS = "Agent 1 capabilities"
AGENT_2_CAPS = "Agent 2 capabilities"
NONEXISTENT_AGENT = "nonexistent_agent"


class TestAgentRegistry:
    """Tests for the AgentRegistry class."""

    def test_init_creates_empty_registry(self) -> None:
        """New registry is empty."""
        registry = AgentRegistry()
        assert len(registry) == 0

    def test_register_agent(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """Can register an agent."""
        clean_registry.register(mock_agent)
        assert mock_agent.name in clean_registry
        assert len(clean_registry) == 1

    def test_register_duplicate_raises_error(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """Registering same agent twice raises error."""
        clean_registry.register(mock_agent)
        with pytest.raises(ValueError, match="already registered"):
            clean_registry.register(mock_agent)

    def test_unregister_agent(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """Can unregister an agent."""
        clean_registry.register(mock_agent)
        clean_registry.unregister(mock_agent.name)
        assert mock_agent.name not in clean_registry

    def test_unregister_nonexistent_raises_error(
        self, clean_registry: AgentRegistry
    ) -> None:
        """Unregistering non-existent agent raises error."""
        with pytest.raises(KeyError, match="not registered"):
            clean_registry.unregister(NONEXISTENT_AGENT)

    def test_get_agent(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """Can retrieve a registered agent."""
        clean_registry.register(mock_agent)
        retrieved = clean_registry.get(mock_agent.name)
        assert retrieved is mock_agent

    def test_get_nonexistent_raises_error(self, clean_registry: AgentRegistry) -> None:
        """Getting non-existent agent raises error."""
        with pytest.raises(KeyError, match="not registered"):
            clean_registry.get(NONEXISTENT_AGENT)

    def test_get_all(self, mock_agent_factory, clean_registry: AgentRegistry) -> None:
        """Can get all registered agents."""
        agent1 = mock_agent_factory(AGENT_1_NAME)
        agent2 = mock_agent_factory(AGENT_2_NAME)
        clean_registry.register(agent1)
        clean_registry.register(agent2)

        all_agents = clean_registry.get_all()
        assert len(all_agents) == 2
        assert AGENT_1_NAME in all_agents
        assert AGENT_2_NAME in all_agents

    def test_get_capabilities(
        self, mock_agent_factory, clean_registry: AgentRegistry
    ) -> None:
        """Can get capabilities of all agents."""
        agent1 = mock_agent_factory(AGENT_1_NAME, AGENT_1_CAPS)
        agent2 = mock_agent_factory(AGENT_2_NAME, AGENT_2_CAPS)
        clean_registry.register(agent1)
        clean_registry.register(agent2)

        caps = clean_registry.get_capabilities()
        assert caps[AGENT_1_NAME] == AGENT_1_CAPS
        assert caps[AGENT_2_NAME] == AGENT_2_CAPS

    def test_get_all_as_tools(
        self, mock_agent_factory, clean_registry: AgentRegistry
    ) -> None:
        """Can get all agents as tools."""
        agent1 = mock_agent_factory(AGENT_1_NAME)
        agent2 = mock_agent_factory(AGENT_2_NAME)
        clean_registry.register(agent1)
        clean_registry.register(agent2)

        tools = clean_registry.get_all_as_tools()
        assert len(tools) == 2

    def test_is_registered(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """Can check if agent is registered."""
        assert not clean_registry.is_registered(mock_agent.name)
        clean_registry.register(mock_agent)
        assert clean_registry.is_registered(mock_agent.name)

    def test_clear(self, mock_agent_factory, clean_registry: AgentRegistry) -> None:
        """Can clear all agents."""
        clean_registry.register(mock_agent_factory(AGENT_1_NAME))
        clean_registry.register(mock_agent_factory(AGENT_2_NAME))
        assert len(clean_registry) == 2

        clean_registry.clear()
        assert len(clean_registry) == 0

    def test_contains(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """Can use 'in' operator."""
        clean_registry.register(mock_agent)
        assert mock_agent.name in clean_registry
        assert NONEXISTENT_AGENT not in clean_registry


class TestGlobalRegistryFunctions:
    """Tests for global registry convenience functions."""

    def test_get_registry_returns_singleton(self) -> None:
        """get_registry returns the same instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_register_agent_function(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """register_agent convenience function works."""
        register_agent(mock_agent)
        assert mock_agent.name in clean_registry

    def test_get_all_capabilities_function(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """get_all_capabilities convenience function works."""
        clean_registry.register(mock_agent)
        caps = get_all_capabilities()
        assert mock_agent.name in caps

    def test_get_all_agent_tools_function(
        self, mock_agent: "MockAgent", clean_registry: AgentRegistry
    ) -> None:
        """get_all_agent_tools convenience function works."""
        clean_registry.register(mock_agent)
        tools = get_all_agent_tools()
        assert len(tools) == 1
