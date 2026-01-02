"""Remote file tools for MACSDK agents.

Tools for fetching and working with files from remote servers,
useful for log analysis, configuration review, and data retrieval.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import httpx
from langchain_core.tools import ToolException, tool

from ..core.url_security import (
    URLSecurityError,
    create_redirect_validator,
    validate_url,
)

logger = logging.getLogger(__name__)


@tool
async def fetch_file(
    url: str,
    grep_pattern: str | None = None,
    tail_lines: int | None = None,
    head_lines: int | None = None,
    timeout: int = 30,
    ssl_verify: bool = True,
) -> str:
    """Fetch a file from a URL with optional filtering.

    Args:
        url: URL to fetch the file from.
        grep_pattern: Optional regex pattern to filter lines.
        tail_lines: Return only the last N lines.
        head_lines: Return only the first N lines.
        timeout: Request timeout in seconds.
        ssl_verify: Whether to verify SSL certificates (default True).
                   Set to False for internal servers with self-signed certs.

    Returns:
        File content (filtered if specified).

    Raises:
        ToolException: If the file cannot be fetched (network error, HTTP error, etc.)

    Example:
        >>> fetch_file("https://example.com/app.log", tail_lines=100)
        >>> fetch_file("https://example.com/config.yml", grep_pattern="database")
        >>> fetch_file("https://internal.server/log", ssl_verify=False)
    """
    # Validate URL against security policy (uses global config)
    from ..core.config import config

    if config.url_security.enabled:
        try:
            validate_url(url, config.url_security)
        except URLSecurityError as e:
            raise ToolException(str(e))

    try:
        # Configure event hooks to validate redirects
        validator = create_redirect_validator(config.url_security)
        event_hooks = {"request": [validator]} if validator else {}

        async with httpx.AsyncClient(
            verify=ssl_verify,
            timeout=timeout,
            follow_redirects=True,
            event_hooks=event_hooks,
        ) as client:
            response = await client.get(url)

            if response.status_code != 200:
                raise ToolException(
                    f"HTTP {response.status_code} fetching {url}. "
                    "This is a tool error, not content from the file."
                )

            content = response.text

        # Apply filters
        lines = content.splitlines()

        if grep_pattern:
            try:
                pattern = re.compile(grep_pattern)
                lines = [line for line in lines if pattern.search(line)]
            except re.error as e:
                raise ToolException(f"Invalid grep pattern '{grep_pattern}': {e}")

        if tail_lines:
            lines = lines[-tail_lines:]
        elif head_lines:
            lines = lines[:head_lines]

        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        raise ToolException(
            f"HTTP {e.response.status_code} fetching {url}. "
            "This is a tool error, not content from the file."
        )
    except httpx.RequestError as e:
        raise ToolException(
            f"Network error fetching {url}: {e}. "
            "This is a connection problem, not an error from the remote file."
        )
    except ToolException:
        raise  # Re-raise ToolExceptions as-is
    except Exception as e:
        raise ToolException(f"Unexpected error fetching {url}: {e}")


@tool
async def fetch_and_save(
    url: str,
    save_path: str,
    timeout: int = 60,
    ssl_verify: bool = True,
) -> str:
    """Fetch a file from URL and save it locally.

    Args:
        url: URL to fetch the file from.
        save_path: Local path to save the file.
        timeout: Request timeout in seconds.
        ssl_verify: Whether to verify SSL certificates (default True).

    Returns:
        Success message with file path and size.

    Raises:
        ToolException: If the file cannot be fetched or saved.

    Example:
        >>> fetch_and_save(
        ...     "https://example.com/report.pdf",
        ...     "/tmp/report.pdf"
        ... )
    """
    # Validate URL against security policy (uses global config)
    from ..core.config import config

    if config.url_security.enabled:
        try:
            validate_url(url, config.url_security)
        except URLSecurityError as e:
            raise ToolException(str(e))

    try:
        # Configure event hooks to validate redirects
        validator = create_redirect_validator(config.url_security)
        event_hooks = {"request": [validator]} if validator else {}

        async with httpx.AsyncClient(
            verify=ssl_verify,
            timeout=timeout,
            follow_redirects=True,
            event_hooks=event_hooks,
        ) as client:
            response = await client.get(url)

            if response.status_code != 200:
                raise ToolException(f"HTTP {response.status_code} fetching {url}")

            content = response.content

        # Ensure directory exists
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_bytes(content)
        logger.info(f"Saved file to {save_path} ({len(content)} bytes)")

        return f"Successfully saved to {save_path} ({len(content)} bytes)"

    except httpx.HTTPStatusError as e:
        raise ToolException(f"HTTP {e.response.status_code} fetching {url}. Error: {e}")
    except httpx.RequestError as e:
        raise ToolException(f"Network error fetching {url}: {e}")
    except ToolException:
        raise
    except Exception as e:
        raise ToolException(f"Error saving file: {e}")


@tool
async def fetch_json(
    url: str,
    extract: str | None = None,
    timeout: int = 30,
    ssl_verify: bool = True,
) -> str:
    """Fetch JSON from a URL with optional JSONPath extraction.

    Args:
        url: URL to fetch JSON from.
        extract: Optional JSONPath expression (e.g., "$.data.items[*].name").
        timeout: Request timeout in seconds.
        ssl_verify: Whether to verify SSL certificates (default True).

    Returns:
        JSON content (extracted if specified).

    Raises:
        ToolException: If the JSON cannot be fetched or parsed.

    Example:
        >>> fetch_json("https://api.example.com/data")
        >>> fetch_json("https://api.example.com/users", extract="$[*].email")
    """
    # Validate URL against security policy (uses global config)
    from ..core.config import config

    if config.url_security.enabled:
        try:
            validate_url(url, config.url_security)
        except URLSecurityError as e:
            raise ToolException(str(e))

    try:
        # Configure event hooks to validate redirects
        validator = create_redirect_validator(config.url_security)
        event_hooks = {"request": [validator]} if validator else {}

        async with httpx.AsyncClient(
            verify=ssl_verify,
            timeout=timeout,
            follow_redirects=True,
            event_hooks=event_hooks,
        ) as client:
            response = await client.get(url, headers={"Accept": "application/json"})

            if response.status_code != 200:
                raise ToolException(f"HTTP {response.status_code} fetching {url}")

            import json

            data = response.json()

            # Apply JSONPath extraction if specified
            if extract:
                from jsonpath_ng import parse

                expr = parse(extract)
                matches = [match.value for match in expr.find(data)]

                if len(matches) == 0:
                    raise ToolException(
                        f"No matches found for JSONPath expression '{extract}'"
                    )
                elif len(matches) == 1:
                    data = matches[0]
                else:
                    data = matches

            return json.dumps(data, indent=2, default=str)

    except httpx.HTTPStatusError as e:
        raise ToolException(f"HTTP {e.response.status_code} fetching {url}. Error: {e}")
    except httpx.RequestError as e:
        raise ToolException(f"Network error fetching {url}: {e}")
    except ToolException:
        raise
    except Exception as e:
        raise ToolException(f"Error fetching JSON from {url}: {e}")
