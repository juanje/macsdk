"""ToDo list middleware for task planning in agents.

This middleware wraps LangChain's TodoListMiddleware to provide agents
with task planning capabilities for complex multi-step queries.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.agents.middleware import TodoListMiddleware as LCTodoListMiddleware

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TodoListMiddleware(LCTodoListMiddleware):  # type: ignore[misc]
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

    The middleware adds a to-do list to the agent's context that the
    agent can manage using natural language in its reasoning:

    Agent behavior:
    - "Let me break this down: First check pipeline status, then investigate"
    - "I've checked the pipeline. Now I need to get the job details."
    - "Task complete. I have all the information needed."

    Note:
        The to-do list is internal to the agent. It doesn't require explicit
        tool calls - the agent naturally plans and tracks tasks in its reasoning.
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the middleware.

        Args:
            enabled: Whether the middleware is active. If False,
                     the middleware passes through without modification.
        """
        super().__init__()
        self.enabled = enabled
        logger.debug(f"TodoListMiddleware initialized (enabled={enabled})")
