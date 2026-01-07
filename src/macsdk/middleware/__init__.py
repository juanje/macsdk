"""Middleware module for MACSDK.

This module provides middleware components that can be applied to agents
to enhance their capabilities:

- DatetimeContextMiddleware: Injects current datetime into prompts
- SummarizationMiddleware: Summarizes long conversations
- PromptDebugMiddleware: Displays prompts sent to the LLM for debugging
- ToolInstructionsMiddleware: Injects usage instructions for tool sets
- TodoListMiddleware: Task planning capabilities

Example:
    >>> from macsdk.middleware import DatetimeContextMiddleware, SummarizationMiddleware
    >>>
    >>> middleware = [
    ...     DatetimeContextMiddleware(),
    ...     SummarizationMiddleware(trigger_tokens=50000),
    ... ]
    >>> agent = create_agent(model=..., tools=..., middleware=middleware)
"""

from .datetime_context import (
    DatetimeContextMiddleware,
    format_datetime_context,
)
from .debug_prompts import PromptDebugMiddleware
from .summarization import SummarizationMiddleware
from .todo import TodoListMiddleware
from .tool_instructions import ToolInstructionsMiddleware

__all__ = [
    "DatetimeContextMiddleware",
    "PromptDebugMiddleware",
    "SummarizationMiddleware",
    "TodoListMiddleware",
    "ToolInstructionsMiddleware",
    "format_datetime_context",
]
