"""LLM caching utilities for the RAG agent.

This module provides caching functionality to avoid redundant API calls
and improve response times for repeated queries.
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

logger = logging.getLogger(__name__)

# Default cache path
DEFAULT_CACHE_PATH = Path("./.macsdk_llm_cache.db")


def setup_llm_cache(enable: bool = True, cache_path: Path | None = None) -> None:
    """Setup LLM caching to avoid redundant API calls.

    This caches LLM responses in a SQLite database. If the same prompt
    is sent again, the cached response is returned instantly without
    making an API call.

    Benefits:
    - Instant responses for repeated queries
    - Zero cost for cached responses
    - Persistent across sessions

    Args:
        enable: If True, enable LLM caching.
        cache_path: Path to the SQLite cache file.

    Example:
        >>> setup_llm_cache(enable=True)
        >>> # First call: makes API request
        >>> response1 = llm.invoke("What is Python?")
        >>> # Second call: uses cache (instant, free)
        >>> response2 = llm.invoke("What is Python?")
    """
    if enable:
        path = cache_path or DEFAULT_CACHE_PATH
        logger.info(f"Enabling LLM cache at {path}")
        set_llm_cache(SQLiteCache(database_path=str(path)))
    else:
        logger.info("LLM cache disabled")
        set_llm_cache(None)


def clear_llm_cache(cache_path: Path | None = None) -> None:
    """Clear the LLM cache database.

    Useful for testing or when you want to force fresh API calls.

    Args:
        cache_path: Path to the SQLite cache file.
    """
    path = cache_path or DEFAULT_CACHE_PATH
    if path.exists():
        logger.info(f"Clearing LLM cache at {path}")
        path.unlink()
        logger.info("LLM cache cleared")
    else:
        logger.info("No cache to clear")


def get_cache_stats(cache_path: Path | None = None) -> dict[str, int | str | bool]:
    """Get statistics about the LLM cache.

    Args:
        cache_path: Path to the SQLite cache file.

    Returns:
        Dictionary with cache statistics.
    """
    path = cache_path or DEFAULT_CACHE_PATH
    if not path.exists():
        return {
            "exists": False,
            "size_bytes": 0,
            "size_mb": "0.0",
        }

    size_bytes = path.stat().st_size
    size_mb = round(size_bytes / (1024 * 1024), 2)
    return {
        "exists": True,
        "path": str(path),
        "size_bytes": size_bytes,
        "size_mb": str(size_mb),
    }
