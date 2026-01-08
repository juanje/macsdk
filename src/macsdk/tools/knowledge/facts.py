"""Facts tools for MACSDK agents.

Facts provide contextual information and reference data about specific topics.
Agents should consult facts for accurate names, policies, and configurations.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from .helpers import _read_document


def create_facts_tools(facts_dir: Path) -> list:
    """Create facts tools configured for a specific directory.

    Args:
        facts_dir: Path to the facts directory.

    Returns:
        List of configured tool instances (only read_fact).
    """

    # Create closure that captures the facts_dir
    @tool
    def read_fact(path: str) -> str:
        """Get contextual information and reference data about a specific topic.

        The available facts are listed in your system instructions.
        Use the path from that list to read the fact content.

        The returned information provides background knowledge, domain-specific details,
        or reference data needed to work accurately on tasks.

        Args:
            path: The fact path from the available facts list
                  (e.g., 'api-endpoints.md' or 'services/database-info.md').

        Returns:
            Detailed information and context about the topic.
        """
        return _read_document(facts_dir, path, "fact")

    return [read_fact]
