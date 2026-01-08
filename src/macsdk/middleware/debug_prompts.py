"""Debug middleware to log prompts sent to LLM.

This middleware displays the system and user prompts being sent
to the LLM, useful for debugging and understanding agent behavior.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware

if TYPE_CHECKING:
    from langchain.agents.middleware import AgentState, ModelRequest
    from langchain.agents.middleware.types import ModelResponse
    from langgraph.runtime import Runtime

logger = logging.getLogger(__name__)


class PromptDebugMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Middleware that logs prompts, tool calls, and responses from the LLM.

    This middleware helps developers:
    - See the exact system prompt being used
    - View user messages as they are sent
    - Debug agent behavior and prompt engineering
    - Monitor tool calls with their complete arguments
    - Inspect tool execution results (ToolMessage)
    - Track AI responses and decisions
    - Optionally log model responses

    The middleware distinguishes between different message types:
    - System/User messages: Show prompts and user input
    - AI messages with tool_calls: Show which tools are being called with args
    - Tool messages: Show tool execution results
    - AI messages without tool_calls: Show regular text responses

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
        show_response: bool = True,
        max_length: int | None = None,
    ) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active.
            show_system: Whether to show system prompts.
            show_user: Whether to show user messages.
            show_response: Whether to show model responses (after_model).
            max_length: Maximum characters to show per message.
                       If None, reads from config.debug_prompt_max_length at runtime.

        Note:
            Output format (clean vs standard logging) is controlled by
            setup_logging(clean_llm_format=True) in core.logging, not here.
        """
        self.enabled = enabled
        self.show_system = show_system
        self.show_user = show_user
        self.show_response = show_response
        self._max_length_override = max_length
        self._cached_max_length: int | None = None
        logger.debug(f"PromptDebugMiddleware initialized (enabled={enabled})")

    @property
    def max_length(self) -> int:
        """Get max_length, lazily loading from config if not overridden."""
        if self._max_length_override is not None:
            return self._max_length_override

        # Return cached value if available
        if self._cached_max_length is not None:
            return self._cached_max_length

        # Lazy load from config at runtime and cache it
        from ..core.config import config

        self._cached_max_length = int(config.debug_prompt_max_length)
        return self._cached_max_length

    def _output(self, text: str) -> None:
        """Output LLM call info to application log (not stdout).

        Relies on logger configuration (set in core.logging.setup_logging)
        to handle formatting. The logger is configured with clean format
        and propagate=False when clean_format=True is passed to setup_logging.
        """
        logger.info(text)

    def _truncate(self, text: str) -> str:
        """Truncate text if too long."""
        if len(text) > self.max_length:
            return text[: self.max_length] + f"\n... (truncated, {len(text)} chars)"
        return text

    def _get_messages_from_request(self, request: "ModelRequest") -> list:
        """Extract messages from request or request.state.

        Args:
            request: The model request.

        Returns:
            List of messages, or empty list if none found.
        """
        messages = getattr(request, "messages", [])
        if not messages and hasattr(request, "state"):
            state = request.state
            if isinstance(state, dict):
                messages = state.get("messages", [])
            else:
                messages = getattr(state, "messages", [])
        return messages

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

    def _format_tool_call(self, tool_call: Any) -> str:
        """Format a tool call with its arguments.

        Args:
            tool_call: Tool call object or dict with name and args.

        Returns:
            Formatted string showing tool name and arguments.

        Warning:
            This logs raw tool arguments including potentially sensitive data.
            This middleware should ONLY be used in development environments.
        """
        if isinstance(tool_call, dict):
            name = tool_call.get("name", "unknown")
            args = tool_call.get("args", {})
        else:
            name = getattr(tool_call, "name", "unknown")
            args = getattr(tool_call, "args", {})

        # Pretty print arguments (default=str handles non-serializable objects)
        try:
            args_str = json.dumps(args, indent=2, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            args_str = str(args)

        return f"📞 {name}\n   Args: {self._truncate(args_str)}"

    def _get_agent_context(self, request: "ModelRequest") -> str:
        """Try to extract agent context from request for better debugging.

        Args:
            request: The model request.

        Returns:
            Agent context string (e.g., "supervisor", "toolbox") or empty string.
        """
        # Try to get context from state metadata
        if hasattr(request, "state"):
            state = request.state
            # Try dict access first (most common in LangGraph)
            if isinstance(state, dict):
                agent_name = state.get("agent_name")  # type: ignore[typeddict-item]
                if agent_name:
                    return f" [{agent_name}]"
                node = state.get("node")  # type: ignore[typeddict-item]
                if node:
                    return f" [{node}]"
            else:
                # Fallback to getattr for Pydantic models or other objects
                agent_name = getattr(state, "agent_name", None)
                if agent_name:
                    return f" [{agent_name}]"
                node = getattr(state, "node", None)
                if node:
                    return f" [{node}]"

        # Try to infer from system message content
        if hasattr(request, "system_message") and request.system_message:
            system_content = str(getattr(request.system_message, "content", ""))
            # Check first 1000 chars (increased from 300 for longer prompts)
            content_sample = system_content.lower()[:1000]
            if "supervisor" in content_sample:
                return " [supervisor]"
            if "specialist agent" in content_sample:
                return " [agent]"

        # Try to infer from first messages
        # (some agents pass system prompt as HumanMessage)
        messages = self._get_messages_from_request(request)

        if messages:
            # Check first message content for agent indicators
            first_msg = messages[0]
            first_content = str(getattr(first_msg, "content", ""))[:500].lower()

            if "supervisor" in first_content and "orchestrate" in first_content:
                return " [supervisor]"
            elif "specialist" in first_content or "you are a" in first_content:
                # Generic agent detection
                return " [agent]"

        return ""

    def _log_request(self, request: "ModelRequest") -> None:
        """Log the model request (system prompt and messages).

        Args:
            request: The model request to log.
        """
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        agent_context = self._get_agent_context(request)
        self._output(f"\n🔍 [LLM{agent_context}] Before Model Call")

        # Access system prompt via request.system_message
        if self.show_system and hasattr(request, "system_message"):
            system_msg = request.system_message
            if system_msg:
                self._output("\n📋 SYSTEM PROMPT:")

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

        # Access messages from request
        messages = self._get_messages_from_request(request)

        for i, msg in enumerate(messages):
            is_system = isinstance(msg, SystemMessage)
            is_human = isinstance(msg, HumanMessage)
            is_ai = isinstance(msg, AIMessage)
            is_tool = isinstance(msg, ToolMessage)

            if is_system and self.show_system:
                self._output(f"\n📋 SYSTEM MESSAGE (message {i + 1}):")
                self._output(self._format_message(msg))

            elif is_human and self.show_user:
                self._output(f"\n👤 USER MESSAGE (message {i + 1}):")
                self._output(self._format_message(msg))

            elif is_ai:
                # AIMessage may contain tool_calls or regular text response
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    self._output(f"\n🤖 AI MESSAGE - TOOL CALLS (message {i + 1}):")
                    self._output(f"🔧 Calling {len(tool_calls)} tool(s):")
                    for tc in tool_calls:
                        self._output(self._format_tool_call(tc))
                else:
                    # Regular AI response without tool calls
                    self._output(f"\n🤖 AI MESSAGE (message {i + 1}):")
                    self._output(self._format_message(msg))

            elif is_tool:
                # ToolMessage contains the result of a tool execution
                tool_name = getattr(msg, "name", "unknown")
                tool_call_id = getattr(msg, "tool_call_id", "unknown")
                status = getattr(msg, "status", None)

                status_icon = "✅" if status != "error" else "❌"
                self._output(f"\n🔨 TOOL RESULT (message {i + 1}):")
                self._output(
                    f"{status_icon} Tool: {tool_name} | Call ID: {tool_call_id}"
                )

                content = getattr(msg, "content", "")
                if content:
                    self._output(f"Result:\n{self._truncate(str(content))}")

                # Check for error information
                if hasattr(msg, "artifact") and msg.artifact:
                    self._output(f"Artifact: {msg.artifact}")

            elif not is_system and not is_human and not is_ai and not is_tool:
                msg_type = type(msg).__name__
                content_preview = str(getattr(msg, "content", ""))[:100]
                self._output(f"\n📨 {msg_type} (message {i + 1}): {content_preview}...")

        self._output(f"\n📊 Total messages: {len(messages)}\n")

    def _extract_message(self, response: "ModelResponse") -> Any:
        """Extract the message from a model response.

        Args:
            response: The model response to extract from.

        Returns:
            The extracted message, or None if extraction failed.

        Note:
            Handles multiple LangChain response structures:
            - Old: response.message (single AIMessage)
            - New: response.result (can be AIMessage or list of messages)
        """
        # Try old structure first (pre-v0.3)
        if hasattr(response, "message"):
            return response.message

        # Try newer structure (v0.3+)
        if hasattr(response, "result"):
            result = response.result
            # result might be a list of messages, take the last one (the AI response)
            if isinstance(result, list):
                msg = result[-1] if result else None
            else:
                msg = result

            # Verify it's message-like (has content or tool_calls)
            if msg and (hasattr(msg, "content") or hasattr(msg, "tool_calls")):
                return msg

        return None

    def _log_response(self, response: "ModelResponse", agent_context: str = "") -> None:
        """Log the model response.

        Args:
            response: The model response to log.
            agent_context: Optional agent context string.
        """
        self._output(f"\n🤖 [LLM{agent_context}] After Model Call")

        msg = self._extract_message(response)

        if msg is None:
            # Could not extract response - log diagnostic info
            self._output("\n⚠️  Could not extract response content")
            self._output(f"Response type: {type(response).__name__}")
            attrs = [a for a in dir(response) if not a.startswith("_")]
            self._output(f"Available attributes: {attrs}")
            self._output("")
            return

        # Log token usage if available (useful for cost tracking and optimization)
        if hasattr(msg, "response_metadata"):
            metadata = msg.response_metadata
            if isinstance(metadata, dict):
                # Different providers use different keys
                usage = metadata.get("usage") or metadata.get("token_usage")
                if usage:
                    self._output(f"\n📊 TOKEN USAGE: {usage}")

        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            # Model decided to call tools
            self._output(f"\n🔧 MODEL REQUESTING TOOL CALLS ({len(tool_calls)}):")
            for tc in tool_calls:
                self._output(self._format_tool_call(tc))
        else:
            # Regular text response
            self._output("\n🤖 MODEL RESPONSE:")
            self._output(self._format_message(msg))

        self._output("")  # Empty line for separation

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

        agent_context = self._get_agent_context(request)
        self._log_request(request)
        response = handler(request)

        if self.show_response:
            self._log_response(response, agent_context)

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

        agent_context = self._get_agent_context(request)
        self._log_request(request)
        response: "ModelResponse" = await handler(request)

        if self.show_response:
            self._log_response(response, agent_context)

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
