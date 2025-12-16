"""Local agents for devops-chatbot (mono-repo approach).

This package contains agents that live inside the chatbot project,
as opposed to remote agents installed from external packages.
"""

from .api import ApiAgent

__all__ = ["ApiAgent"]
