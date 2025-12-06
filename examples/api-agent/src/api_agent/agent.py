"""Agent implementation for api-agent.

This module demonstrates how to create an agent that uses
MACSDK's API tools with the ApiServiceRegistry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from macsdk.core import get_answer_model, run_agent_with_tools

from .models import AgentResponse
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


CAPABILITIES = """Demonstrates MACSDK API tools with JSONPlaceholder.
Uses api_get/api_post from macsdk.tools with registered services.
Shows JSONPath extraction for specific field queries.
Can retrieve users, posts, comments, and TODOs."""


def create_api_agent():
    """Create the api-agent agent.

    Returns:
        Configured agent instance with API tools.
    """
    return create_agent(
        model=get_answer_model(),
        tools=TOOLS,
        middleware=[],
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
    """Agent demonstrating MACSDK API tools.

    This agent shows the recommended pattern for API integrations:
    1. Register services with ApiServiceRegistry
    2. Create domain-specific tools using api_get/api_post
    3. Use JSONPath for extracting specific data
    """

    name: str = "api_agent"
    capabilities: str = CAPABILITIES
    tools: list = TOOLS

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
            """Query JSONPlaceholder API for users, posts, comments, or TODOs.

            Use this tool when the user wants to:
            - Look up user information or emails
            - Find posts by a user or post titles
            - Read comments on posts
            - Check TODO lists (all, completed, or pending)
            - Create new posts (simulated)

            Args:
                query: The query to process.
                config: Runnable configuration (injected).

            Returns:
                The agent's response text.
            """
            result = await agent_instance.run(query, config=config)
            return result["response"]

        return invoke_api_agent
