"""Knowledge tools module for MACSDK.

This module provides skills and facts tools that help agents access
task instructions and contextual information packaged with the agent.

Example:
    >>> from macsdk.tools.knowledge import get_knowledge_bundle
    >>>
    >>> # Get tools and middleware configured for your package
    >>> knowledge_tools, knowledge_middleware = get_knowledge_bundle(__package__)
    >>>
    >>> # Use in agent creation
    >>> agent = create_agent(
    ...     tools=[*my_tools, *knowledge_tools],
    ...     middleware=[*my_middleware, *knowledge_middleware],
    ... )
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

from .facts import create_facts_tools
from .skills import create_skills_tools

__all__ = ["get_knowledge_bundle"]


def get_knowledge_bundle(
    package: str,
    skills_subdir: str = "skills",
    facts_subdir: str = "facts",
    include_skills: bool = True,
    include_facts: bool = True,
) -> tuple[list[Any], list[Any]]:
    """Get knowledge tools and middleware for a package.

    This is a convenience function that returns tools and middleware
    configured correctly for the knowledge system. The middleware
    auto-detects which tools are included and injects appropriate
    usage instructions along with the inventory of available skills/facts.

    Args:
        package: Package name. Use __package__ for current package.
        skills_subdir: Subdirectory for skills (default: "skills").
        facts_subdir: Subdirectory for facts (default: "facts").
        include_skills: Include skills tools (read_skill).
        include_facts: Include facts tools (read_fact).

    Returns:
        Tuple of (tools, middleware).

    Example:
        >>> from macsdk.tools.knowledge import get_knowledge_bundle
        >>>
        >>> knowledge_tools, knowledge_mw = get_knowledge_bundle(__package__)
        >>> agent = create_agent(
        ...     tools=[*my_tools, *knowledge_tools],
        ...     middleware=[*my_mw, *knowledge_mw],
        ...     system_prompt=SYSTEM_PROMPT,
        ... )

    Example with partial inclusion:
        >>> # Only include skills, not facts
        >>> tools, middleware = get_knowledge_bundle(
        ...     __package__,
        ...     include_skills=True,
        ...     include_facts=False,
        ... )
    """
    from ...middleware import ToolInstructionsMiddleware

    # Note: This implementation assumes the package is installed as an extracted
    # directory (standard pip install). It will not work with zip-safe deployments
    # (e.g., zipapps or unextracted eggs) as the tools need persistent filesystem
    # paths. For production deployments, ensure packages are installed normally.
    package_root = files(package)
    tools: list[Any] = []

    skills_path: Path | None = None
    facts_path: Path | None = None

    # Create skills tools if requested
    if include_skills:
        skills_path = Path(str(package_root.joinpath(skills_subdir)))
        skills_tools = create_skills_tools(skills_path)
        tools.extend(skills_tools)  # Now just [read_skill]

    # Create facts tools if requested
    if include_facts:
        facts_path = Path(str(package_root.joinpath(facts_subdir)))
        facts_tools = create_facts_tools(facts_path)
        tools.extend(facts_tools)  # Now just [read_fact]

    # Create middleware configured for the included tools
    # Pass directory paths for inventory injection into system prompt
    middleware = (
        [
            ToolInstructionsMiddleware(
                tools=tools,
                skills_dir=skills_path,
                facts_dir=facts_path,
            )
        ]
        if tools
        else []
    )

    return tools, middleware
