"""Agent implementation for api-agent.

This module demonstrates how to create an agent that uses
MACSDK's API tools for DevOps monitoring scenarios.

It combines:
- Generic SDK tools (api_get, fetch_file) for flexible API access
- Custom tools for specialized operations with JSONPath extraction
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from macsdk.core import config, get_answer_model, run_agent_with_tools
from macsdk.middleware import (
    DatetimeContextMiddleware,
    PromptDebugMiddleware,
    TodoListMiddleware,
)

from .models import AgentResponse
from .prompts import SYSTEM_PROMPT, TODO_PLANNING_SPECIALIST_PROMPT
from .tools import get_tools

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


CAPABILITIES = """DevOps monitoring agent using MACSDK API tools.

This agent can:
- Monitor CI/CD pipelines and investigate failures
- Check infrastructure service health
- Review alerts (critical, warnings, unacknowledged)
- Track deployments across environments
- Download and analyze job logs

Uses generic SDK tools (api_get, fetch_file) plus custom tools
for specialized operations with JSONPath extraction."""


def create_api_agent(
    debug: bool | None = None,
) -> Any:
    """Create the api-agent agent.

    Args:
        debug: Whether to enable debug mode (shows prompts).
            If None, uses the config value (default: False).

    Returns:
        Configured agent instance.
    """
    # Build system prompt with task planning integrated
    # TODO middleware is always enabled
    system_prompt = SYSTEM_PROMPT + "\n\n" + TODO_PLANNING_SPECIALIST_PROMPT

    # Build middleware list
    middleware: list[Any] = []

    # Add debug middleware if enabled (via parameter or config)
    debug_enabled = debug if debug is not None else config.debug
    if debug_enabled:
        middleware.append(PromptDebugMiddleware(enabled=True, show_response=True))

    # Add datetime context middleware
    middleware.append(DatetimeContextMiddleware())

    # Add todo middleware (always enabled for task planning)
    middleware.append(TodoListMiddleware(enabled=True))

    agent = create_agent(
        model=get_answer_model(),
        tools=get_tools(),
        middleware=middleware,
        response_format=AgentResponse,
        system_prompt=system_prompt,
    )

    return agent


async def run_api_agent(
    query: str,
    context: dict | None = None,
    run_config: RunnableConfig | None = None,
    debug: bool | None = None,
) -> dict:
    """Run the api-agent agent.

    Args:
        query: User query to process.
        context: Optional context from previous interactions.
        run_config: Optional runnable configuration.
        debug: Whether to enable debug mode (shows prompts).
            If None, uses the config value (default: False).

    Returns:
        Agent response dictionary.
    """
    agent = create_api_agent(debug=debug)
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        agent_name="api_agent",
        context=context,
        config=run_config,
    )


class ApiAgent:
    """DevOps monitoring agent using MACSDK API tools.

    This agent demonstrates the recommended pattern for API integrations:
    1. Register services with ApiServiceRegistry
    2. Use generic SDK tools (api_get, fetch_file) for flexibility
    3. Create custom tools with make_api_request for JSONPath extraction
    4. Describe API schema in the prompt for the LLM
    """

    name: str = "api_agent"
    capabilities: str = CAPABILITIES
    tools: list = []  # Loaded in __init__

    def __init__(self) -> None:
        """Initialize the agent with tools."""
        self.tools = get_tools()

    async def run(
        self,
        query: str,
        context: dict | None = None,
        run_config: RunnableConfig | None = None,
        debug: bool | None = None,
    ) -> dict:
        """Execute the agent.

        Args:
            query: User query to process.
            context: Optional context from previous interactions.
            run_config: Optional runnable configuration.
            debug: Whether to enable debug mode (shows prompts).

        Returns:
            Agent response dictionary.
        """
        return await run_api_agent(query, context, run_config, debug)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool."""
        agent_instance = self

        @tool
        async def api_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Query this specialist agent with a natural language request.

            Args:
                query: What you want this agent to do or find out.
                config: Runnable configuration (injected automatically).

            Returns:
                The agent's response text.
            """
            result = await agent_instance.run(query, run_config=config)
            return str(result["response"])

        return api_agent
