"""Facts tools for MACSDK agents.

Facts provide contextual information and reference data about specific topics.
Agents should consult facts for accurate names, policies, and configurations.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from .helpers import _list_documents, _read_document


def create_facts_tools(facts_dir: Path) -> list:
    """Create facts tools configured for a specific directory.

    Args:
        facts_dir: Path to the facts directory.

    Returns:
        List of configured tool instances.
    """

    # Create closures that capture the facts_dir
    @tool
    def list_facts() -> list[dict[str, str]]:
        """List available facts that provide contextual information on specific topics.

        Use this to discover what background knowledge, reference information, or
        domain-specific data is available. Facts help provide accurate context when
        working on tasks.

        Returns:
            List of available facts with name, description, and path
            (relative to facts directory).
        """
        return _list_documents(facts_dir)

    @tool
    def read_fact(path: str) -> str:
        """Get contextual information and reference data about a specific topic.

        Use this after finding a relevant fact with list_facts(). The returned
        information provides background knowledge, domain-specific details, or
        reference data needed to work accurately on tasks.

        Args:
            path: The path from list_facts() (e.g., 'api-endpoints.md' or
                  'services/database-info.md').

        Returns:
            Detailed information and context about the topic.
        """
        return _read_document(facts_dir, path, "fact")

    return [list_facts, read_fact]
