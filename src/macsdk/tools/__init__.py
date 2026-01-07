"""Reusable tools library for MACSDK agents.

This module provides common tools that agents can use for
interacting with external systems, APIs, remote files, and calculations.

Tools available:
- API tools: api_get, api_post, api_put, api_delete, api_patch
- Remote tools: fetch_file, fetch_and_save, fetch_json
- Math tools: calculate
- Programmatic: make_api_request (with JSONPath support)

Example:
    >>> from macsdk.tools import api_get, fetch_file, calculate
    >>> from macsdk.core.api_registry import register_api_service
    >>>
    >>> # Register a service
    >>> register_api_service("myapi", "https://api.example.com")
    >>>
    >>> # Use API tools
    >>> result = await api_get("myapi", "/users")
    >>>
    >>> # Use calculate
    >>> result = calculate("sqrt(16) + 2**3")  # "12.0"
"""

from .api import api_delete, api_get, api_patch, api_post, api_put, make_api_request
from .calculate import calculate
from .remote import fetch_and_save, fetch_file, fetch_json

__all__ = [
    # API tools (for LLM use)
    "api_get",
    "api_post",
    "api_put",
    "api_delete",
    "api_patch",
    # API tools (for programmatic use with JSONPath)
    "make_api_request",
    # Remote file tools
    "fetch_file",
    "fetch_and_save",
    "fetch_json",
    # Math tools
    "calculate",
]
