"""DevOps Specialist agent implementation.

This agent demonstrates using knowledge tools (skills and facts) to extend
agent capabilities without modifying code. CAPABILITIES defines what the
agent does, while skills and facts provide detailed instructions and context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from macsdk.agents.supervisor import SPECIALIST_PLANNING_PROMPT
from macsdk.core import get_answer_model, run_agent_with_tools
from macsdk.middleware import DatetimeContextMiddleware, TodoListMiddleware
from macsdk.tools.knowledge import get_knowledge_bundle

from .models import AgentResponse
from .tools import get_tools

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


# CAPABILITIES is the single source of truth for this agent:
# - Used as the system prompt for the LLM
# - Used by the supervisor to decide when to route queries here
# - Skills and facts extend these capabilities with detailed instructions
CAPABILITIES = """DevOps specialist with knowledge-based task guidance.

This agent can help with:
- Service health monitoring and troubleshooting
- Deployment procedures and automation
- Infrastructure configuration
- CI/CD pipeline management
- Log analysis and debugging

## Tools Available

You have access to:
- Generic API tools (api_get) for REST calls
- File fetching tools (fetch_file) for logs and configs
- Calculate tool for any math operations
- **Skills system** for step-by-step task instructions
- **Facts system** for contextual information and reference data

## Guidelines

1. **Use skills first**: Before attempting complex tasks, check if there's a
   relevant skill with instructions (the available skills are listed in
   the system prompt)
2. **Consult facts**: Use facts to get accurate service names, configurations,
   and policies
3. **Calculate accurately**: Always use calculate() for math - never compute
   mentally
4. **Be systematic**: Follow documented procedures from skills when available
5. **Verify your work**: Check results and report any issues clearly

**Math**: Always use calculate() for any numeric operation. Never compute
mentally.
"""

# CAPABILITIES is the system prompt
SYSTEM_PROMPT = CAPABILITIES


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
    system_prompt = SYSTEM_PROMPT + "\n\n" + SPECIALIST_PLANNING_PROMPT

    # Build middleware list
    middleware: list[Any] = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]

    # Add knowledge middleware (auto-injects skills/facts inventory)
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
    """DevOps Specialist agent that implements the SpecialistAgent protocol.

    This agent extends its capabilities through knowledge tools:
    - Skills: Step-by-step instructions for tasks (skills/*.md)
    - Facts: Contextual information and reference data (facts/*.md)
    """

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
