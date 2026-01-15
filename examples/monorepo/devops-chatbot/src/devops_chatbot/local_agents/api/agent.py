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
CAPABILITIES = """DevOps monitoring assistant using MACSDK API tools.

This agent can:
- Monitor CI/CD pipelines and investigate failures
- Check infrastructure service health
- Review alerts (critical, warnings, unacknowledged)
- Track deployments across environments
- Download and analyze job logs"""

# Optional: Extended instructions for this agent only (not sent to supervisor)
# Use this for critical instructions that must ALWAYS be in the agent's prompt:
# - Domain-specific behavior guidelines
# - API response handling rules
# - Data validation requirements
# - Important domain context
#
# Note: Final formatting is handled by the formatter agent, not here.
# Keep CAPABILITIES concise (supervisor sees it). Put detailed instructions here.
EXTENDED_INSTRUCTIONS = """You are a DevOps monitoring specialist with access to MACSDK API tools.

## API Service: "devops"

You have access to a DevOps monitoring API with these endpoints:

### Services (Infrastructure Health)
- GET /services - List all services
- GET /services/{id} - Get specific service (id: 1-6)
  Fields: id, name, status (healthy/degraded/warning), uptime, last_check, issues

### Alerts
- GET /alerts - List all alerts
- GET /alerts with params {"severity": "critical"} - Filter by severity
- GET /alerts with params {"acknowledged": "false"} - Unacknowledged alerts
  Fields: id, title, severity (info/warning/critical), service, acknowledged

### Pipelines (CI/CD)
- GET /pipelines - List all pipelines
- GET /pipelines/{id} - Get specific pipeline (id: 1-5)
- GET /pipelines with params {"status": "failed"} - Filter by status
  Fields: id, name, status (passed/failed/running/pending), branch, commit

### Jobs
- GET /jobs - List all jobs
- GET /jobs with params {"pipelineId": "1"} - Jobs for a pipeline
- GET /jobs with params {"status": "failed"} - Failed jobs
  Fields: id, name, pipelineId, status, duration, error, log_url

### Deployments
- GET /deployments - List all deployments
- GET /deployments with params {"environment": "production"} - Filter by env
  Fields: id, version, environment, status, deployed_by, created_at

## Available Tools

### Generic Tools (use with any endpoint)
- **api_get**: Make GET requests to any endpoint above
- **fetch_file**: Download files (logs, configs) from URLs
- **calculate**: Safe math evaluation (always use for numbers)

### Custom Tools (specialized operations)
- **get_service_health_summary**: Quick overview of all services health
- **get_failed_pipeline_names**: List names of failed pipelines
- **investigate_failed_job**: Deep investigation with log analysis

## Guidelines

1. Use `api_get` with service="devops" for most queries
2. Use custom tools when they match the use case exactly
3. For failed jobs, use `investigate_failed_job` to get full details with logs
4. When asked about services, `get_service_health_summary` gives a quick overview
5. Always provide actionable insights based on the data
6. Always use calculate() for any math operations - never compute mentally
"""

SYSTEM_PROMPT = CAPABILITIES


def create_api_agent(
    debug: bool | None = None,
) -> Any:
    """Create the api-agent.

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


async def run_api_agent(
    query: str,
    context: dict | None = None,
    run_config: RunnableConfig | None = None,
    debug: bool | None = None,
) -> dict:
    """Run the api-agent.

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
    4. Describe API schema in CAPABILITIES for the LLM
    """

    name: str = "api_agent"
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
        return await run_api_agent(query, context, run_config, debug)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool.

        This allows the supervisor to call this agent as a tool,
        enabling dynamic agent orchestration.

        Returns:
            A LangChain tool wrapping this agent.
        """
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
