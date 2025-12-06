"""Web interface for MACSDK chatbots.

This module provides a ready-to-use FastAPI web interface
for chatbot interactions via WebSocket.
"""

from .server import create_web_app, run_web_server

__all__ = ["create_web_app", "run_web_server"]
