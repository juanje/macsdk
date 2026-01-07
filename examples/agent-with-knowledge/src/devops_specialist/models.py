"""Response models for DevOps Specialist.

This module defines the response format for the agent.
You can extend BaseAgentResponse with additional fields if needed.
"""

from __future__ import annotations

from macsdk.core.models import BaseAgentResponse


class AgentResponse(BaseAgentResponse):
    """Response model for DevOps Specialist.

    Inherits from BaseAgentResponse and can be extended with additional fields.

    By default, this class doesn't add any fields, but you can customize it:

    Example:
        class AgentResponse(BaseAgentResponse):
            # Add custom fields for your agent
            confidence_score: float = 0.0
            processing_time_ms: int = 0
            data_sources_used: list[str] = []
    """

    pass
