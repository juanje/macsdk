"""Debug middleware to log prompts sent to LLM.

This middleware displays the system and user prompts being sent
to the LLM, useful for debugging and understanding agent behavior.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentState, ModelRequest
    from langchain.agents.middleware.types import ModelResponse
    from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


class PromptDebugMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Middleware that logs prompts sent to the LLM.

    This middleware helps developers:
    - See the exact system prompt being used
    - View user messages as they are sent
    - Debug agent behavior and prompt engineering
    - Optionally log model responses

    Example:
        >>> from macsdk.middleware import PromptDebugMiddleware
        >>> from langchain.agents import create_agent
        >>>
        >>> middleware = [PromptDebugMiddleware()]
        >>> agent = create_agent(
        ...     model=get_answer_model(),
        ...     tools=tools,
        ...     middleware=middleware,
        ...     system_prompt="You are a helpful assistant.",
        ... )
    """

    def __init__(
        self,
        enabled: bool = True,
        show_system: bool = True,
        show_user: bool = True,
        show_response: bool = False,
        max_length: int = 2000,
        use_logger: bool = False,
    ) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active.
            show_system: Whether to show system prompts.
            show_user: Whether to show user messages.
            show_response: Whether to show model responses (after_model).
            max_length: Maximum characters to show per message.
            use_logger: If True, use logger instead of print.
        """
        self.enabled = enabled
        self.show_system = show_system
        self.show_user = show_user
        self.show_response = show_response
        self.max_length = max_length
        self.use_logger = use_logger
        logger.debug(f"PromptDebugMiddleware initialized (enabled={enabled})")

    def _output(self, text: str) -> None:
        """Output text to logger or print."""
        if self.use_logger:
            logger.info(text)
        else:
            print(text)

    def _truncate(self, text: str) -> str:
        """Truncate text if too long."""
        if len(text) > self.max_length:
            return text[: self.max_length] + f"\n... (truncated, {len(text)} chars)"
        return text

    def _format_message(self, msg: Any) -> str:
        """Format a message for display."""
        msg_type = type(msg).__name__
        content = getattr(msg, "content", str(msg))

        # Handle list content (structured content blocks)
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = "\n".join(text_parts) if text_parts else str(content)

        return f"[{msg_type}]\n{self._truncate(str(content))}"

    def _log_request(self, request: "ModelRequest") -> None:
        """Log the model request (system prompt and messages).

        Args:
            request: The model request to log.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        self._output("\n" + "=" * 80)
        self._output("🔍 [PROMPT DEBUG] Before Model Call")
        self._output("=" * 80)

        # Access system prompt via request.system_message
        if self.show_system and hasattr(request, "system_message"):
            system_msg = request.system_message
            if system_msg:
                self._output("\n📋 SYSTEM PROMPT:")
                self._output("-" * 40)

                # Handle both string and SystemMessage
                if hasattr(system_msg, "content"):
                    raw_content = system_msg.content
                    content_str: str = ""

                    # Handle content blocks
                    if hasattr(system_msg, "content_blocks"):
                        try:
                            blocks = list(system_msg.content_blocks)
                            text_parts: list[str] = []
                            for block in blocks:
                                if hasattr(block, "text"):
                                    text_parts.append(str(getattr(block, "text", "")))
                                elif isinstance(block, dict):
                                    text_parts.append(str(block.get("text", "")))
                            if text_parts:
                                content_str = "\n".join(text_parts)
                        except Exception:  # nosec B110
                            pass  # Content parsing failure, will try other methods

                    if not content_str:
                        if isinstance(raw_content, list):
                            list_parts: list[str] = []
                            for item in raw_content:  # type: ignore[union-attr]
                                if isinstance(item, dict):
                                    list_parts.append(str(item.get("text", str(item))))
                                else:
                                    list_parts.append(str(item))
                            content_str = "\n".join(list_parts)
                        else:
                            content_str = str(raw_content)

                    self._output(self._truncate(content_str))
                else:
                    self._output(self._truncate(str(system_msg)))
                self._output("-" * 40)

        # Access messages from request
        messages = getattr(request, "messages", [])
        if not messages and hasattr(request, "state"):
            messages = request.state.get("messages", [])

        for i, msg in enumerate(messages):
            is_system = isinstance(msg, SystemMessage)
            is_human = isinstance(msg, HumanMessage)

            if is_system and self.show_system:
                self._output(f"\n📋 SYSTEM MESSAGE (message {i + 1}):")
                self._output("-" * 40)
                self._output(self._format_message(msg))
                self._output("-" * 40)

            elif is_human and self.show_user:
                self._output(f"\n👤 USER MESSAGE (message {i + 1}):")
                self._output("-" * 40)
                self._output(self._format_message(msg))
                self._output("-" * 40)

            elif not is_system and not is_human:
                msg_type = type(msg).__name__
                content_preview = str(getattr(msg, "content", ""))[:100]
                self._output(f"\n📨 {msg_type} (message {i + 1}): {content_preview}...")

        self._output(f"\n📊 Total messages: {len(messages)}")
        self._output("=" * 80 + "\n")

    def _log_response(self, response: "ModelResponse") -> None:
        """Log the model response.

        Args:
            response: The model response to log.
        """
        self._output("\n" + "=" * 80)
        self._output("🤖 [PROMPT DEBUG] After Model Call")
        self._output("=" * 80)

        if hasattr(response, "message"):
            msg = response.message
            self._output("\n🤖 MODEL RESPONSE:")
            self._output("-" * 40)
            self._output(self._format_message(msg))
            self._output("-" * 40)

            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                self._output(f"\n🔧 Tool calls: {len(tool_calls)}")
                for tc in tool_calls[:5]:
                    if isinstance(tc, dict):
                        self._output(f"   - {tc.get('name', 'unknown')}")

        self._output("=" * 80 + "\n")

    def wrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], "ModelResponse"],
    ) -> "ModelResponse":
        """Wrap model calls to log prompts (sync version).

        Args:
            request: The model request containing messages and system prompt.
            handler: The next handler in the middleware chain.

        Returns:
            The model response.
        """
        if not self.enabled:
            return handler(request)

        self._log_request(request)
        response = handler(request)

        if self.show_response:
            self._log_response(response)

        return response

    async def awrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], Awaitable["ModelResponse"]],
    ) -> "ModelResponse":
        """Wrap model calls to log prompts (async version).

        Args:
            request: The model request containing messages and system prompt.
            handler: The next handler in the middleware chain.

        Returns:
            The model response.
        """
        if not self.enabled:
            result: "ModelResponse" = await handler(request)
            return result

        self._log_request(request)
        response: "ModelResponse" = await handler(request)

        if self.show_response:
            self._log_response(response)

        return response

    def before_model(
        self,
        state: "AgentState",
        runtime: "Runtime",
    ) -> dict[str, Any] | None:
        """Fallback hook for before_model (deprecated in favor of wrap_model_call).

        Args:
            state: Current agent state with messages.
            runtime: LangGraph runtime context.

        Returns:
            None (does not modify state).
        """
        # This is kept for compatibility but wrap_model_call is preferred
        return None

    def after_model(
        self,
        state: "AgentState",
        runtime: "Runtime",
    ) -> dict[str, Any] | None:
        """Fallback hook for after_model (deprecated in favor of wrap_model_call).

        Args:
            state: Current agent state with messages.
            runtime: LangGraph runtime context.

        Returns:
            None (does not modify state).
        """
        # This is kept for compatibility but wrap_model_call handles responses
        return None
