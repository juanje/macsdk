"""DateTime context middleware for MACSDK agents.

This middleware injects the current date and time into agent prompts,
helping agents understand temporal context when interpreting logs,
timestamps, and relative dates in user queries.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentState, ModelRequest
    from langchain.agents.middleware.types import ModelResponse
    from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)

# Delimiters for datetime context block (robust parsing)
# Note: XML tags like <datetime> cause Gemini to be more "planful" - adding
# extra write_todos calls and consulting more skills/facts before acting.
# HTML comments are ignored by LLMs, providing robust delimiters without
# affecting agent behavior.
DATETIME_CONTEXT_START = "<!-- macsdk:datetime:start -->"
DATETIME_CONTEXT_END = "<!-- macsdk:datetime:end -->"
# Header for human readability inside the block
DATETIME_CONTEXT_HEADER = "## Current DateTime Context"


def _calculate_date_references(now: datetime) -> dict[str, str]:
    """Calculate common date references for time-range queries.

    Args:
        now: Current datetime in UTC.

    Returns:
        Dictionary with pre-calculated dates in ISO 8601 format.
    """
    # Common relative dates
    yesterday = now - timedelta(days=1)
    last_24h = now - timedelta(hours=24)
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    # Start of current week (Monday at 00:00:00 UTC)
    days_since_monday = now.weekday()  # Monday = 0
    start_of_week = (now - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Start of current month (1st day at 00:00:00 UTC)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Start of previous month
    if now.month == 1:
        start_of_prev_month = now.replace(
            year=now.year - 1,
            month=12,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    else:
        start_of_prev_month = now.replace(
            month=now.month - 1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    return {
        "yesterday": yesterday.strftime("%Y-%m-%dT00:00:00Z"),
        "last_24h": last_24h.strftime("%Y-%m-%dT%H:%M:00Z"),
        "last_7_days": last_7_days.strftime("%Y-%m-%dT00:00:00Z"),
        "last_30_days": last_30_days.strftime("%Y-%m-%dT00:00:00Z"),
        "start_of_week": start_of_week.strftime("%Y-%m-%dT00:00:00Z"),
        "start_of_month": start_of_month.strftime("%Y-%m-%dT00:00:00Z"),
        "start_of_prev_month": start_of_prev_month.strftime("%Y-%m-%dT00:00:00Z"),
    }


def format_datetime_context(now: datetime | None = None) -> str:
    """Format current datetime as context string for prompts.

    Includes pre-calculated dates for common time-range queries,
    making it easy for agents to use relative dates in API calls.

    Args:
        now: Optional datetime to format. Defaults to current UTC time.

    Returns:
        Formatted datetime context string with current time and
        pre-calculated reference dates in ISO 8601 format.

    Example:
        >>> context = format_datetime_context()
        >>> print(context)
        ## Current DateTime Context
        - **Current UTC time**: 2024-01-15 14:30 UTC
        - **Current date**: Monday, January 15, 2024
        - **ISO format**: 2024-01-15T14:30:00+00:00
        ...
    """
    if now is None:
        now = datetime.now(timezone.utc)

    refs = _calculate_date_references(now)

    return f"""
{DATETIME_CONTEXT_START}
{DATETIME_CONTEXT_HEADER}

**Now:**
- Current UTC time: {now.strftime("%Y-%m-%d %H:%M UTC")}
- Current date: {now.strftime("%A, %B %d, %Y")}
- ISO format: {now.strftime("%Y-%m-%dT%H:%M:00+00:00")}

**Pre-calculated dates for API queries (ISO 8601 format):**
| Reference | Date | Use for |
|-----------|------|---------|
| Yesterday | {refs["yesterday"]} | "yesterday" queries |
| Last 24 hours | {refs["last_24h"]} | "last 24 hours", "today" |
| Last 7 days | {refs["last_7_days"]} | "last week", "past 7 days" |
| Last 30 days | {refs["last_30_days"]} | "last month", "past 30 days" |
| Start of this week | {refs["start_of_week"]} | "this week" (Monday) |
| Start of this month | {refs["start_of_month"]} | "this month" |
| Start of last month | {refs["start_of_prev_month"]} | "last month" (calendar) |

**Usage:** For time-range API queries, use these dates directly with parameters
like `updated_after`, `created_after`, `since`, etc.

**Phrase interpretation:**
- "last 7 days" / "past week" → use {refs["last_7_days"]}
- "this week" → use {refs["start_of_week"]}
- "last month" (relative) → use {refs["last_30_days"]}
- "last month" (calendar) → use {refs["start_of_prev_month"]}
{DATETIME_CONTEXT_END}
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

    def __init__(self, enabled: bool = True, cache_ttl_seconds: int = 60) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active. If False,
                     the middleware passes through without modification.
            cache_ttl_seconds: Time-to-live for cached datetime context in
                              seconds. Default is 60 seconds to balance
                              freshness with performance.
        """
        import re

        self.enabled = enabled
        self._cache_ttl = cache_ttl_seconds
        self._cached_context: str | None = None
        self._cache_time: datetime | None = None

        # Pre-compile regex for datetime context removal (performance optimization)
        pattern_str = (
            re.escape(DATETIME_CONTEXT_START) + r".*?" + re.escape(DATETIME_CONTEXT_END)
        )
        self._cleanup_pattern: re.Pattern[str] = re.compile(
            pattern_str, flags=re.DOTALL
        )

        logger.debug(
            f"DatetimeContextMiddleware initialized "
            f"(enabled={enabled}, cache_ttl={cache_ttl_seconds}s)"
        )

    def _get_cached_context(self) -> str:
        """Get datetime context from cache or generate new one if expired.

        Note: This method has a minor race condition in multi-threaded
        environments where multiple threads might regenerate the context
        simultaneously. This is acceptable because:
        1. The operation is idempotent (same input = same output)
        2. format_datetime_context() is cheap (simple string formatting)
        3. The worst case is redundant string generation, not corruption

        If format_datetime_context() becomes expensive in the future,
        consider adding a threading.Lock.

        Returns:
            Formatted datetime context string.
        """
        now = datetime.now(timezone.utc)
        if (
            self._cached_context is None
            or self._cache_time is None
            or (now - self._cache_time).total_seconds() > self._cache_ttl
        ):
            self._cached_context = format_datetime_context(now)
            self._cache_time = now
            logger.debug("Generated new datetime context (cache miss or expired)")
        else:
            logger.debug("Using cached datetime context")
        return self._cached_context

    def _remove_stale_context(self, content: str) -> str:
        """Remove old datetime context from content if present.

        Uses pre-compiled regex with delimiters for robust parsing,
        with fallback for legacy format.

        Args:
            content: The content string to clean.

        Returns:
            Content with datetime context removed (if it was present).
        """
        # Try delimiters first (new format - robust, uses pre-compiled regex)
        if DATETIME_CONTEXT_START in content and DATETIME_CONTEXT_END in content:
            content = self._cleanup_pattern.sub("", content).strip()
            logger.debug("Removed stale datetime context (delimited format)")
            return content

        # Fallback for legacy format without delimiters (backward compatibility)
        if DATETIME_CONTEXT_HEADER in content:
            content = content.split(DATETIME_CONTEXT_HEADER)[0].strip()
            logger.debug("Removed stale datetime context (legacy format)")

        return content

    def _inject_datetime_context(self, request: "ModelRequest") -> None:
        """Inject datetime context into request.system_message.

        This method modifies the system_message in the request to append
        datetime context at the end, which is optimal for LLM caching.

        Args:
            request: The model request containing the system_message to modify.
        """
        from langchain_core.messages import SystemMessage

        # Check if there's a system_message to modify
        if not (hasattr(request, "system_message") and request.system_message):
            logger.debug("No system_message in request, skipping injection")
            return

        content = str(request.system_message.content)

        # Remove old datetime context if present (for multi-turn conversations)
        content = self._remove_stale_context(content)

        datetime_context = self._get_cached_context()

        # Inject at the END of the system prompt for better caching
        new_content = f"{content}\n\n{datetime_context}"
        request.system_message = SystemMessage(content=new_content)
        logger.debug("Injected datetime context into system_message (at end)")

    def wrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], "ModelResponse"],
    ) -> "ModelResponse":
        """Inject datetime context into the system message (sync).

        This hook is called before each model invocation and has access
        to the full request including the system_message configured when
        creating the agent.

        Args:
            request: The model request containing system_message and messages.
            handler: The next handler in the middleware chain.

        Returns:
            The model response from the handler.
        """
        if not self.enabled:
            return handler(request)

        self._inject_datetime_context(request)
        return handler(request)

    async def awrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], Awaitable["ModelResponse"]],
    ) -> "ModelResponse":
        """Inject datetime context into the system message (async).

        This hook is called before each model invocation and has access
        to the full request including the system_message configured when
        creating the agent.

        Args:
            request: The model request containing system_message and messages.
            handler: The next async handler in the middleware chain.

        Returns:
            The model response from the handler.
        """
        if not self.enabled:
            return await handler(request)

        self._inject_datetime_context(request)
        return await handler(request)

    def before_model(
        self,
        state: "AgentState",
        runtime: "Runtime",
    ) -> dict[str, Any] | None:
        """Fallback hook for injecting datetime context.

        This hook is kept for backwards compatibility with agents that don't
        use wrap_model_call. It modifies the messages list to include datetime
        context, but cannot access the system_message configured in create_agent.

        Prefer using wrap_model_call/awrap_model_call which has access to the
        full request including system_message.

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
            original_content = str(modified_messages[0].content)

            # Remove old datetime context if present (for multi-turn conversations)
            original_content = self._remove_stale_context(original_content)

            # Inject fresh datetime context
            datetime_context = self._get_cached_context()
            # Place datetime context at END for better LLM caching
            modified_messages[0] = SystemMessage(
                content=f"{original_content}\n\n{datetime_context}"
            )
            logger.debug("Injected datetime context into system message (at end)")
        else:
            # Insert new system message with datetime context
            datetime_context = self._get_cached_context()
            modified_messages.insert(0, SystemMessage(content=datetime_context))
            logger.debug("Added new system message with datetime context")

        return {"messages": modified_messages}
