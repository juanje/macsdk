"""Built-in agents for MACSDK.

This module provides SDK built-in agents:
- supervisor: Orchestrates specialist agents
- rag: Retrieval-augmented generation (optional)

Example:
    >>> from macsdk.agents import RAGAgent
    >>> from macsdk.core import register_agent
    >>>
    >>> agent = RAGAgent()
    >>> register_agent(agent)
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .rag import RAGAgent

from .formatter import formatter_node
from .supervisor import (
    AGENT_CAPABILITIES_PLACEHOLDER,
    SPECIALIST_PLANNING_PROMPT,
    SUPERVISOR_PROMPT,
    TODO_PLANNING_SPECIALIST_PROMPT,
    create_supervisor_agent,
    supervisor_agent_node,
)

__all__ = [
    # RAG Agent (lazy-loaded to avoid requiring optional dependencies)
    "RAGAgent",
    # Supervisor Agent
    "create_supervisor_agent",
    "supervisor_agent_node",
    "AGENT_CAPABILITIES_PLACEHOLDER",
    "SUPERVISOR_PROMPT",
    "SPECIALIST_PLANNING_PROMPT",
    "TODO_PLANNING_SPECIALIST_PROMPT",
    # Formatter Agent
    "formatter_node",
]


def __getattr__(name: str) -> Any:
    """Lazy import for optional agents.

    RAGAgent requires optional dependencies (langchain_community, chromadb, etc.)
    so we only import it when actually accessed.
    """
    if name == "RAGAgent":
        try:
            from .rag import RAGAgent

            return RAGAgent
        except ImportError as e:
            raise ImportError(
                "RAGAgent requires extra dependencies. "
                "Install with: pip install macsdk[rag]"
            ) from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return list of available attributes including lazy-loaded ones.

    This ensures RAGAgent appears in dir() and IDE autocompletion.
    """
    return list(__all__)
