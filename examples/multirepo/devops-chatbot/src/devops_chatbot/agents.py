"""Agent registration.

This module registers all specialist agents with the chatbot.
The register_all_agents() function is called when the chatbot starts.
"""

from __future__ import annotations

from typing import Any

from api_agent import ApiAgent

from macsdk.agents import RAGAgent
from macsdk.core import get_registry, register_agent


def register_all_agents() -> None:
    """Register all specialist agents.

    This chatbot includes:
    - RAG Agent: For documentation Q&A (configured via config.yml)
    - API Agent: For interacting with JSONPlaceholder REST API
    """
    registry = get_registry()

    # RAG Agent for documentation Q&A
    # Configure sources, glossary, etc. in config.yml
    if not registry.is_registered("rag_agent"):
        register_agent(RAGAgent())

    # API Agent for REST API interactions (JSONPlaceholder)
    if not registry.is_registered("api_agent"):
        register_agent(ApiAgent())


def get_registered_agents() -> list[dict[str, Any]]:
    """Get information about all registered agents.

    Returns:
        List of dicts with agent info (name, description, tools_count).
    """
    # First ensure agents are registered
    register_all_agents()

    registry = get_registry()
    agents_info: list[dict[str, Any]] = []

    for name, agent in registry.get_all().items():
        info = {
            "name": name,
            "description": getattr(agent, "capabilities", "No description"),
            "tools_count": len(getattr(agent, "tools", [])),
        }
        agents_info.append(info)

    return agents_info
