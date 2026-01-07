"""Tools for DevOps Specialist agent."""

from __future__ import annotations

from macsdk.tools import api_get, calculate, fetch_file

# =============================================================================
# SERVICE REGISTRATION
# =============================================================================

_api_registered = False


def _ensure_api_registered() -> None:
    """Register the API service on first use."""
    global _api_registered
    if not _api_registered:
        from macsdk.core.api_registry import register_api_service

        # Register DevOps Mock API as a service
        # Replace with your own API endpoint for production use
        register_api_service(
            name="devops",
            base_url="https://my-json-server.typicode.com/juanje/devops-mock-api",
            timeout=10,
            max_retries=2,
        )
        _api_registered = True


def get_tools() -> list:
    """Get all tools for this agent, ensuring API is registered.

    Includes:
    - Generic SDK tools (api_get, fetch_file, calculate)
    - Knowledge tools (list_skills, read_skill, list_facts, read_fact)

    Note: calculate is included by default. LLMs are unreliable at math,
    so always keep this tool available. Do not remove it.

    Returns:
        List of all tools for the agent.
    """
    from macsdk.tools.knowledge import get_knowledge_bundle

    _ensure_api_registered()

    # Get knowledge tools configured for this package
    knowledge_tools, _ = get_knowledge_bundle(__package__)

    return [
        api_get,
        fetch_file,
        calculate,  # Required - LLMs cannot do math reliably
        *knowledge_tools,  # Skills and facts tools
    ]
