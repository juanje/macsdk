"""Protocol definition for specialist agents.

This module defines the interface that all specialist agents must implement
to be compatible with the MACSDK framework.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


@runtime_checkable
class SpecialistAgent(Protocol):
    """Protocol that all specialist agents must implement.

    This defines the contract for specialist agents in the MACSDK
    framework. Any agent implementing this protocol can be
    registered and used by the supervisor.

    Attributes:
        name: Unique identifier for the agent (e.g., 'weather_agent').
        capabilities: Human-readable description of what the agent can do.
            This is used by the supervisor to decide which agent to route to.

    Example:
        >>> class MyAgent:
        ...     name = "my_agent"
        ...     capabilities = "Handles my specific domain"
        ...
        ...     async def run(self, query: str, context: dict | None = None) -> dict:
        ...         return {"response": "Hello!", "agent_name": self.name}
        ...
        ...     def as_tool(self) -> BaseTool:
        ...         # Return this agent wrapped as a LangChain tool
        ...         ...
    """

    name: str
    capabilities: str

    async def run(self, query: str, context: dict | None = None) -> dict:
        """Execute the agent with a user query.

        Args:
            query: The user's query string.
            context: Optional context dictionary with additional information
                such as conversation history or previous results.

        Returns:
            A dictionary containing at minimum:
                - 'response': The agent's response text
                - 'agent_name': The name of the agent
                - 'tools_used': List of tools used (optional)
        """
        ...

    def as_tool(self) -> "BaseTool":
        """Return the agent wrapped as a LangChain tool.

        This allows the supervisor to invoke the agent as a tool,
        enabling the agent-as-tool pattern for multi-agent orchestration.

        Returns:
            A BaseTool instance that wraps this agent's run method.
        """
        ...
