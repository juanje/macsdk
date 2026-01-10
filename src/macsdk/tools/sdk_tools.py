"""SDK internal tools that are auto-included in agents.

These tools are automatically added to every specialist agent:
- calculate: Safe math evaluation (LLMs are unreliable at arithmetic)
- read_skill: Read skill documents (if skills/ directory exists)
- read_fact: Read fact documents (if facts/ directory exists)

The knowledge tools (read_skill, read_fact) are only added if the
corresponding directories exist AND contain .md files.
"""

from __future__ import annotations

from typing import Any

from .calculate import calculate

__all__ = ["get_sdk_tools", "get_sdk_middleware"]


def get_sdk_tools(package: str | None = None) -> list[Any]:
    """Get SDK-provided tools with auto-detection.

    Always includes:
    - calculate: Safe math evaluation (LLMs need it)

    Conditionally includes (if directories exist with .md files):
    - read_skill: Read skill documents
    - read_fact: Read fact documents

    Args:
        package: Package name for knowledge tools. Use __package__.
            If None, only returns calculate (no knowledge tools).

    Returns:
        List of SDK tools appropriate for the agent.

    Example:
        >>> from macsdk.tools import get_sdk_tools
        >>>
        >>> def get_tools():
        ...     return [
        ...         *get_sdk_tools(__package__),  # calculate + auto-detect
        ...         api_get,
        ...         fetch_file,
        ...     ]
    """
    tools: list[Any] = [calculate]

    if package is not None:
        from .knowledge import get_knowledge_bundle

        knowledge_tools, _ = get_knowledge_bundle(package)
        tools.extend(knowledge_tools)

    return tools


def get_sdk_middleware(package: str | None = None) -> list[Any]:
    """Get SDK-provided middleware with auto-detection.

    Conditionally includes (if directories exist with .md files):
    - ToolInstructionsMiddleware: Injects knowledge inventory into prompt

    Args:
        package: Package name for knowledge middleware. Use __package__.
            If None, returns empty list.

    Returns:
        List of SDK middleware appropriate for the agent.

    Example:
        >>> from macsdk.tools import get_sdk_middleware
        >>>
        >>> def create_my_agent():
        ...     middleware = [
        ...         DatetimeContextMiddleware(),
        ...         *get_sdk_middleware(__package__),  # auto-detect knowledge
        ...     ]
    """
    if package is None:
        return []

    from .knowledge import get_knowledge_bundle

    _, knowledge_middleware = get_knowledge_bundle(package)
    return knowledge_middleware
