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

    Tools are only created if directories exist AND contain .md files.
    This enables auto-detection: create the directory and add files
    to enable the feature automatically.

    Args:
        package: Package name. Use __package__ for current package.
        skills_subdir: Subdirectory for skills (default: "skills").
        facts_subdir: Subdirectory for facts (default: "facts").
        include_skills: Include skills tools (read_skill).
        include_facts: Include facts tools (read_fact).

    Returns:
        Tuple of (tools, middleware). Empty lists if no knowledge exists.

    Example:
        >>> from macsdk.tools.knowledge import get_knowledge_bundle
        >>>
        >>> # Auto-detection: only creates tools if dirs have content
        >>> knowledge_tools, knowledge_mw = get_knowledge_bundle(__package__)
        >>> len(knowledge_tools)  # 0 if no skills/ or facts/ with .md files
        0

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

    # Create skills tools ONLY if directory exists with .md content
    if include_skills:
        candidate_path = Path(str(package_root.joinpath(skills_subdir)))
        if (
            candidate_path.exists()
            and candidate_path.is_dir()
            and any(candidate_path.glob("*.md"))
        ):
            skills_path = candidate_path
            skills_tools = create_skills_tools(skills_path)
            tools.extend(skills_tools)

    # Create facts tools ONLY if directory exists with .md content
    if include_facts:
        candidate_path = Path(str(package_root.joinpath(facts_subdir)))
        if (
            candidate_path.exists()
            and candidate_path.is_dir()
            and any(candidate_path.glob("*.md"))
        ):
            facts_path = candidate_path
            facts_tools = create_facts_tools(facts_path)
            tools.extend(facts_tools)

    # Middleware ONLY if we have tools
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
