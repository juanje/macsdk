"""Middleware module for MACSDK.

This module provides middleware components that can be applied to agents
to enhance their capabilities:

- DatetimeContextMiddleware: Injects current datetime into prompts
- SummarizationMiddleware: Summarizes long conversations

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
from .summarization import SummarizationMiddleware

__all__ = [
    "DatetimeContextMiddleware",
    "SummarizationMiddleware",
    "format_datetime_context",
]
