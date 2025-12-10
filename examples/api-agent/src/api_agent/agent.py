"""Agent implementation for api-agent.

This module demonstrates how to create an agent that uses
MACSDK's API tools for DevOps monitoring scenarios.

It combines:
- Generic SDK tools (api_get, fetch_file) for flexible API access
- Custom tools for specialized operations with JSONPath extraction
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from macsdk.core import get_answer_model, run_agent_with_tools
from macsdk.middleware import DatetimeContextMiddleware

from .models import AgentResponse
from .prompts import SYSTEM_PROMPT
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


def create_api_agent():
    """Create the api-agent agent.

    Returns:
        Configured agent instance with DevOps tools.
    """
    return create_agent(
        model=get_answer_model(),
        tools=get_tools(),
        middleware=[DatetimeContextMiddleware()],
        response_format=AgentResponse,
    )


async def run_api_agent(
    query: str,
    context: dict | None = None,
    config: RunnableConfig | None = None,
) -> dict:
    """Run the api-agent agent.

    Args:
        query: User query to process.
        context: Optional context from previous interactions.
        config: Optional runnable configuration.

    Returns:
        Agent response dictionary.
    """
    agent = create_api_agent()
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        system_prompt=SYSTEM_PROMPT,
        agent_name="api_agent",
        context=context,
        config=config,
    )


class ApiAgentAgent:
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
        config: RunnableConfig | None = None,
    ) -> dict:
        """Execute the agent.

        Args:
            query: User query to process.
            context: Optional context from previous interactions.
            config: Optional runnable configuration.

        Returns:
            Agent response dictionary.
        """
        return await run_api_agent(query, context, config)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool."""
        agent_instance = self

        @tool
        async def invoke_api_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Query DevOps infrastructure for pipelines, jobs, services, and alerts.

            Use this tool when the user wants to:
            - Check pipeline status (list, failed, running)
            - Investigate failed jobs and download logs
            - Monitor service health (healthy, degraded, warning)
            - View alerts (unacknowledged, critical)
            - Check deployment history

            Args:
                query: The query to process.
                config: Runnable configuration (injected).

            Returns:
                The agent's response text.
            """
            result = await agent_instance.run(query, config=config)
            return result["response"]

        return invoke_api_agent
