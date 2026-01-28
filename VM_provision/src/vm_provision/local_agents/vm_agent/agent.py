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
  Possible values for arch: x86_64, aarch64, s390x, pp64le
  Possible values for distro/compose: RHIVOS, RHIVOS (latest-RHIVOS-2), RHEL-10.2-Nightly, CentOS-Stream-10, RHIVOS (latest-RHIVOS-2-Core), RHIVOS (RHIVOS-1.0.0-RC3), RHIVOS (latest-RHIVOS-1)
  Possible values for xstream: RHIVOS-1, RHIVOS-2, AutoSD-10, AutoSD-9, RHIVOS-1-ER5-rc2
  Possible values for image: nightly, qa, latest-RHIVOS-1, latest-RHIVOS-2
  Possible values for image_name: qa, fusa-minimal, minimal, developer
  Possible values for image_type: regular, ostree, debug (or combinations like "qa - regular - debug")

- POST /testing-farm/vm-provisioning
  Description: Creates a new VM in the Test Console environment.
  The request payload (body) MUST contain the following REQUIRED fields: arch, distro, username, reservation_time, immediate_execution.
  **CRITICAL: When creating a VM, you MUST ALWAYS include ALL required fields in the body.**
  
  Default values to use if not provided by user: 
    arch = "x86_64", 
    distro = "RHIVOS (latest-RHIVOS-2)", 
    username = "VM_provision_chatbot", 
    reservation_time = 30,
    immediate_execution = 1,
    comment = "" (empty string, or omit the field), 
    debug_kernel = 0
  
  **FIELD NAMES AND POSSIBLE VALUES:**
  
  **Required Fields (lowercase field names):**
  - arch: Architecture. Possible values: "x86_64", "aarch64", "s390x", "pp64le"
  - distro: Distribution/compose. Possible values: "RHIVOS", "RHIVOS (latest-RHIVOS-2)", "RHEL-10.2-Nightly", "CentOS-Stream-10", "RHIVOS (latest-RHIVOS-2-Core)", "RHIVOS (RHIVOS-1.0.0-RC3)", "RHIVOS (latest-RHIVOS-1)"
  - username: Username for the VM owner. Example: "VM_provision_chatbot", "yarboa", "akkohli"
  - reservation_time: Duration in minutes (number). Example: 30, 60, 120, 1000
  - immediate_execution: Whether to execute immediately (number: 1 = yes, 0 = no). Use 1 for immediate execution.
  
  **Optional Fields:**
  - xstream: OS stream/version. Possible values: "RHIVOS-1", "RHIVOS-2", "AutoSD-10", "AutoSD-9", "RHIVOS-1-ER5-rc2"
  - image: Image type. Possible values: "nightly", "qa", "latest-RHIVOS-1", "latest-RHIVOS-2"
  - image_name: Image name/variant. Possible values: "qa", "fusa-minimal", "minimal", "developer"
  - image_type: Image format type. Possible values: "regular", "ostree", "debug" (or combinations like "qa - regular - debug")
  - compose: Distribution compose (often same as distro). Possible values: "RHIVOS", "RHEL-10.2-Nightly"
  - comment: Description/comment for the VM (string). Can be empty string "" or omitted.
  - debug_kernel: Whether to use debug kernel (number: 0 = no, 1 = yes). Default: 0
  - disk_space: Disk space with unit (string). Example: "100 Gb", "50 Gb"
  - memory: Memory size with unit (string). Example: "4 Gb", "8 Gb"
  - ssh_key: SSH public key (string). Example: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."
  - starting_at_date: Scheduled start date (string). Empty string "" if not scheduled.
  - starting_at_time: Scheduled start time (string). Empty string "" if not scheduled.
  - starting_at_timezone: Scheduled timezone (string). Empty string "" if not scheduled.
  - hw_requirements: Hardware requirements object. Example: {"virtualization.is-supported": "false", "cpu.processors": ">= 4", "cpu.cores": ">= 8"}
  
  **TYPICAL BODY STRUCTURE (example with all common fields):**
  {
    "arch": "x86_64",
    "distro": "RHIVOS",
    "username": "VM_provision_chatbot",
    "reservation_time": 120,
    "immediate_execution": 1,
    "xstream": "RHIVOS-1",
    "image": "nightly",
    "image_name": "qa",
    "image_type": "regular",
    "comment": "Testing VM provisioning",
    "debug_kernel": 0,
    "disk_space": "100 Gb",
    "memory": "4 Gb",
    "ssh_key": "",
    "starting_at_date": "",
    "starting_at_time": "",
    "starting_at_timezone": "",
    "hw_requirements": {
      "virtualization.is-supported": "false",
      "cpu.processors": ">= 4",
      "cpu.cores": ">= 8"
    }
  }
  
  **MINIMUM REQUIRED BODY (for basic VM creation):**
  {
    "arch": "x86_64",
    "distro": "RHIVOS (latest-RHIVOS-2)",
    "username": "VM_provision_chatbot",
    "reservation_time": 30,
    "immediate_execution": 1,
    "debug_kernel": 0,
    "comment": "",
    "starting_at_date": "",
    "starting_at_time": "",
    "starting_at_timezone": "",
    "xstream": "",
    "image": "",
    "image_name": "",
    "image_type": "",
    "disk_space": "",
    "memory": "",
    "ssh_key": ""
  }
  
  **CRITICAL FIELD NAME REQUIREMENTS:**
  - Use "Arch" (capital A), NOT "arch"
  - Use "Distro" (capital D), NOT "distro"  
  - Use "User" (capital U), NOT "user" or "username"
  - Use "duration" (lowercase), NOT "reservation_time" or "Duration"
  - Field names are case-sensitive - the API requires exact capitalization


## 📝 Guidelines

**CRITICAL RULE: When creating a VM, make EXACTLY ONE api_post call. Never make multiple calls for a single VM creation request.**

1.  **Service Name:** Always use service="vm-provisioning" when calling api_get and api_post.
2.  **Create VM:** When asked to create a new VM, use api_post with:
    - **CRITICAL: Make EXACTLY ONE api_post call. NEVER make multiple calls to create a single VM.**
    - service="vm-provisioning"
    - endpoint="/testing-farm/vm-provisioning"
    - body: A dictionary containing ALL required fields (arch, distro, username, reservation_time, immediate_execution)
    - **CRITICAL:** You MUST construct the body dictionary with actual values. DO NOT pass an empty dictionary {}.
    - **MANDATORY:** You MUST ALWAYS include all required fields in the body. NEVER send an empty body {}.
    - **MANDATORY:** When creating a VM, call api_post ONCE and ONLY ONCE. Do not make multiple parallel or sequential calls.
    - **When calling api_post, you MUST write out the complete body dictionary like this:**
      api_post(
        service="vm-provisioning",
        endpoint="/testing-farm/vm-provisioning",
        body={
          "arch": "x86_64",
          "distro": "RHIVOS (latest-RHIVOS-2)",
          "username": "VM_provision_chatbot",
          "reservation_time": 30,
          "immediate_execution": 1,
          "debug_kernel": 0,
          "comment": "",
          "starting_at_date": "",
          "starting_at_time": "",
          "starting_at_timezone": "",
          "xstream": "",
          "image": "",
          "image_name": "",
          "image_type": "",
          "disk_space": "",
          "memory": "",
          "ssh_key": ""
        }
      )
    - **Minimum body structure (use these defaults if user doesn't specify):**
      {
        "arch": "x86_64",
        "distro": "RHIVOS (latest-RHIVOS-2)",
        "username": "VM_provision_chatbot",
        "reservation_time": 30,
        "immediate_execution": 1,
        "debug_kernel": 0,
        "comment": "",
        "starting_at_date": "",
        "starting_at_time": "",
        "starting_at_timezone": "",
        "xstream": "",
        "image": "",
        "image_name": "",
        "image_type": "",
        "disk_space": "",
        "memory": "",
        "ssh_key": ""
      }
    - Optional fields you can include if specified: xstream, image, image_name, image_type, disk_space, memory, ssh_key, comment, hw_requirements, starting_at_date, starting_at_time, starting_at_timezone
    - **IMPORTANT:** ALL field names are LOWERCASE (arch, distro, username, NOT Arch, Distro, User)
    - **IMPORTANT:** Use numbers (1, 0) for immediate_execution and debug_kernel, NOT booleans (True, False)
    - **IMPORTANT:** Use empty strings "" for optional string fields, NOT null or None
    - **IMPORTANT:** The body parameter must be a complete dictionary with all fields - do not pass {} and expect it to be filled automatically
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
