"""Skills tools for MACSDK agents.

Skills provide step-by-step instructions for performing specific tasks.
Agents should consult skills before attempting complex operations.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from .helpers import _read_document


def create_skills_tools(skills_dir: Path) -> list:
    """Create skills tools configured for a specific directory.

    Args:
        skills_dir: Path to the skills directory.

    Returns:
        List of configured tool instances (only read_skill).
    """

    # Create closure that captures the skills_dir
    @tool
    def read_skill(path: str) -> str:
        """Get detailed instructions on how to perform a specific task or capability.

        The available skills are listed in your system instructions.
        Use the path from that list to read the skill content.

        The returned instructions will guide you through completing that type of task,
        including guidelines, examples, and best practices.

        Skills may reference other more specific skills for progressive disclosure.

        Args:
            path: The skill path from the available skills list
                  (e.g., 'deploy-service.md' or 'check-service-health/api-gateway.md').

        Returns:
            Complete instructions and guidelines for performing the task.
        """
        return _read_document(skills_dir, path, "skill")

    return [read_skill]
