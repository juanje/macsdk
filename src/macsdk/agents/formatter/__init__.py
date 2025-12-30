"""Response Formatter Agent.

This module provides the formatter agent that synthesizes and formats
the final response to users based on raw agent results.
"""

from .agent import formatter_node
from .prompts import (
    FORMATTER_CORE_PROMPT,
    FORMATTER_EXTRA_PROMPT,
    FORMATTER_FORMAT_PROMPT,
    FORMATTER_TONE_PROMPT,
)

__all__ = [
    "formatter_node",
    "FORMATTER_CORE_PROMPT",
    "FORMATTER_TONE_PROMPT",
    "FORMATTER_FORMAT_PROMPT",
    "FORMATTER_EXTRA_PROMPT",
]
