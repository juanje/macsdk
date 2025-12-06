"""Context summarization middleware for MACSDK agents.

This middleware automatically summarizes long conversations to prevent
context window overflow while preserving important information.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentState
    from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)

# Default summarization settings
DEFAULT_TRIGGER_TOKENS = 100000
DEFAULT_KEEP_MESSAGES = 6


class SummarizationMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Middleware that summarizes long conversations.

    When the conversation exceeds a token threshold, older messages
    are summarized to reduce context size while preserving key information.

    This middleware uses the `after_model` hook to check conversation
    length and trigger summarization when needed.

    Example:
        >>> from macsdk.middleware import SummarizationMiddleware
        >>> from langchain.agents import create_agent
        >>>
        >>> middleware = [SummarizationMiddleware(trigger_tokens=50000)]
        >>> agent = create_agent(
        ...     model=get_answer_model(),
        ...     tools=tools,
        ...     middleware=middleware,
        ... )

    Note:
        This is a placeholder implementation. Full summarization requires
        integration with LangChain's SummarizationMiddleware which needs
        additional configuration for the summarization model.
    """

    def __init__(
        self,
        enabled: bool = True,
        trigger_tokens: int = DEFAULT_TRIGGER_TOKENS,
        keep_messages: int = DEFAULT_KEEP_MESSAGES,
    ) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active.
            trigger_tokens: Token count threshold to trigger summarization.
            keep_messages: Number of recent messages to keep unsummarized.
        """
        self.enabled = enabled
        self.trigger_tokens = trigger_tokens
        self.keep_messages = keep_messages
        logger.debug(
            f"SummarizationMiddleware initialized "
            f"(enabled={enabled}, trigger={trigger_tokens}, keep={keep_messages})"
        )

    def _estimate_tokens(self, messages: list) -> int:
        """Estimate token count for messages.

        This is a rough estimate using character count / 4.
        For production, use tiktoken for accurate counts.

        Args:
            messages: List of messages to estimate.

        Returns:
            Estimated token count.
        """
        total_chars = sum(
            len(str(m.content)) if hasattr(m, "content") else len(str(m))
            for m in messages
        )
        return total_chars // 4  # Rough estimate

    def after_model(
        self,
        state: "AgentState",
        runtime: "Runtime",
    ) -> dict[str, Any] | None:
        """Check and summarize after each model call.

        This hook is called after each LLM response. It checks if
        the conversation has exceeded the token threshold and
        triggers summarization if needed.

        Args:
            state: Current agent state with messages.
            runtime: LangGraph runtime context.

        Returns:
            Updated state with summarized messages, or None if no change.
        """
        if not self.enabled:
            return None

        messages = state.get("messages", [])
        if not messages:
            return None

        # Estimate current token count
        token_count = self._estimate_tokens(messages)

        if token_count < self.trigger_tokens:
            return None

        logger.info(
            f"Token count ({token_count}) exceeds threshold ({self.trigger_tokens}), "
            "summarization would be triggered"
        )

        # For now, just keep the last N messages as a simple approach
        # Full summarization would require calling an LLM to summarize
        if len(messages) <= self.keep_messages:
            return None

        # Keep system message (if any) + last N messages
        from langchain_core.messages import BaseMessage, SystemMessage

        kept_messages: list[BaseMessage] = []
        other_messages: list[BaseMessage] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                kept_messages.append(msg)
            else:
                other_messages.append(msg)

        # Keep the most recent messages
        recent_messages = other_messages[-self.keep_messages :]
        kept_messages.extend(recent_messages)

        trimmed_count = len(messages) - len(kept_messages)
        if trimmed_count > 0:
            logger.info(f"Trimmed {trimmed_count} older messages to reduce context")
            return {"messages": kept_messages}

        return None
