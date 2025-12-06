"""Agent registry for dynamic agent management.

This module provides a centralized registry for specialist agents,
allowing dynamic registration and discovery of agents at runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

    from .protocol import SpecialistAgent


class AgentRegistry:
    """Registry for managing specialist agents.

    This class provides a centralized way to register, retrieve, and
    manage specialist agents in the MACSDK framework.

    The registry is designed to be used as a singleton, but can also
    be instantiated for testing or isolated use cases.

    Example:
        >>> registry = AgentRegistry()
        >>> registry.register(my_agent)
        >>> all_agents = registry.get_all()
        >>> tools = registry.get_all_as_tools()
    """

    def __init__(self) -> None:
        """Initialize an empty agent registry."""
        self._agents: dict[str, SpecialistAgent] = {}

    def register(self, agent: "SpecialistAgent") -> None:
        """Register a specialist agent.

        Args:
            agent: The agent to register. Must implement SpecialistAgent protocol.

        Raises:
            ValueError: If an agent with the same name is already registered.
        """
        if agent.name in self._agents:
            raise ValueError(
                f"Agent '{agent.name}' is already registered. "
                "Use unregister() first if you want to replace it."
            )
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        """Unregister an agent by name.

        Args:
            name: The name of the agent to unregister.

        Raises:
            KeyError: If no agent with that name is registered.
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' is not registered.")
        del self._agents[name]

    def get(self, name: str) -> "SpecialistAgent":
        """Get a registered agent by name.

        Args:
            name: The name of the agent to retrieve.

        Returns:
            The registered agent.

        Raises:
            KeyError: If no agent with that name is registered.
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' is not registered.")
        return self._agents[name]

    def get_all(self) -> dict[str, "SpecialistAgent"]:
        """Get all registered agents.

        Returns:
            A dictionary mapping agent names to agent instances.
        """
        return dict(self._agents)

    def get_capabilities(self) -> dict[str, str]:
        """Get capabilities of all registered agents.

        Returns:
            A dictionary mapping agent names to their capability descriptions.
        """
        return {name: agent.capabilities for name, agent in self._agents.items()}

    def get_all_as_tools(self) -> list["BaseTool"]:
        """Get all registered agents as LangChain tools.

        Returns:
            A list of BaseTool instances, one for each registered agent.
        """
        return [agent.as_tool() for agent in self._agents.values()]

    def is_registered(self, name: str) -> bool:
        """Check if an agent is registered.

        Args:
            name: The name of the agent to check.

        Returns:
            True if the agent is registered, False otherwise.
        """
        return name in self._agents

    def clear(self) -> None:
        """Clear all registered agents.

        This is mainly useful for testing.
        """
        self._agents.clear()

    def __len__(self) -> int:
        """Return the number of registered agents."""
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        """Check if an agent is registered using 'in' operator."""
        return name in self._agents


# Global registry instance for convenience
_global_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance.

    Returns:
        The global AgentRegistry instance.
    """
    return _global_registry


def register_agent(agent: "SpecialistAgent") -> None:
    """Register an agent in the global registry.

    This is a convenience function that registers an agent in the
    global registry instance.

    Args:
        agent: The agent to register.
    """
    _global_registry.register(agent)


def get_all_capabilities() -> dict[str, str]:
    """Get capabilities of all agents in the global registry.

    Returns:
        A dictionary mapping agent names to their capability descriptions.
    """
    return _global_registry.get_capabilities()


def get_all_agent_tools() -> list["BaseTool"]:
    """Get all agents as tools from the global registry.

    Returns:
        A list of BaseTool instances for all registered agents.
    """
    return _global_registry.get_all_as_tools()
