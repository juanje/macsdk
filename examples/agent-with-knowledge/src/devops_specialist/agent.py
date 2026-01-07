"""DevOps Specialist agent implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from macsdk.core import get_answer_model, run_agent_with_tools
from macsdk.middleware import DatetimeContextMiddleware, TodoListMiddleware
from macsdk.tools.knowledge import get_knowledge_bundle

from .models import AgentResponse
from .prompts import SYSTEM_PROMPT, TODO_PLANNING_SPECIALIST_PROMPT
from .tools import get_tools

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

CAPABILITIES = """DevOps specialist with access to skills and facts knowledge systems.

Can help with:
- Service deployment and configuration
- Health monitoring and troubleshooting
- Infrastructure management
- CI/CD operations
- Log analysis

Uses knowledge tools for task guidance and contextual information."""


def create_devops_specialist(debug: bool = False) -> Any:
    """Create the DevOps Specialist agent.

    Args:
        debug: Whether to enable debug mode.

    Returns:
        Configured agent instance.
    """
    # Get all tools (includes knowledge tools)
    tools = get_tools()

    # Build system prompt with task planning
    system_prompt = SYSTEM_PROMPT + "\n\n" + TODO_PLANNING_SPECIALIST_PROMPT

    # Build middleware list
    middleware: list[Any] = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]

    # Add knowledge middleware (auto-injects usage instructions)
    _, knowledge_middleware = get_knowledge_bundle(__package__)
    middleware.extend(knowledge_middleware)

    agent: Any = create_agent(
        model=get_answer_model(),
        tools=tools,
        middleware=middleware,
        system_prompt=system_prompt,
        response_format=AgentResponse,
    )

    return agent


async def run_devops_specialist(
    query: str,
    context: dict | None = None,
    run_config: RunnableConfig | None = None,
    debug: bool = False,
) -> dict:
    """Run the DevOps Specialist agent.

    Args:
        query: User query to process.
        context: Optional context from previous interactions.
        run_config: Optional runnable configuration.
        debug: Whether to enable debug mode.

    Returns:
        Agent response dictionary.
    """
    agent = create_devops_specialist(debug=debug)
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        agent_name="devops_specialist",
        context=context,
        config=run_config,
    )


class DevOpsSpecialist:
    """DevOps Specialist agent that implements the SpecialistAgent protocol."""

    name: str = "devops_specialist"
    capabilities: str = CAPABILITIES
    tools: list = []

    def __init__(self) -> None:
        """Initialize the agent with tools (includes knowledge tools)."""
        self.tools = get_tools()

    async def run(
        self,
        query: str,
        context: dict | None = None,
        run_config: RunnableConfig | None = None,
        debug: bool = False,
    ) -> dict:
        """Execute the agent.

        Args:
            query: User query to process.
            context: Optional context from previous interactions.
            run_config: Optional runnable configuration.
            debug: Whether to enable debug mode.

        Returns:
            Agent response dictionary.
        """
        return await run_devops_specialist(query, context, run_config, debug)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool.

        Returns:
            A LangChain tool wrapping this agent.
        """
        agent_instance = self

        @tool
        async def devops_specialist(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Query the DevOps specialist with a natural language request.

            Args:
                query: What you want the specialist to do or find out.
                config: Runnable configuration (injected automatically).

            Returns:
                The specialist's response text.
            """
            result = await agent_instance.run(query, run_config=config)
            return str(result["response"])

        return devops_specialist
