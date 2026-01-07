"""ToDo list middleware for task planning in agents.

This middleware provides agents with task planning capabilities for complex
multi-step queries WITHOUT requiring explicit tool calls.

Instead of using write_todos/read_todos tools (which add extra LLM calls),
this middleware manages the plan internally and injects it into the prompt.

The middleware is STATELESS: it reconstructs the current plan by scanning
the conversation history for <plan> and <task_complete> tags. This ensures
compatibility with LangGraph persistence and multi-turn conversations.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import BaseMessage

if TYPE_CHECKING:
    from langchain.agents.middleware import ModelRequest
    from langchain.agents.middleware.types import ModelResponse

logger = logging.getLogger(__name__)

# Delimiters for plan context block
PLAN_CONTEXT_START = "<!-- macsdk:plan:start -->"
PLAN_CONTEXT_END = "<!-- macsdk:plan:end -->"
PLAN_CONTEXT_HEADER = "## Current Task Plan"

# Tags used by the agent to create/update plans
# These must match the tags in prompts.py
TAG_PLAN_START = "<plan>"
TAG_PLAN_END = "</plan>"
TAG_TASK_COMPLETE_START = "<task_complete>"
TAG_TASK_COMPLETE_END = "</task_complete>"


class TodoListMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Middleware that equips agents with task planning capabilities.

    This middleware allows agents to:
    - Break down complex queries into manageable tasks
    - Track progress on multi-step investigations
    - Mark tasks as complete
    - See remaining work in their context

    Particularly useful for:
    - Complex multi-agent coordination
    - Sequential investigations with dependencies
    - Long-running tasks requiring multiple tool calls

    Example:
        >>> from macsdk.middleware import TodoListMiddleware
        >>> from langchain.agents import create_agent
        >>>
        >>> middleware = [TodoListMiddleware()]
        >>> agent = create_agent(
        ...     model=get_answer_model(),
        ...     tools=tools,
        ...     middleware=middleware,
        ... )

    The middleware is STATELESS: it reconstructs the plan from conversation
    history on each call, ensuring compatibility with LangGraph persistence.

    Agent behavior:
    - Creates plan: "<plan>Check pipeline\\nGet logs\\nAnalyze results</plan>"
    - Updates task: "<task_complete>Check pipeline</task_complete>"
    - Sees progress: "Current Plan: ✓Check pipeline, →Get logs, ○Analyze"

    Note:
        Unlike the LangChain TodoListMiddleware, this implementation does NOT
        add write_todos/read_todos tools, avoiding extra LLM calls. The plan
        is managed purely through text in the prompt and response parsing.
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active. If False,
                     the middleware passes through without modification.
        """
        self.enabled = enabled

        # Pre-compile regex patterns for performance
        self._plan_pattern = re.compile(
            re.escape(TAG_PLAN_START) + r"(.*?)" + re.escape(TAG_PLAN_END),
            flags=re.DOTALL | re.IGNORECASE,
        )
        self._task_complete_pattern = re.compile(
            re.escape(TAG_TASK_COMPLETE_START)
            + r"(.*?)"
            + re.escape(TAG_TASK_COMPLETE_END),
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Combined pattern to detect both plan and completion tags in order
        self._combined_pattern = re.compile(
            f"({re.escape(TAG_PLAN_START)}.*?{re.escape(TAG_PLAN_END)})|"
            f"({re.escape(TAG_TASK_COMPLETE_START)}.*?"
            f"{re.escape(TAG_TASK_COMPLETE_END)})",
            flags=re.DOTALL | re.IGNORECASE,
        )
        self._cleanup_pattern = re.compile(
            re.escape(PLAN_CONTEXT_START) + r".*?" + re.escape(PLAN_CONTEXT_END),
            flags=re.DOTALL,
        )

        logger.debug(f"TodoListMiddleware initialized (enabled={enabled})")

    def _normalize_task_name(self, task: str) -> str:
        """Normalize a task name for comparison.

        Removes trailing punctuation and extra whitespace to make
        task matching more robust against minor LLM variations.

        Args:
            task: Task name to normalize.

        Returns:
            Normalized task name (lowercase, stripped, no trailing punctuation).
        """
        # Strip whitespace and convert to lowercase
        normalized = task.strip().lower()
        # Remove common trailing punctuation
        while normalized and normalized[-1] in ".,;:!?":
            normalized = normalized[:-1].strip()
        return normalized

    def _reconstruct_plan_from_history(
        self, messages: list[BaseMessage]
    ) -> list[dict[str, str]]:
        """Reconstruct the current plan by scanning conversation history.

        This ensures the middleware is stateless and compatible with
        LangGraph persistence. The plan state is derived from messages,
        not stored in memory.

        Tags are processed in the order they appear to correctly handle
        cases where an agent completes tasks and creates a new plan in
        the same message.

        Args:
            messages: List of conversation messages.

        Returns:
            Current plan as list of task dicts with 'task' and 'status' keys.
        """
        current_plan: list[dict[str, str]] = []

        # Scan through messages to find plans and updates
        # Only process AI messages to prevent user input hijacking
        for msg in messages:
            if msg.type != "ai":
                continue

            # Extract text content from message
            content = ""
            if isinstance(msg.content, str):
                content = msg.content
            elif isinstance(msg.content, list):
                # Handle multi-part messages (strings, dicts, or mixed)
                content = " ".join(
                    str(part.get("text", "")) if isinstance(part, dict) else str(part)
                    for part in msg.content
                )
            else:
                # Skip messages with unexpected content types
                continue

            # Process all tags in order of appearance
            for match in self._combined_pattern.finditer(content):
                plan_block, complete_block = match.groups()

                if plan_block:
                    # Extract plan content and create new plan
                    plan_match = self._plan_pattern.search(plan_block)
                    if plan_match:
                        plan_text = plan_match.group(1).strip()
                        tasks = [t.strip() for t in plan_text.splitlines() if t.strip()]

                        if tasks:
                            current_plan = [
                                {"task": task, "status": "pending"} for task in tasks
                            ]
                            # Mark first task as in_progress
                            if current_plan:
                                current_plan[0]["status"] = "in_progress"
                            logger.debug(
                                f"Reconstructed plan with {len(current_plan)} tasks "
                                "from history"
                            )

                elif complete_block and current_plan:
                    # Extract completion and update current plan
                    complete_match = self._task_complete_pattern.search(complete_block)
                    if complete_match:
                        completed_task = complete_match.group(1).strip()

                        # Find and mark task as completed
                        # (normalized match: case-insensitive, no trailing punctuation)
                        task_found = False
                        normalized_completed = self._normalize_task_name(completed_task)
                        for task in current_plan:
                            if (
                                self._normalize_task_name(task["task"])
                                == normalized_completed
                            ):
                                task["status"] = "completed"
                                task_found = True
                                logger.debug(
                                    f"Marked task as completed: {completed_task}"
                                )
                                break

                        if not task_found:
                            logger.warning(
                                f"Task completion requested but not found in plan: "
                                f"{completed_task}"
                            )

                        # Move in_progress marker to next pending task
                        # Only if no other task is currently in_progress
                        has_in_progress = any(
                            t["status"] == "in_progress" for t in current_plan
                        )
                        if not has_in_progress:
                            for task in current_plan:
                                if task["status"] == "pending":
                                    task["status"] = "in_progress"
                                    logger.debug(
                                        f"Marked task as in_progress: {task['task']}"
                                    )
                                    break

        return current_plan

    def _format_plan(self, plan: list[dict[str, str]]) -> str:
        """Format a plan for display in the prompt.

        Args:
            plan: List of task dicts with 'task' and 'status' keys.

        Returns:
            Formatted plan string with status indicators.
        """
        if not plan:
            return ""

        lines = [PLAN_CONTEXT_START, PLAN_CONTEXT_HEADER, ""]
        for task in plan:
            status = task["status"]
            task_text = task["task"]

            if status == "completed":
                icon = "✓"
            elif status == "in_progress":
                icon = "→"
            else:  # pending
                icon = "○"

            lines.append(f"{icon} {task_text}")

        lines.append("")
        lines.append(
            f"**To update:** {TAG_TASK_COMPLETE_START}task name{TAG_TASK_COMPLETE_END}"
        )
        lines.append(
            f"**To create plan:** {TAG_PLAN_START}Task 1\\nTask 2\\nTask 3"
            f"{TAG_PLAN_END}"
        )
        lines.append(PLAN_CONTEXT_END)

        return "\n".join(lines)

    def _remove_stale_plan(self, content: str) -> str:
        """Remove old plan context from content if present.

        Args:
            content: The content string to clean.

        Returns:
            Content with plan context removed.
        """
        if PLAN_CONTEXT_START in content and PLAN_CONTEXT_END in content:
            content = self._cleanup_pattern.sub("", content).strip()
            logger.debug("Removed stale plan context")
        return content

    def _inject_plan_context(self, request: "ModelRequest") -> None:
        """Reconstruct plan from history and inject into request.system_message.

        Args:
            request: The model request containing the system_message to modify.
        """
        from langchain_core.messages import SystemMessage

        # Check if there's a system_message to modify
        if not (hasattr(request, "system_message") and request.system_message):
            logger.debug("No system_message in request, skipping plan injection")
            return

        # Reconstruct plan from message history
        messages = getattr(request, "messages", [])
        current_plan = self._reconstruct_plan_from_history(messages)

        content = str(request.system_message.content)

        # Remove old plan context if present
        content = self._remove_stale_plan(content)

        # Inject current plan if we have one
        if current_plan:
            plan_context = self._format_plan(current_plan)
            # Inject at the END of the system prompt for better caching
            new_content = f"{content}\n\n{plan_context}"
            request.system_message = SystemMessage(content=new_content)
            logger.debug("Injected plan context into system_message")

    def wrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], "ModelResponse"],
    ) -> "ModelResponse":
        """Inject plan context before call (sync).

        Args:
            request: The model request.
            handler: The next handler in the middleware chain.

        Returns:
            The model response from the handler.
        """
        if not self.enabled:
            return handler(request)

        # Inject plan into prompt (reconstructed from history)
        self._inject_plan_context(request)

        # Call the model
        return handler(request)

    async def awrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], Awaitable["ModelResponse"]],
    ) -> "ModelResponse":
        """Inject plan context before call (async).

        Args:
            request: The model request.
            handler: The next async handler in the middleware chain.

        Returns:
            The model response from the handler.
        """
        if not self.enabled:
            return await handler(request)

        # Inject plan into prompt (reconstructed from history)
        self._inject_plan_context(request)

        # Call the model
        return await handler(request)
