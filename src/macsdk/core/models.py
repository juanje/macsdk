"""Base models for MACSDK agents.

This module provides base Pydantic models that specialist agents
can inherit from for structured responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BaseAgentResponse(BaseModel):
    """Base model for all specialist agent responses.

    Specialist agents should inherit from this class and add
    their own fields for domain-specific information.

    Attributes:
        response_text: Human-readable response explaining the result.
        tools_used: List of tool names that were used during processing.

    Example:
        >>> class MyAgentResponse(BaseAgentResponse):
        ...     custom_field: str = Field(description="My custom field")
    """

    response_text: str = Field(
        description="Human-readable response explaining the result"
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="List of tool names that were used",
    )
