"""User interfaces for MACSDK chatbots.

This module provides ready-to-use interfaces for interacting
with chatbots, including CLI and web interfaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .cli import run_cli_chatbot
    from .web import create_web_app, run_web_server

# Lazy imports to avoid loading heavy dependencies and config at import time
__all__ = ["create_web_app", "run_cli_chatbot", "run_web_server"]


def __getattr__(name: str) -> Any:
    """Lazy import of interface functions."""
    if name == "run_cli_chatbot":
        from .cli import run_cli_chatbot

        return run_cli_chatbot
    elif name == "create_web_app":
        from .web import create_web_app

        return create_web_app
    elif name == "run_web_server":
        from .web import run_web_server

        return run_web_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
