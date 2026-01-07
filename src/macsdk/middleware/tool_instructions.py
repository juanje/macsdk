"""Tool instructions middleware for MACSDK agents.

This middleware injects usage instructions for specific tool sets,
helping agents understand how to use complementary tools like
list_skills/read_skill and list_facts/read_fact correctly.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware import AgentMiddleware

from .tool_instructions_prompts import (
    FACTS_INSTRUCTIONS,
    KNOWLEDGE_SYSTEM_INSTRUCTIONS,
    SKILLS_INSTRUCTIONS,
)

if TYPE_CHECKING:
    from langchain.agents.middleware import ModelRequest
    from langchain.agents.middleware.types import ModelResponse

logger = logging.getLogger(__name__)


class ToolInstructionsMiddleware(AgentMiddleware):  # type: ignore[type-arg]
    """Middleware that injects usage instructions for specific tool sets.

    This middleware inspects the agent's tools and automatically adds
    relevant usage instructions to the system prompt. Instructions are
    cached per session for efficiency.

    Currently supports:
    - Skills/Facts knowledge system (list_skills, read_skill, list_facts, read_fact)

    Note: Tool detection relies on exact name matching. If tools are renamed
    (e.g., via aliasing), the middleware will not detect them. This is by design
    as these tool names are part of the public API contract. If you need custom
    tool names, instantiate this middleware with your own tool name mappings
    by subclassing or modifying TOOL_PATTERNS.

    Example:
        >>> from macsdk.middleware import ToolInstructionsMiddleware
        >>> from macsdk.tools.knowledge import get_knowledge_bundle
        >>>
        >>> knowledge_tools, knowledge_middleware = get_knowledge_bundle(__package__)
        >>> # knowledge_middleware already contains ToolInstructionsMiddleware
        >>> agent = create_agent(
        ...     model=get_answer_model(),
        ...     tools=[*my_tools, *knowledge_tools],
        ...     middleware=[*my_middleware, *knowledge_middleware],
        ... )
    """

    # Mapping of tool sets → instructions (pairs)
    # These tool names are part of the public API contract
    TOOL_PATTERNS: dict[frozenset[str], str] = {
        frozenset({"list_skills", "read_skill"}): SKILLS_INSTRUCTIONS,
        frozenset({"list_facts", "read_fact"}): FACTS_INSTRUCTIONS,
    }

    # Combined instructions (priority over individual patterns)
    COMBINED_PATTERNS: dict[frozenset[str], str] = {
        frozenset(
            {"list_skills", "read_skill", "list_facts", "read_fact"}
        ): KNOWLEDGE_SYSTEM_INSTRUCTIONS,
    }

    def __init__(self, tools: list[Callable[..., Any]], enabled: bool = True) -> None:
        """Initialize the middleware.

        Args:
            tools: List of tool functions the agent has access to.
            enabled: Whether the middleware is active.
        """
        self.enabled = enabled
        self.tool_names = self._extract_tool_names(tools)
        self._cached_instructions: str | None = None
        logger.debug(
            f"ToolInstructionsMiddleware initialized with tools: {self.tool_names}"
        )

    def _extract_tool_names(self, tools: list[Callable[..., Any]]) -> set[str]:
        """Extract tool names, handling both raw functions and LangChain tools.

        Args:
            tools: List of tool functions or BaseTool instances.

        Returns:
            Set of tool names.
        """
        names = set()
        for tool in tools:
            # LangChain BaseTool has a 'name' attribute
            if hasattr(tool, "name"):
                names.add(tool.name)
            else:
                names.add(getattr(tool, "__name__", str(tool)))
        return names

    def _get_instructions(self) -> str:
        """Get cached instructions based on detected tools.

        Returns:
            Formatted instruction string, or empty string if no patterns match.
        """
        if self._cached_instructions is not None:
            return self._cached_instructions

        parts = []

        # First check combined patterns (more specific, takes priority)
        matched_combined = False
        for pattern, instructions in self.COMBINED_PATTERNS.items():
            if pattern.issubset(self.tool_names):
                parts.append(instructions)
                matched_combined = True
                logger.debug(f"Using combined pattern: {pattern}")
                break  # Only use one combined pattern

        # If no combined pattern matched, check individual patterns
        if not matched_combined:
            for pattern, instructions in self.TOOL_PATTERNS.items():
                if pattern.issubset(self.tool_names):
                    parts.append(instructions)
                    logger.debug(f"Using individual pattern: {pattern}")

        self._cached_instructions = "\n\n".join(parts)
        return self._cached_instructions

    def wrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], "ModelResponse"],
    ) -> "ModelResponse":
        """Inject tool instructions into the system message (sync).

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

        self._inject_tool_instructions(request)
        return handler(request)

    async def awrap_model_call(
        self,
        request: "ModelRequest",
        handler: Callable[["ModelRequest"], Awaitable["ModelResponse"]],
    ) -> "ModelResponse":
        """Inject tool instructions into the system message (async).

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

        self._inject_tool_instructions(request)
        return await handler(request)

    def _inject_tool_instructions(self, request: "ModelRequest") -> None:
        """Inject tool instructions into request.system_message.

        This method modifies the system_message in the request to append
        tool instructions at the end, which is optimal for LLM caching.

        Idempotent: checks if instructions are already present to prevent
        duplication on request retries.

        Args:
            request: The model request containing the system_message to modify.
        """
        from langchain_core.messages import SystemMessage

        instructions = self._get_instructions()
        if not instructions:
            logger.debug("No tool patterns matched, skipping injection")
            return

        if hasattr(request, "system_message") and request.system_message:
            # Extract text content (handle both str and structured content)
            current_content = request.system_message.content
            if isinstance(current_content, list):
                # Structured content - extract text parts
                text_parts = [
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in current_content
                ]
                content_str = "".join(text_parts)
            else:
                content_str = str(current_content)

            # Idempotency check: prevent duplication on retries
            if instructions in content_str:
                logger.debug("Instructions already present, skipping injection")
                return

            # Append instructions at the END for better LLM caching
            new_content = f"{content_str}\n\n{instructions}"
            request.system_message = SystemMessage(content=new_content)
            logger.debug("Injected tool instructions into system_message")
        elif instructions:
            # Create system message if none exists and we have instructions
            request.system_message = SystemMessage(content=instructions)
            logger.debug("Created system_message with tool instructions")
