"""Tools for interacting with DevOps Mock API.

This agent demonstrates how to use MACSDK's API tools for DevOps scenarios:
- Pipeline monitoring and troubleshooting
- Service health checks
- Alert management
- Log retrieval

The pattern shown here is:
1. Register the API service on startup
2. Create domain-specific tools that use api_get from MACSDK
3. Use JSONPath to extract specific fields when needed
4. Use fetch_file to download logs for investigation
"""

from __future__ import annotations

from langchain_core.tools import tool

from macsdk.core.api_registry import register_api_service
from macsdk.tools import api_get, fetch_file

# =============================================================================
# SERVICE REGISTRATION
# =============================================================================

# Register DevOps Mock API as a service
# Hosted on my-json-server.typicode.com using juanje/devops-mock-api repo
register_api_service(
    name="devops",
    base_url="https://my-json-server.typicode.com/juanje/devops-mock-api",
    timeout=10,
    max_retries=2,
)


# =============================================================================
# PIPELINE TOOLS
# =============================================================================


@tool
async def list_pipelines() -> str:
    """List all CI/CD pipelines.

    Returns all pipelines with their status (passed, failed, running, pending).

    Returns:
        List of pipelines as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/pipelines",
        }
    )


@tool
async def get_pipeline(pipeline_id: int) -> str:
    """Get details of a specific pipeline.

    Args:
        pipeline_id: The pipeline's ID.

    Returns:
        Pipeline details as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": f"/pipelines/{pipeline_id}",
        }
    )


@tool
async def get_failed_pipelines() -> str:
    """Get all failed pipelines.

    Useful for quickly identifying pipelines that need attention.

    Returns:
        List of failed pipelines as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/pipelines",
            "params": {"status": "failed"},
        }
    )


@tool
async def get_pipeline_names_by_status(status: str) -> str:
    """Get pipeline names filtered by status.

    Demonstrates using JSONPath to extract specific fields.

    Args:
        status: Pipeline status (passed, failed, running, pending).

    Returns:
        List of pipeline names.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/pipelines",
            "params": {"status": status},
            "extract": "$[*].name",
        }
    )


# =============================================================================
# JOB TOOLS
# =============================================================================


@tool
async def get_jobs_for_pipeline(pipeline_id: int) -> str:
    """Get all jobs for a specific pipeline.

    Returns jobs with their status, duration, and any errors.

    Args:
        pipeline_id: The pipeline's ID.

    Returns:
        List of jobs as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/jobs",
            "params": {"pipelineId": pipeline_id},
        }
    )


@tool
async def get_failed_jobs() -> str:
    """Get all failed jobs across all pipelines.

    Useful for identifying what went wrong in failed pipelines.

    Returns:
        List of failed jobs with error details as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/jobs",
            "params": {"status": "failed"},
        }
    )


@tool
async def get_job(job_id: int) -> str:
    """Get details of a specific job.

    Includes error message and log_url if the job failed.

    Args:
        job_id: The job's ID.

    Returns:
        Job details as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": f"/jobs/{job_id}",
        }
    )


@tool
async def get_job_log(log_url: str) -> str:
    """Download and return the contents of a job log.

    Use this after finding a failed job to investigate the error.
    The log_url can be found in the job's details.

    Args:
        log_url: The URL to the log file (from job's log_url field).

    Returns:
        Log file contents as string.
    """
    return await fetch_file.ainvoke({"url": log_url})


# =============================================================================
# SERVICE HEALTH TOOLS
# =============================================================================


@tool
async def list_services() -> str:
    """List all infrastructure services and their health status.

    Returns services with status (healthy, degraded, warning, critical).

    Returns:
        List of services as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/services",
        }
    )


@tool
async def get_service(service_id: int) -> str:
    """Get details of a specific service.

    Args:
        service_id: The service's ID.

    Returns:
        Service details as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": f"/services/{service_id}",
        }
    )


@tool
async def get_unhealthy_services() -> str:
    """Get services that are not healthy.

    Returns services with status 'degraded', 'warning', or 'critical'.

    Returns:
        List of unhealthy services as JSON string.
    """
    # Get degraded services
    degraded = await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/services",
            "params": {"status": "degraded"},
        }
    )
    warning = await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/services",
            "params": {"status": "warning"},
        }
    )
    return f"Degraded: {degraded}\nWarning: {warning}"


@tool
async def get_service_names_and_status() -> str:
    """Get a summary of all services with their names and status.

    Demonstrates using JSONPath to extract multiple fields.

    Returns:
        Service names and status.
    """
    names = await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/services",
            "extract": "$[*].name",
        }
    )
    statuses = await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/services",
            "extract": "$[*].status",
        }
    )
    return f"Services: {names}\nStatuses: {statuses}"


# =============================================================================
# ALERT TOOLS
# =============================================================================


@tool
async def list_alerts() -> str:
    """List all active alerts.

    Returns alerts with severity (info, warning, critical).

    Returns:
        List of alerts as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/alerts",
        }
    )


@tool
async def get_unacknowledged_alerts() -> str:
    """Get alerts that haven't been acknowledged yet.

    These are alerts that need attention.

    Returns:
        List of unacknowledged alerts as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/alerts",
            "params": {"acknowledged": "false"},
        }
    )


@tool
async def get_critical_alerts() -> str:
    """Get critical severity alerts.

    These are high-priority issues that need immediate attention.

    Returns:
        List of critical alerts as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/alerts",
            "params": {"severity": "critical"},
        }
    )


# =============================================================================
# DEPLOYMENT TOOLS
# =============================================================================


@tool
async def list_deployments() -> str:
    """List all deployments across environments.

    Shows deployment history for production, staging, etc.

    Returns:
        List of deployments as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/deployments",
        }
    )


@tool
async def get_deployment(deployment_id: int) -> str:
    """Get details of a specific deployment.

    Args:
        deployment_id: The deployment's ID.

    Returns:
        Deployment details as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": f"/deployments/{deployment_id}",
        }
    )


@tool
async def get_production_deployments() -> str:
    """Get deployments to production environment.

    Returns:
        List of production deployments as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "devops",
            "endpoint": "/deployments",
            "params": {"environment": "production"},
        }
    )


# =============================================================================
# TOOL LIST (for CLI inspection)
# =============================================================================

TOOLS = [
    # Pipeline tools
    list_pipelines,
    get_pipeline,
    get_failed_pipelines,
    get_pipeline_names_by_status,
    # Job tools
    get_jobs_for_pipeline,
    get_failed_jobs,
    get_job,
    get_job_log,
    # Service health tools
    list_services,
    get_service,
    get_unhealthy_services,
    get_service_names_and_status,
    # Alert tools
    list_alerts,
    get_unacknowledged_alerts,
    get_critical_alerts,
    # Deployment tools
    list_deployments,
    get_deployment,
    get_production_deployments,
]
