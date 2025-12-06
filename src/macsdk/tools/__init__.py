"""Reusable tools library for MACSDK agents.

This module provides common tools that agents can use for
interacting with external systems, APIs, and remote files.

Tools available:
- API tools: api_get, api_post, api_put, api_delete, api_patch
- Remote tools: fetch_file, fetch_and_save, fetch_json

Example:
    >>> from macsdk.tools import api_get, fetch_file
    >>> from macsdk.core.api_registry import register_api_service
    >>>
    >>> # Register a service
    >>> register_api_service("myapi", "https://api.example.com")
    >>>
    >>> # Use API tools
    >>> result = await api_get("myapi", "/users")
"""

from .api import api_delete, api_get, api_patch, api_post, api_put
from .remote import fetch_and_save, fetch_file, fetch_json

__all__ = [
    # API tools
    "api_get",
    "api_post",
    "api_put",
    "api_delete",
    "api_patch",
    # Remote file tools
    "fetch_file",
    "fetch_and_save",
    "fetch_json",
]
