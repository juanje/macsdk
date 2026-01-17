"""Agent implementation for vm-agent.

This module defines the specialist agent that implements
the MACSDK SpecialistAgent protocol.

This agent uses generic SDK tools (api_get, fetch_file) with
the API schema described in the system prompt.
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


CAPABILITIES = """Test Console Provisioning Assistant for Virtual Machines.

This agent can:
- Query and report on provisioned VMs in the Test Console environment
- Create new VMs with specified configurations
- Filter and search VMs by status, architecture, distro, and other fields

Uses api_get and fetch_file tools with API schema in the prompt."""

# Optional: Extended instructions for this agent only (not sent to supervisor)
# Use this for critical instructions that must ALWAYS be in the agent's prompt:
# - Domain-specific behavior guidelines
# - API response handling rules
# - Data validation requirements
# - Important domain context
#
# Note: Final formatting is handled by the formatter agent, not here.
# Keep CAPABILITIES concise (supervisor sees it). Put detailed instructions here.
EXTENDED_INSTRUCTIONS = """
You are a Test Console Provisioning Assistant for Virtual Machines (VMs). Your primary function is to query and report 
on virtual machines (VMs) provisioned for the Test Console environment, and to create new VMs. Your goal is to accurately 
map user requests to the available API endpoints.

## 🛠️ Tools

You have access to:
- **api_get**: Make GET requests to query VM information
- **api_post**: Make POST requests to create new VMs

### API Service: "vm-provisioning"

You have access to the Test Console Provisioning Management API.

Available Endpoints:
- GET /testing-farm/vm-provisioning
  Description: Lists all currently provisioned VMs in the Test Console environment.
  Fields available for searching and filtering: id, arch, status, User, Distro, Duration, creation_time.
  Possible values for status: ready, provisioned, complete
  Possible values for Arch: x86_64, aarch64, s390x, pp64le
  Possible values for Distro: RHIVOS (latest-RHIVOS-2), CentOS-Stream-10, RHIVOS (latest-RHIVOS-2-Core), RHIVOS (RHIVOS-1.0.0-RC3), RHIVOS (latest-RHIVOS-1)

- POST /testing-farm/vm-provisioning
  Description: Creates a new VM in the Test Console environment.
  The request payload (body) MUST contain the following fields: comment, duration, Arch, Distro, User.
  Default values to be used if not provided by user: 
    arch = x86_64, 
    distro = RHIVOS (latest-RHIVOS-2), 
    User = chatbot, 
    comment = None, 
    duration = 30.
  Possible values for Arch: x86_64, aarch64, s390x, pp64le


## 📝 Guidelines

1.  **Service Name:** Always use service="vm-provisioning" when calling api_get and api_post.
2.  **Create VM:** When asked to create a new VM, use api_post with:
    - service="vm-provisioning"
    - endpoint="/testing-farm/vm-provisioning"
    - body: A dictionary containing the required fields (comment, duration, Arch, Distro, User)
3. **Getting VM Lists:** When asked to get VMs, ALWAYS make EXACTLY ONE api_get call to get all the results (no one than one for one user query) and then perform any filtering operation if needed:
    - service="vm-provisioning"
    - endpoint="/testing-farm/vm-provisioning"
    - if user asks filer based on specific parameters, first get the results from the server with single api_get call and then filter the results to present to the user.
    - The API returns approximately 50 most recent VMs. This is a hard limit - you cannot get more results by making additional calls.
4.  **Filtering by User:** The API does NOT support server-side filtering by User field via query parameters. To filter by user:
    - Make ONE api_get call WITHOUT User in params (just endpoint="/testing-farm/vm-provisioning")
    - Parse the JSON response to find VMs where the "User" field matches the requested username
    - Filter the results in your response processing, not via multiple API calls
    - If asked for "last N VMs for user X", filter by User in the response, then take the last N by creation_time or id
    - First get all the results with a single api_get call, then filter by User in the response.

5.  **Filtering by other fields:** You can try using params for fields like status, arch, or distro, but if filtering doesn't work, fetch all results and filter client-side.
    - First get all the results with a single api_get call, then filter by the other fields in the response.

6.  **Efficiency:** NEVER make multiple api_get calls for the same query. Always make ONE call, get the results, and process them. If you need to filter, do it in your response processing after receiving the data.

7.  **Response Processing:** When you receive VM data:
    - The response is a JSON array of VM objects
    - Each VM has fields: id, arch, status, User, Distro, Duration, creation_time
    - Sort by creation_time or id (descending) to get the most recent first
    - Filter by User field (case-sensitive) if needed
    - Take the first N results after filtering/sorting
8.  **VM Detail:** When asked for details about a specific VM, use api_get with the id field in params to filter results.
"""

SYSTEM_PROMPT = CAPABILITIES


def create_vm_agent(
    debug: bool | None = None,
) -> Any:
    """Create the vm-agent agent.

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


async def run_vm_agent(
    query: str,
    context: dict | None = None,
    run_config: RunnableConfig | None = None,
    debug: bool | None = None,
) -> dict:
    """Run the vm-agent agent.

    Args:
        query: User query to process.
        context: Optional context from previous interactions.
        run_config: Optional runnable configuration.
        debug: Whether to enable debug mode (shows prompts).
            If None, uses the config value (default: False).

    Returns:
        Agent response dictionary.
    """
    agent = create_vm_agent(debug=debug)
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        agent_name="vm_agent",
        context=context,
        config=run_config,
    )


class VmAgent:
    """Agent that implements the SpecialistAgent protocol.

    This class provides the interface that MACSDK expects:
    - name: Unique identifier for the agent
    - capabilities: Description of what the agent can do
    - tools: List of available tools
    - run(): Execute the agent
    - as_tool(): Return the agent as a callable tool
    """

    name: str = "vm_agent"
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
        return await run_vm_agent(query, context, run_config, debug)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool.

        This allows the supervisor to call this agent as a tool,
        enabling dynamic agent orchestration.

        Returns:
            A LangChain tool wrapping this agent.
        """
        agent_instance = self

        @tool
        async def vm_agent(
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

        return vm_agent
