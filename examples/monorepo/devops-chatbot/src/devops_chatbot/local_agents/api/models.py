"""Response models for api-agent.

Define structured responses that the agent returns.
The supervisor uses these to understand agent output.

BaseAgentResponse already includes:
- response_text: str - Human-readable response
- tools_used: list[str] - Tools that were called

This example shows fields relevant for DevOps monitoring.
"""

from pydantic import Field

from macsdk.core import BaseAgentResponse


class AgentResponse(BaseAgentResponse):
    """Response model for DevOps monitoring agent.

    These fields capture structured data from API queries about
    services, pipelines, alerts, and deployments.
    """

    # Service health summary
    services_healthy: int = Field(default=0, description="Number of healthy services")
    services_degraded: int = Field(default=0, description="Number of degraded services")
    services_warning: int = Field(
        default=0, description="Number of services with warnings"
    )

    # Pipeline status
    pipeline_id: str | None = Field(
        default=None, description="Pipeline ID if querying specific pipeline"
    )
    pipeline_status: str | None = Field(
        default=None, description="Pipeline status (passed/failed/running/pending)"
    )
    failed_jobs: list[str] = Field(
        default_factory=list, description="Names of failed jobs"
    )

    # Alerts summary
    critical_alerts: int = Field(default=0, description="Number of critical alerts")
    unacknowledged_alerts: int = Field(
        default=0, description="Number of unacknowledged alerts"
    )

    # Error information (for failed jobs/pipelines)
    error_summary: str | None = Field(
        default=None, description="Summary of errors found"
    )
    log_urls: list[str] = Field(
        default_factory=list, description="URLs to relevant logs"
    )
