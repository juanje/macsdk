"""Skills tools for MACSDK agents.

Skills provide step-by-step instructions for performing specific tasks.
Agents should consult skills before attempting complex operations.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from .helpers import _list_documents, _read_document


def create_skills_tools(skills_dir: Path) -> list:
    """Create skills tools configured for a specific directory.

    Args:
        skills_dir: Path to the skills directory.

    Returns:
        List of configured tool instances.
    """

    # Create closures that capture the skills_dir
    @tool
    def list_skills() -> list[dict[str, str]]:
        """List available skills that describe how to perform specific tasks.

        Use this when you need to discover what specialized capabilities or task
        instructions are available. Each skill contains step-by-step guidance for
        accomplishing a particular type of work.

        Skills may be organized hierarchically (general → specific). Use general
        skills first for overview, then specific skills for deep investigation.

        Returns:
            List of available skills with name, description, and path
            (relative to skills directory).
        """
        return _list_documents(skills_dir)

    @tool
    def read_skill(path: str) -> str:
        """Get detailed instructions on how to perform a specific task or capability.

        Use this after finding a relevant skill with list_skills(). The returned
        instructions will guide you through completing that type of task, including
        guidelines, examples, and best practices.

        Skills may reference other more specific skills for progressive disclosure.

        Args:
            path: The path from list_skills() (e.g., 'deploy-service.md' or
                  'check-service-health/api-gateway.md').

        Returns:
            Complete instructions and guidelines for performing the task.
        """
        return _read_document(skills_dir, path, "skill")

    return [list_skills, read_skill]
