"""Prompt templates for MACSDK.

Note: Prompts are now organized per-agent in agents/<agent>/prompts.py
This file re-exports for backward compatibility.
"""

# Re-export supervisor prompts for backward compatibility
# Re-export formatter prompts for convenience
from .agents.formatter.prompts import (
    FORMATTER_CORE_PROMPT,
    FORMATTER_EXTRA_PROMPT,
    FORMATTER_FORMAT_PROMPT,
    FORMATTER_PROMPT,
    FORMATTER_TONE_PROMPT,
    build_formatter_prompt,
)
from .agents.supervisor.prompts import (
    AGENT_CAPABILITIES_PLACEHOLDER,
    SPECIALIST_PLANNING_PROMPT,
    SUPERVISOR_PROMPT,
    TODO_PLANNING_SPECIALIST_PROMPT,
)

__all__ = [
    # Supervisor prompts
    "AGENT_CAPABILITIES_PLACEHOLDER",
    "SUPERVISOR_PROMPT",
    "SPECIALIST_PLANNING_PROMPT",
    "TODO_PLANNING_SPECIALIST_PROMPT",  # Backward compatibility
    # Formatter prompts
    "FORMATTER_CORE_PROMPT",
    "FORMATTER_TONE_PROMPT",
    "FORMATTER_FORMAT_PROMPT",
    "FORMATTER_EXTRA_PROMPT",
    "FORMATTER_PROMPT",
    "build_formatter_prompt",
]
