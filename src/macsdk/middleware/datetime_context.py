"""DateTime context middleware for MACSDK agents.

This middleware injects the current date and time into agent prompts,
helping agents understand temporal context when interpreting logs,
timestamps, and relative dates in user queries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentState
    from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


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
        "last_24h": last_24h.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
        - **Current UTC time**: 2024-01-15 14:30:00 UTC
        - **Current date**: Monday, January 15, 2024
        - **ISO format**: 2024-01-15T14:30:00+00:00
        ...
    """
    if now is None:
        now = datetime.now(timezone.utc)

    refs = _calculate_date_references(now)

    return f"""
## Current DateTime Context

**Now:**
- Current UTC time: {now.strftime("%Y-%m-%d %H:%M:%S UTC")}
- Current date: {now.strftime("%A, %B %d, %Y")}
- ISO format: {now.isoformat()}

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
