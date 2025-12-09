"""Callback handlers for MACSDK.

This module provides callback handlers for intercepting LangChain events
and emitting progress messages in real-time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import BaseCallbackHandler

from .utils import log_progress

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig


class ToolProgressCallback(BaseCallbackHandler):
    """Callback handler that logs tool usage in real-time.

    This handler emits progress messages when tools are called,
    providing transparency to users about what the agent is doing.
    """

    def __init__(
        self,
        agent_name: str = "agent",
        config: "RunnableConfig | None" = None,
    ) -> None:
        """Initialize the callback handler.

        Args:
            agent_name: Name of the agent for log prefixes.
            config: Optional RunnableConfig for stream writer access.
        """
        super().__init__()
        self.agent_name = agent_name
        self.config = config

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts running.

        Args:
            serialized: Serialized tool information.
            input_str: The input to the tool.
            run_id: Unique identifier for this run.
            parent_run_id: Parent run identifier if nested.
            tags: Optional tags for the run.
            metadata: Optional metadata for the run.
            inputs: Tool inputs dictionary.
            **kwargs: Additional keyword arguments.
        """
        tool_name = serialized.get("name", "unknown_tool")
        log_progress(f"[{self.agent_name}] 🔧 Using tool: {tool_name}\n", self.config)

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes running.

        Args:
            output: The output from the tool.
            run_id: Unique identifier for this run.
            parent_run_id: Parent run identifier if nested.
            tags: Optional tags for the run.
            **kwargs: Additional keyword arguments.
        """
        # Optionally log completion - keeping it quiet to reduce noise
        pass

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        parent_run_id: Any | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool errors.

        Args:
            error: The error that occurred.
            run_id: Unique identifier for this run.
            parent_run_id: Parent run identifier if nested.
            tags: Optional tags for the run.
            **kwargs: Additional keyword arguments.
        """
        log_progress(
            f"[{self.agent_name}] ⚠️ Tool error: {error!s}\n",
            self.config,
        )
