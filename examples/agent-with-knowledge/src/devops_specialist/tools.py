"""Tools for DevOps Specialist agent."""

from __future__ import annotations

from macsdk.tools import api_get, fetch_file, get_sdk_tools

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
    - SDK internal tools (calculate, and knowledge tools if dirs exist)
    - Manual tools (api_get, fetch_file)

    Note:
        Knowledge tools (read_skill, read_fact) are auto-detected.
        Create skills/ or facts/ directories with .md files to enable them.

    Returns:
        List of all tools for the agent.
    """
    _ensure_api_registered()

    return [
        *get_sdk_tools(__package__),  # calculate + auto-detect knowledge
        api_get,
        fetch_file,
    ]
