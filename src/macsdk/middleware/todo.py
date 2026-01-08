"""Deprecated TodoListMiddleware.

This middleware is deprecated and does nothing. Planning is now handled
via CoT prompts in the system message for better LLM compatibility.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import ModelRequest
    from langchain.agents.middleware.types import ModelResponse


class TodoListMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Deprecated: Planning is now handled via CoT prompts.

    This middleware is kept for backward compatibility but does nothing.
    Remove from your middleware list for cleaner code.

    The previous tag-based planning approach (<plan>, <task_complete>)
    was not followed by LLMs (especially Gemini models). The new approach
    uses Chain-of-Thought planning prompts that encourage visible planning
    in the message history without requiring special parsing.

    See SUPERVISOR_PLANNING_PROMPT and SPECIALIST_PLANNING_PROMPT for
    the new planning guidance.
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the middleware with a deprecation warning.

        Args:
            enabled: Ignored, kept for backward compatibility.
        """
        super().__init__()
        warnings.warn(
            "TodoListMiddleware is deprecated and does nothing. "
            "Planning is now handled via CoT prompts in the system message. "
            "Remove this middleware from your configuration.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.enabled = enabled

    def wrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], "ModelResponse"],
    ) -> "ModelResponse":
        """Pass through to next handler (no-op).

        Args:
            request: The model request.
            handler: The next handler in the middleware chain.

        Returns:
            The model response from the handler.
        """
        return handler(request)

    async def awrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], Awaitable["ModelResponse"]],
    ) -> "ModelResponse":
        """Pass through to next handler (no-op, async version).

        Args:
            request: The model request.
            handler: The next async handler in the middleware chain.

        Returns:
            The model response from the handler.
        """
        return await handler(request)
