"""Supervisor agent for orchestrating specialist agents.

The supervisor agent analyzes user queries and routes them to appropriate
specialist agents, orchestrating multiple agents when needed to provide
complete answers.
"""

from .agent import (
    create_supervisor_agent,
    supervisor_agent_node,
)
from .prompts import (
    AGENT_CAPABILITIES_PLACEHOLDER,
    SPECIALIST_PLANNING_PROMPT,
    SUPERVISOR_PROMPT,
    TODO_PLANNING_SPECIALIST_PROMPT,
)

__all__ = [
    "create_supervisor_agent",
    "supervisor_agent_node",
    "AGENT_CAPABILITIES_PLACEHOLDER",
    "SUPERVISOR_PROMPT",
    "SPECIALIST_PLANNING_PROMPT",
    "TODO_PLANNING_SPECIALIST_PROMPT",  # Backward compatibility
]
