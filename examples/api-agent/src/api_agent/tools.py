"""Tools for interacting with DevOps Mock API.

This agent demonstrates TWO approaches to using MACSDK's API tools:

## Approach 1: Generic Tools (Recommended for flexibility)
Use `api_get` and `fetch_file` directly, with API schema in the prompt.
The LLM decides which endpoints to call based on user queries.

## Approach 2: Custom Tools (Recommended for specific use cases)
Create domain-specific tools using `make_api_request` for:
- Complex operations that combine multiple API calls
- Extracting specific fields with JSONPath
- Adding business logic or transformations

This example uses Approach 1 as primary, with a few custom tools
demonstrating Approach 2 for advanced scenarios.
"""

from __future__ import annotations

from langchain_core.tools import tool

from macsdk.core.api_registry import register_api_service
from macsdk.tools import api_get, fetch_file, make_api_request

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
# APPROACH 2: CUSTOM TOOLS (Examples using make_api_request with extract)
# =============================================================================
# These demonstrate how to create specialized tools when you need:
# - JSONPath extraction for specific fields
# - Business logic or data transformation
# - Combining multiple API calls


@tool
async def get_service_health_summary() -> str:
    """Get a quick summary of all services health.

    This custom tool demonstrates using make_api_request with JSONPath
    to extract only the fields we need, reducing response size.

    Returns:
        Formatted summary of service names and their status.
    """
    # Use make_api_request with extract for JSONPath
    names_result = await make_api_request(
        "GET",
        "devops",
        "/services",
        extract="$[*].name",
    )
    statuses_result = await make_api_request(
        "GET",
        "devops",
        "/services",
        extract="$[*].status",
    )

    if not names_result["success"] or not statuses_result["success"]:
        return "Error fetching service health"

    names = names_result["data"]
    statuses = statuses_result["data"]

    # Format as readable summary
    summary = []
    for name, status in zip(names, statuses):
        emoji = {"healthy": "✅", "degraded": "⚠️", "warning": "🔶"}.get(status, "❌")
        summary.append(f"{emoji} {name}: {status}")

    return "\n".join(summary)


@tool
async def get_failed_pipeline_names() -> str:
    """Get just the names of failed pipelines.

    Demonstrates extracting specific fields to reduce token usage
    when you only need certain information.

    Returns:
        List of failed pipeline names.
    """
    result = await make_api_request(
        "GET",
        "devops",
        "/pipelines",
        params={"status": "failed"},
        extract="$[*].name",
    )

    if not result["success"]:
        return f"Error: {result.get('error', 'Unknown error')}"

    names = result["data"]
    if not names:
        return "No failed pipelines found"

    return f"Failed pipelines: {', '.join(names)}"


@tool
async def investigate_failed_job(job_id: int) -> str:
    """Investigate a failed job by fetching details and log.

    This custom tool combines multiple API calls and file fetching
    into a single operation for convenience.

    Args:
        job_id: The ID of the failed job to investigate.

    Returns:
        Job details with error information and relevant log excerpt.
    """
    # Get job details
    job_result = await make_api_request("GET", "devops", f"/jobs/{job_id}")

    if not job_result["success"]:
        return f"Error fetching job: {job_result.get('error')}"

    job = job_result["data"]

    # Build response
    response = [
        f"## Job: {job.get('name', 'Unknown')} (ID: {job_id})",
        f"Status: {job.get('status', 'Unknown')}",
        f"Pipeline ID: {job.get('pipelineId', 'Unknown')}",
        f"Duration: {job.get('duration', 'Unknown')}",
    ]

    if job.get("error"):
        response.append(f"Error: {job['error']}")

    # Fetch log if available
    log_url = job.get("log_url")
    if log_url:
        log_content = await fetch_file.ainvoke({"url": log_url})
        # Extract last 20 lines or error section
        log_lines = log_content.strip().split("\n")
        relevant_lines = log_lines[-20:] if len(log_lines) > 20 else log_lines
        response.append("\n### Log excerpt:")
        response.append("```")
        response.extend(relevant_lines)
        response.append("```")

    return "\n".join(response)


# =============================================================================
# TOOLS LIST
# =============================================================================

def get_tools() -> list:
    """Get all tools for this agent.

    Returns both generic SDK tools (for flexible API access)
    and custom tools (for specialized operations).
    """
    return [
        # Generic SDK tools - LLM uses these with any endpoint
        api_get,
        fetch_file,
        # Custom tools - specialized operations with business logic
        get_service_health_summary,
        get_failed_pipeline_names,
        investigate_failed_job,
    ]


# For CLI inspection
TOOLS = get_tools()
