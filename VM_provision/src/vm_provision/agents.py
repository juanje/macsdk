"""Agent registration.

This module registers all specialist agents with the chatbot.
The register_all_agents() function is called when the chatbot starts.
"""

from __future__ import annotations

from typing import Any

from macsdk.core import get_registry, register_agent

# --- BEGIN AGENT IMPORTS ---
from .local_agents.vm_agent import VmAgent

def register_all_agents() -> None:
    """Register all specialist agents.

    Add your agents here. Example:

        from my_agent import MyAgent

        if not registry.is_registered("my_agent"):
            register_agent(MyAgent())

    Or use the CLI to add agents:

        macsdk add-agent . --package my-agent
    """
    registry = get_registry()

    # --- BEGIN AGENT REGISTRATION ---
    if not registry.is_registered("vm_agent"):
        register_agent(VmAgent())

    _ = registry  # Avoid unused variable warning


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
