"""Response models for DevOps Specialist.

By default, agents use BaseAgentResponse which provides:
- response_text: str - Human-readable response
- tools_used: list[str] - Tools that were called

This is sufficient for most agents. The supervisor receives
the response_text via the tool wrapper.
"""

from __future__ import annotations

from macsdk.core.models import BaseAgentResponse

# Default: Use the SDK's base response directly
AgentResponse = BaseAgentResponse