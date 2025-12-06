"""Remote file tools for MACSDK agents.

Tools for fetching and working with files from remote servers,
useful for log analysis, configuration review, and data retrieval.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Annotated

import aiohttp
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

logger = logging.getLogger(__name__)


@tool
async def fetch_file(
    url: str,
    grep_pattern: str | None = None,
    tail_lines: int | None = None,
    head_lines: int | None = None,
    timeout: int = 30,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Fetch a file from a URL with optional filtering.

    Args:
        url: URL to fetch the file from.
        grep_pattern: Optional regex pattern to filter lines.
        tail_lines: Return only the last N lines.
        head_lines: Return only the first N lines.
        timeout: Request timeout in seconds.

    Returns:
        File content (filtered if specified) or error message.

    Example:
        >>> fetch_file("https://example.com/app.log", tail_lines=100)
        >>> fetch_file("https://example.com/config.yml", grep_pattern="database")
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status != 200:
                    return f"Error: HTTP {response.status}"

                content = await response.text()

        # Apply filters
        lines = content.splitlines()

        if grep_pattern:
            try:
                pattern = re.compile(grep_pattern)
                lines = [line for line in lines if pattern.search(line)]
            except re.error as e:
                return f"Invalid grep pattern: {e}"

        if tail_lines:
            lines = lines[-tail_lines:]
        elif head_lines:
            lines = lines[:head_lines]

        return "\n".join(lines)

    except aiohttp.ClientError as e:
        return f"Network error: {e}"
    except Exception as e:
        return f"Error fetching file: {e}"


@tool
async def fetch_and_save(
    url: str,
    save_path: str,
    timeout: int = 60,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Fetch a file from URL and save it locally.

    Args:
        url: URL to fetch the file from.
        save_path: Local path to save the file.
        timeout: Request timeout in seconds.

    Returns:
        Success message with file path or error message.

    Example:
        >>> fetch_and_save(
        ...     "https://example.com/report.pdf",
        ...     "/tmp/report.pdf"
        ... )
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status != 200:
                    return f"Error: HTTP {response.status}"

                content = await response.read()

        # Ensure directory exists
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_bytes(content)
        logger.info(f"Saved file to {save_path} ({len(content)} bytes)")

        return f"Successfully saved to {save_path} ({len(content)} bytes)"

    except aiohttp.ClientError as e:
        return f"Network error: {e}"
    except Exception as e:
        return f"Error saving file: {e}"


@tool
async def fetch_json(
    url: str,
    extract: str | None = None,
    timeout: int = 30,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Fetch JSON from a URL with optional JSONPath extraction.

    Args:
        url: URL to fetch JSON from.
        extract: Optional JSONPath expression (e.g., "$.data.items[*].name").
        timeout: Request timeout in seconds.

    Returns:
        JSON content (extracted if specified) or error message.

    Example:
        >>> fetch_json("https://api.example.com/data")
        >>> fetch_json("https://api.example.com/users", extract="$[*].email")
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={"Accept": "application/json"},
            ) as response:
                if response.status != 200:
                    return f"Error: HTTP {response.status}"

                import json

                data = await response.json()

                # Apply JSONPath extraction if specified
                if extract:
                    from jsonpath_ng import parse

                    expr = parse(extract)
                    matches = [match.value for match in expr.find(data)]

                    if len(matches) == 0:
                        return "No matches found for JSONPath expression"
                    elif len(matches) == 1:
                        data = matches[0]
                    else:
                        data = matches

                return json.dumps(data, indent=2, default=str)

    except aiohttp.ClientError as e:
        return f"Network error: {e}"
    except Exception as e:
        return f"Error fetching JSON: {e}"
