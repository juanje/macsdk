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
from macsdk.core import config, get_answer_model, run_agent_with_tools
from macsdk.middleware import (
    DatetimeContextMiddleware,
    PromptDebugMiddleware,
)
from macsdk.tools import get_sdk_middleware

from .models import AgentResponse
from .tools import get_tools

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


# CAPABILITIES: Brief description for supervisor routing
# The supervisor uses this to decide when to call this agent
# Skills and facts extend these capabilities with detailed instructions
CAPABILITIES = """DevOps specialist with knowledge-based task guidance.

This agent can help with:
- Service health monitoring and troubleshooting
- Deployment procedures and automation
- Infrastructure configuration
- CI/CD pipeline management
- Log analysis and debugging

The agent learns dynamically from skills (procedures) and facts (context)."""

# Optional: Extended instructions for this agent only (not sent to supervisor)
# Use this for critical instructions that must ALWAYS be in the agent's prompt:
# - Domain-specific behavior guidelines
# - API response handling rules
# - Data validation requirements
# - Important domain context
#
# Note: Final formatting is handled by the formatter agent, not here.
# Keep CAPABILITIES concise (supervisor sees it). Put detailed instructions here.
EXTENDED_INSTRUCTIONS = """You are a DevOps specialist with access to knowledge tools.

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

SYSTEM_PROMPT = CAPABILITIES


def create_devops_specialist(
    debug: bool | None = None,
) -> Any:
    """Create the DevOps Specialist agent.

    Args:
        debug: Whether to enable debug mode (shows prompts).
            If None, uses the config value (default: False).

    Returns:
        Configured agent instance.
    """
    # Get all tools (includes SDK internal + manual tools)
    tools = get_tools()

    # Build system prompt
    system_prompt = SYSTEM_PROMPT

    # Add extended instructions if defined
    if EXTENDED_INSTRUCTIONS:
        system_prompt += "\n\n" + EXTENDED_INSTRUCTIONS

    # Add task planning guidance (Chain-of-Thought prompts)
    system_prompt += "\n\n" + SPECIALIST_PLANNING_PROMPT

    # Build middleware list
    middleware: list[Any] = []

    # Add debug middleware if enabled
    debug_enabled = debug if debug is not None else config.debug
    if debug_enabled:
        middleware.append(
            PromptDebugMiddleware(
                enabled=True,
                show_response=True,
                max_length=int(config.debug_prompt_max_length),
            )
        )

    # Add datetime context middleware
    middleware.append(DatetimeContextMiddleware())

    # Add SDK middleware (auto-detects knowledge if dirs exist)
    middleware.extend(get_sdk_middleware(__package__))

    agent = create_agent(
        model=get_answer_model(),
        tools=tools,
        middleware=middleware,
        response_format=AgentResponse,
        system_prompt=system_prompt,
    )

    return agent


async def run_devops_specialist(
    query: str,
    context: dict | None = None,
    run_config: RunnableConfig | None = None,
    debug: bool | None = None,
) -> dict:
    """Run the DevOps Specialist agent.

    Args:
        query: User query to process.
        context: Optional context from previous interactions.
        run_config: Optional runnable configuration.
        debug: Whether to enable debug mode (shows prompts).
            If None, uses the config value (default: False).

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


class DevOpsSpecialistAgent:
    """DevOps Specialist agent with knowledge-based capabilities.

    This agent demonstrates how to use skills and facts to extend
    agent capabilities without modifying code.
    """

    name: str = "devops_specialist"
    capabilities: str = CAPABILITIES
    tools: list = []  # Loaded lazily

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
        return await run_devops_specialist(query, context, run_config, debug)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool.

        This allows the supervisor to call this agent as a tool,
        enabling dynamic agent orchestration.

        Returns:
            A LangChain tool wrapping this agent.
        """
        agent_instance = self

        @tool
        async def devops_specialist(
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

        return devops_specialist
