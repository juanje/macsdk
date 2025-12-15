"""Shared utilities for CLI commands.

This module provides common utility functions used across different CLI commands.
"""

from __future__ import annotations

import re


def slugify(name: str) -> str:
    """Convert name to valid Python package name.

    Args:
        name: Project name (e.g., "my-chatbot", "infra-agent").

    Returns:
        Valid Python package name with underscores.

    Examples:
        >>> slugify("my-chatbot")
        'my_chatbot'
        >>> slugify("infra-agent")
        'infra_agent'
    """
    # Replace hyphens and spaces with underscores
    slug = re.sub(r"[-\s]+", "_", name.lower())
    # Remove invalid characters
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    # Ensure it starts with a letter
    if slug and not slug[0].isalpha():
        slug = "pkg_" + slug
    return slug


def derive_class_name(name: str) -> str:
    """Derive class name from project/agent name.

    Handles cases where the name already ends with 'agent':
    - gitlab-agent -> GitlabAgent (not GitlabAgentAgent)
    - tf-agent -> TfAgent (not TfAgentAgent)
    - weather -> WeatherAgent
    - infra-monitor -> InfraMonitorAgent

    Args:
        name: Project name with dashes or underscores (e.g., "gitlab-agent").

    Returns:
        PascalCase class name ending with "Agent".

    Examples:
        >>> derive_class_name("gitlab-agent")
        'GitlabAgent'
        >>> derive_class_name("weather")
        'WeatherAgent'
        >>> derive_class_name("infra-monitor")
        'InfraMonitorAgent'
    """
    # Normalize: replace dashes with underscores and split
    parts = re.sub(r"[-\s]+", "_", name.lower()).split("_")

    # Check if the last part is "agent" (case-insensitive)
    if parts[-1] == "agent":
        # Don't add another "Agent" suffix
        return "".join(word.title() for word in parts)
    else:
        # Add "Agent" suffix
        return "".join(word.title() for word in parts) + "Agent"
