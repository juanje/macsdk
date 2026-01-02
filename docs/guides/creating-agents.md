# Creating Agents

This guide covers how to create specialist agents for MACSDK chatbots.

## Project Approaches

MACSDK supports two approaches for organizing agents:

| Approach | Use Case | Command |
|----------|----------|---------|
| **Multi-repo** | Reusable agents, separate versioning | `macsdk new agent` |
| **Mono-repo** | Project-specific agents, simpler setup | `macsdk add-agent --new` |

## Creating a Standalone Agent (Multi-repo)

Best for agents you want to reuse across multiple chatbots:

```bash
macsdk new agent infra-agent --description "Monitors infrastructure services"
```

### Project Structure

```
infra-agent/
├── pyproject.toml
├── Containerfile            # Container build instructions
├── src/infra_agent/
│   ├── __init__.py          # Exports agent class
│   ├── agent.py             # Main agent implementation
│   ├── config.py            # Agent configuration (extends MACSDKConfig)
│   ├── models.py            # Response models (uses BaseAgentResponse by default)
│   ├── prompts.py           # System prompts with API schema
│   ├── tools.py             # Tool configuration
│   └── cli.py               # Testing CLI (Rich-powered)
├── config.yml.example
├── .env.example
├── .gitignore
└── README.md
```

## Running Your Agent

### Show Available Commands

```bash
uv run infra-agent
```

```
╭────────────────────── infra-agent ──────────────────────╮
│                                                          │
│    chat      Start interactive chat                      │
│    tools     List available tools                        │
│    info      Show agent information                      │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

### Start Interactive Chat

```bash
uv run infra-agent chat
```

### List Tools

```bash
uv run infra-agent tools
```

```
🔧 Available Tools (Generic SDK)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool       ┃ Description                                      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_get    │ Make a GET request to a registered API service.  │
│ fetch_file │ Fetch a file from a URL with optional filtering. │
└────────────┴──────────────────────────────────────────────────┘
```

## Using API Tools

MACSDK uses a minimalist approach: **few generic tools** instead of many specific tools. The LLM decides which endpoints to call based on the API description in the prompt.

### The recommended pattern

**1. Register the service** (in `tools.py`):

```python
from macsdk.core.api_registry import register_api_service
from macsdk.tools import api_get, fetch_file

register_api_service(
    name="devops",
    base_url="https://api.example.com",
)

def get_tools():
    return [api_get, fetch_file]  # Only 2 generic tools
```

**2. Describe the API in the prompt** (in `prompts.py`):

```python
SYSTEM_PROMPT = """You are a DevOps assistant.

## API Service: "devops"

Available endpoints:
- GET /services - List all services
- GET /services/{id} - Service details
- GET /alerts - List alerts
- GET /alerts with params {"severity": "critical"} - Filter by severity

Always use service="devops" when calling api_get.
"""
```

**3. The LLM does the rest**: When the user asks "Are there any critical alerts?", the LLM automatically chooses the right endpoint.

### Why this approach?

| Traditional | MACSDK |
|-------------|--------|
| 20 tools for 20 endpoints | 2 generic tools |
| Lots of repetitive code | Simple code |
| Hard to maintain | Adding endpoints = updating prompt |
| LLM chooses between many options | LLM reads API description |

### Custom tools (when you need them)

Only create specific tools when you need:
- **JSONPath extraction**: Extract specific fields to reduce tokens
- **Business logic**: Combine calls or transform data

```python
from macsdk.tools import make_api_request

@tool
async def get_service_health_summary() -> str:
    """Quick summary of service health status."""
    result = await make_api_request(
        "GET", "devops", "/services",
        extract="$[*].name",  # JSONPath to extract only names
    )
    # ... formatting logic ...
```

📖 **See [API Tools Reference](../reference/tools.md)** for complete documentation

## Defining Capabilities

Edit `agent.py`:

```python
CAPABILITIES = """DevOps monitoring assistant.

This agent can:
- Check infrastructure service health
- Monitor CI/CD pipelines and jobs
- Review alerts (critical, warnings)
- Track deployments

Use this agent when users ask about infrastructure, pipelines, or alerts."""
```

**Important**: Write detailed capabilities so the supervisor routes queries correctly.

## Customizing the Prompt

Edit `prompts.py` to describe your API:

```python
SYSTEM_PROMPT = """You are a DevOps monitoring assistant.

## API Service: "myapi"

Available endpoints:
- GET /services - List all services
- GET /services/{id} - Get specific service
- GET /pipelines - List pipelines
- GET /pipelines with params {"status": "failed"} - Filter by status
- GET /alerts - List alerts

## Guidelines
1. Always use service="myapi" when calling api_get
2. For alerts, prioritize critical ones
3. Be concise in responses
"""
```

## Response Models

By default, agents use `BaseAgentResponse` from the SDK, which provides:
- `response_text`: Human-readable response
- `tools_used`: List of tools that were called

This is sufficient for most agents since the supervisor receives `response_text` via the tool wrapper.
For most cases, you won't need to modify this file.

For advanced use cases (like inter-agent data coordination), you can extend the base model in `models.py`:

```python
from macsdk.core import BaseAgentResponse
from pydantic import Field

class AgentResponse(BaseAgentResponse):
    """Custom response model with additional structured data."""
    
    service_name: str | None = Field(default=None, description="Service name")
    status: str | None = Field(default=None, description="Service status")
    error_summary: str | None = Field(default=None, description="Error details")
```

**Note:** Custom fields are available in the result dict (`result["service_name"]`) but are not automatically passed to the supervisor. The default approach of putting all relevant information in `response_text` is simpler and works well for most cases.

## The SpecialistAgent Protocol

Every agent must implement the `SpecialistAgent` protocol:

```python
from typing import Annotated
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, tool
from macsdk.core import run_agent_with_tools

class InfraAgent:
    name: str = "infra_agent"
    capabilities: str = CAPABILITIES
    tools: list = []

    def __init__(self):
        self.tools = get_tools()

    async def run(
        self,
        query: str,
        context: dict | None = None,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Execute the agent."""
        return await run_infra_agent(query, context, config)

    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for the supervisor."""
        agent_instance = self

        @tool
        async def infra_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Query this specialist agent with a natural language request."""
            result = await agent_instance.run(query, config=config)
            return result["response"]

        return infra_agent
```

## Testing Your Agent

### Interactive Testing

```bash
uv run infra-agent chat
```

```
╭─────────────────── infra-agent Chat ────────────────────╮
│ Type exit or press Ctrl+C to quit                       │
╰─────────────────────────────────────────────────────────╯

>> Is the authentication service running?
[infra_agent] Processing query...
[infra_agent] 🔧 Using tool: api_get
[infra_agent] Tools used: api_get

╭─────────────────────── Response ───────────────────────╮
│ Service auth-service: Running (healthy)                │
╰────────────────────────────────────────────────────────╯
```

### Run Tests

```bash
uv run pytest
```

## Adding to a Chatbot

### Remote Agents (Multi-repo)

```bash
# From local path (inside chatbot directory)
cd my-chatbot
macsdk add-agent . --path ../infra-agent

# Or publish to PyPI and install
macsdk add-agent . --package infra-agent
```

### Local Agents (Mono-repo)

Create an agent inside your chatbot project:

```bash
cd my-chatbot
macsdk add-agent . --new weather --description "Weather information service"
```

This creates:
```
my-chatbot/
└── src/my_chatbot/
    └── local_agents/
        └── weather/
            ├── __init__.py
            ├── agent.py
            ├── config.py
            ├── models.py
            ├── prompts.py
            └── tools.py
```

The agent is automatically registered in `agents.py` with relative imports:

```python
from .local_agents.weather import WeatherAgent

def register_all_agents():
    if not registry.is_registered("weather"):
        register_agent(WeatherAgent())
```

**When to use local agents:**
- Agent is specific to one chatbot
- Simpler dependency management
- Faster iteration during development

## Best Practices

1. **Use generic tools**: Start with `api_get` + `fetch_file`, add custom tools only when needed
2. **Describe API in prompt**: Let the LLM decide which endpoints to call
3. **Clear capabilities**: Write detailed CAPABILITIES for correct routing
4. **Helpful tool docstrings**: The LLM uses docstrings to decide when to use tools
5. **Handle errors gracefully**: Return helpful error messages
6. **Use streaming**: Call `log_progress` for long operations

## Task Planning with TodoListMiddleware

For complex multi-step queries that require coordination between multiple agents, you can enable task planning middleware:

### Configuration

**Important:** The global `enable_todo` setting applies **only to the supervisor**, not to specialist agents.

**Supervisor (enabled by default):**

```yaml
# Task Planning for supervisor (coordinates multiple agents)
enable_todo: true  # Default: true
```

**Agent-specific setting (disabled by default):**

Agents don't inherit the global setting. Enable explicitly for agents that need it:

```yaml
# Supervisor uses global setting
enable_todo: true

# Enable for specific agents that need task planning
diagnostic_agent:
  enable_todo: true   # Complex multi-step diagnostics

investigation_agent:
  enable_todo: true   # Deep investigations

# Simple agents don't need it (default: false)
# api_lookup_agent: no config needed, uses default (false)
```

**Priority order for specialist agents:**
1. Parameter passed to agent's `run()` method
2. Agent-specific config (`api_agent.enable_todo`)
3. Default value (`False` for agents)

**Priority order for supervisor:**
1. Parameter passed to `create_supervisor_agent()`
2. Global config (`enable_todo`)
3. Default value (`True` for supervisor)

### How It Works

When enabled, the TodoListMiddleware equips agents with an internal to-do list for tracking complex investigations:

- **Breaks down complex queries** into manageable steps
- **Tracks progress** as the agent gathers information
- **Ensures completeness** by reviewing remaining tasks before responding

### When to Use

Enable task planning for agents that handle:
- Multi-step investigations ("Why did the deployment fail?")
- Queries requiring multiple tool calls with dependencies
- Complex diagnostic workflows

### Example

User asks: "Why did the deployment fail?"

With task planning enabled:
1. Agent creates internal plan: Check deployments → Get pipeline details → Fetch logs
2. Tracks progress through each step
3. Ensures all investigation paths are followed
4. Returns complete answer with root cause

### Task Planning Prompts

Specialist agents use `TODO_PLANNING_SPECIALIST_PROMPT`, which includes examples tailored for tool-based workflows:

```python
# The SDK automatically imports this in generated agents
from macsdk.agents.supervisor import TODO_PLANNING_SPECIALIST_PROMPT
```

This prompt differs from `TODO_PLANNING_SUPERVISOR_PROMPT` (used by supervisors) because:
- **Specialist prompts**: Show examples using tools (`get_deployment_details()`, `fetch_logs()`)
- **Supervisor prompts**: Show examples coordinating agents (`call deployment_agent`, `call pipeline_agent`)

#### Customizing for Your Domain

You can override the default in your agent's `prompts.py`:

```python
from macsdk.agents.supervisor import TODO_PLANNING_COMMON

# Build on the common base with domain-specific examples
TODO_PLANNING_SPECIALIST_PROMPT = (
    TODO_PLANNING_COMMON + """
**Example Investigation Flow for Your Domain:**
1. Call get_domain_specific_data()
2. Call analyze_results(data)
3. Call get_recommendations()
... your custom examples ...
"""
)
```

**Note:** For backward compatibility, you can also import from `macsdk.prompts`:
```python
from macsdk.prompts import TODO_PLANNING_SPECIALIST_PROMPT  # Still works
```

The SDK automatically injects this prompt when `enable_todo=True`.

## Advanced: Using Subgraphs

For agents that need multi-step processing, you can use LangGraph:

```python
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: list
    current_step: str

def create_complex_agent():
    graph = StateGraph(AgentState)
    graph.add_node("analyze", analyze_node)
    graph.add_node("gather_data", gather_data_node)
    graph.add_node("synthesize", synthesize_node)
    
    graph.add_edge("analyze", "gather_data")
    graph.add_edge("gather_data", "synthesize")
    graph.add_edge("synthesize", END)
    
    graph.set_entry_point("analyze")
    return graph.compile()
```

## Container Deployment

Each generated agent includes a `Containerfile` for building container images.

### Build the Container

```bash
cd my-agent
podman build -t my-agent .
```

### Run the Container

```bash
podman run --rm -it -e GOOGLE_API_KEY=$GOOGLE_API_KEY my-agent chat
```
