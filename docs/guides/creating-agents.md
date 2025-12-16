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
│   ├── models.py            # Response models
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

Edit `models.py`:

```python
from macsdk.core import BaseAgentResponse
from pydantic import Field

class InfraResponse(BaseAgentResponse):
    """Infrastructure agent response model."""
    
    service: str = Field(default="", description="Service name")
    status: str = Field(default="", description="Service status")
```

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
        async def invoke_infra_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Monitor infrastructure services."""
            result = await agent_instance.run(query, config=config)
            return result["response"]

        return invoke_infra_agent
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
            ├── tools.py
            ├── prompts.py
            └── models.py
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
