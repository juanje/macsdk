"""User interfaces for MACSDK chatbots.

This module provides ready-to-use interfaces for interacting
with chatbots, including CLI and web interfaces.
"""

from .cli import run_cli_chatbot
from .web import create_web_app, run_web_server

__all__ = ["create_web_app", "run_cli_chatbot", "run_web_server"]
