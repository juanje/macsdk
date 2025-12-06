"""DateTime context middleware for MACSDK agents.

This middleware injects the current date and time into agent prompts,
helping agents understand temporal context when interpreting logs,
timestamps, and relative dates in user queries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentState
    from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


def format_datetime_context(now: datetime | None = None) -> str:
    """Format current datetime as context string for prompts.

    Args:
        now: Optional datetime to format. Defaults to current UTC time.

    Returns:
        Formatted datetime context string.

    Example:
        >>> context = format_datetime_context()
        >>> print(context)
        ## Current DateTime Context
        - **Current UTC time**: 2024-01-15 14:30:00 UTC
        - **Current date**: Monday, January 15, 2024
        - **ISO format**: 2024-01-15T14:30:00+00:00
    """
    if now is None:
        now = datetime.now(timezone.utc)

    return f"""
## Current DateTime Context
- **Current UTC time**: {now.strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Current date**: {now.strftime("%A, %B %d, %Y")}
- **ISO format**: {now.isoformat()}

Use this when interpreting timestamps, logs, or relative dates in queries.
"""


class DatetimeContextMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Middleware that injects current datetime into system prompts.

    This middleware helps agents:
    - Interpret timestamps in logs and API responses
    - Understand "today", "yesterday", "last week" in user queries
    - Avoid confusion from training data cutoff dates

    The datetime context is prepended to the system prompt before
    each model invocation using the `before_model` hook.

    Example:
        >>> from macsdk.middleware import DatetimeContextMiddleware
        >>> from langchain.agents import create_agent
        >>>
        >>> middleware = [DatetimeContextMiddleware()]
        >>> agent = create_agent(
        ...     model=get_answer_model(),
        ...     tools=tools,
        ...     middleware=middleware,
        ...     system_prompt="You are a helpful assistant.",
        ... )
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active. If False,
                     the middleware passes through without modification.
        """
        self.enabled = enabled
        logger.debug(f"DatetimeContextMiddleware initialized (enabled={enabled})")

    def before_model(
        self,
        state: "AgentState",
        runtime: "Runtime",
    ) -> dict[str, Any] | None:
        """Inject datetime context before each model call.

        This hook is called before each LLM invocation. It modifies
        the messages to include current datetime context.

        Args:
            state: Current agent state with messages.
            runtime: LangGraph runtime context.

        Returns:
            Updated state with datetime context injected, or None if no changes.
        """
        if not self.enabled:
            return None

        messages = state.get("messages", [])
        if not messages:
            return None

        # Import here to avoid circular imports
        from langchain_core.messages import SystemMessage

        modified_messages = list(messages)

        # Check if first message is a system message
        if modified_messages and isinstance(modified_messages[0], SystemMessage):
            # Only inject if not already present
            if "## Current DateTime Context" in str(modified_messages[0].content):
                logger.debug("Datetime context already present, skipping")
                return None

            datetime_context = format_datetime_context()
            original_content = modified_messages[0].content
            modified_messages[0] = SystemMessage(
                content=f"{datetime_context}\n{original_content}"
            )
            logger.debug("Injected datetime context into system message")
        else:
            # Insert new system message with datetime context
            datetime_context = format_datetime_context()
            modified_messages.insert(0, SystemMessage(content=datetime_context))
            logger.debug("Added new system message with datetime context")

        return {"messages": modified_messages}
