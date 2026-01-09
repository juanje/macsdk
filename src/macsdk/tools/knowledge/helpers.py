"""Helper functions for knowledge tools (skills/facts).

This module provides utilities for safely reading markdown files with
YAML frontmatter from package directories.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _safe_path(base_dir: Path, relative_path: str) -> Path:
    """Resolve a path safely, preventing directory traversal attacks.

    Args:
        base_dir: The base directory that paths must stay within.
        relative_path: The user-provided relative path.

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If the path attempts to escape the base directory.
    """
    # Resolve both paths to absolute
    base_resolved = base_dir.resolve()
    target_resolved = (base_dir / relative_path).resolve()

    # Ensure the target is within the base directory using is_relative_to (Python 3.9+)
    if not target_resolved.is_relative_to(base_resolved):
        raise ValueError(f"Path traversal detected: '{relative_path}'")

    return target_resolved


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Uses yaml.safe_load for robust parsing, supporting:
    - Values with colons
    - Quoted strings
    - Multi-line values
    - Nested YAML structures

    Expected format:
    ---
    name: my-name
    description: My description
    ---
    <content>

    Args:
        content: The full file content.

    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter).
    """
    # Check if file starts with frontmatter delimiter
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        return {}, content

    # Find the closing delimiter (skip first line)
    # Use splitlines() for robust cross-platform newline handling
    lines = content.splitlines()
    end_index = -1

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index == -1:
        return {}, content

    # Extract and parse frontmatter
    frontmatter_text = "\n".join(lines[1:end_index])
    content_without = "\n".join(lines[end_index + 1 :]).strip()

    try:
        parsed = yaml.safe_load(frontmatter_text)
        # Ensure result is a dict (could be string, list, None, etc.)
        frontmatter = parsed if isinstance(parsed, dict) else {}
    except yaml.YAMLError:
        # Fall back to empty frontmatter on parse error
        frontmatter = {}

    return frontmatter, content_without


def _read_file_content(file_path: Path) -> tuple[dict[str, Any], str]:
    """Read a file and return its frontmatter and content.

    Args:
        file_path: Path to the file to read.

    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter).

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Python's universal newline mode (default) handles \r\n, \r, and \n correctly
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    return _parse_frontmatter(content)


def _list_documents(directory: Path) -> list[dict[str, str]]:
    """List top-level markdown documents with frontmatter in a directory.

    Only lists files at the first level (not in subdirectories) to support
    progressive disclosure: top-level skills/facts provide overviews and
    link to more specific documents in subdirectories.

    This pattern reduces prompt size and helps agents navigate knowledge
    hierarchically - reading general guidance first, then diving into
    specifics when needed.

    Args:
        directory: The directory to search.

    Returns:
        List of documents with name, description, and path.

    Example:
        Given this structure:
            skills/
            ├── deploy.md              # Listed (top-level)
            └── deploy/
                └── deploy-frontend.md # NOT listed, but accessible via read_skill()

        The agent sees only "deploy.md" in the inventory, which should
        explain and link to the specific sub-skills in deploy/.
    """
    documents: list[dict[str, str]] = []

    # Check if directory exists
    if not directory.exists():
        return documents

    # Use glob (not rglob) to list only top-level files
    # Sub-documents are accessible via read_skill/read_fact but not listed
    for file in directory.glob("*.md"):
        try:
            frontmatter, _ = _read_file_content(file)
            if "name" in frontmatter:
                relative_path = file.relative_to(directory)
                documents.append(
                    {
                        "name": str(frontmatter.get("name", "")),
                        "description": str(frontmatter.get("description", "")),
                        "path": str(relative_path),
                    }
                )
        except (OSError, yaml.YAMLError, UnicodeDecodeError) as e:
            # Skip files that can't be read or parsed (corrupted, permissions, etc.)
            logger.debug(f"Skipping file {file}: {e}")
            continue
    return documents


def _read_document(base_dir: Path, path: str, doc_type: str) -> str:
    """Read a document safely, with LLM-friendly error messages.

    Args:
        base_dir: The base directory for the document type.
        path: The relative path to the document.
        doc_type: The type of document (for error messages).

    Returns:
        The document content, or an error message if not found.
    """
    try:
        file_path = _safe_path(base_dir, path)
        _, content = _read_file_content(file_path)
        return content
    except FileNotFoundError:
        return (
            f"Error: {doc_type.capitalize()} '{path}' not found. "
            f"Use list_{doc_type}s() to see available {doc_type}s."
        )
    except ValueError as e:
        return f"Error: Invalid path - {e}"
