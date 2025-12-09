# Creating Agents

This guide covers how to create specialist agents for MACSDK chatbots.

## Creating an Agent

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
│   ├── prompts.py           # System prompts
│   ├── tools.py             # Agent tools
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
🔧 Available Tools
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool               ┃ Description                                   ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ get_service_status │ Get the status of a service.                  │
│ search_logs        │ Search application logs for matching entries. │
└────────────────────┴───────────────────────────────────────────────┘
```

## Implementing Tools

Edit `tools.py` to customize the generated example tools:

```python
from langchain_core.tools import tool

@tool
async def get_service_status(service_name: str) -> str:
    """Get the status of a service.
    
    Args:
        service_name: Name of the service to check.
        
    Returns:
        Service status information.
    """
    # Replace with real monitoring API calls
    return f"Service {service_name}: Running (healthy)"

@tool
async def search_logs(query: str, service: str = "all") -> str:
    """Search application logs for matching entries.
    
    Args:
        query: Search query string.
        service: Service name to filter logs (default: all).
        
    Returns:
        Matching log entries.
    """
    # Replace with real log search implementation
    return f"Found 3 log entries matching '{query}' in {service}"

# Export tools for CLI inspection
TOOLS = [get_service_status, search_logs]
```

## Using MACSDK API Tools

For agents that interact with REST APIs, use MACSDK's built-in tools.

### Basic API Service

```python
import os
from langchain_core.tools import tool
from macsdk.core.api_registry import register_api_service
from macsdk.tools import api_get, api_post

# Register the API service once
register_api_service(
    name="my_api",
    base_url="https://api.example.com",
    timeout=10,
    max_retries=2,
)

@tool
async def get_users() -> str:
    """Get all users from the API."""
    return await api_get.ainvoke({
        "service": "my_api",
        "endpoint": "/users",
    })

@tool
async def get_user_names() -> str:
    """Get just the names of all users."""
    return await api_get.ainvoke({
        "service": "my_api",
        "endpoint": "/users",
        "extract": "$[*].name",  # JSONPath extraction
    })
```

### API with Authentication

```python
# Service with Bearer token
register_api_service(
    name="github",
    base_url="https://api.github.com",
    token=os.environ["GITHUB_TOKEN"],  # Adds Authorization: Bearer header
    rate_limit=5000,
)

@tool
async def get_repo_info(owner: str, repo: str) -> str:
    """Get information about a GitHub repository."""
    return await api_get.ainvoke({
        "service": "github",
        "endpoint": f"/repos/{owner}/{repo}",
        "extract": "$.full_name",
    })
```

### API with Custom SSL Certificate

For internal APIs with self-signed or custom certificates:

```python
# Service with custom SSL certificate
register_api_service(
    name="internal_api",
    base_url="https://api.internal.company.com",
    token=os.environ["INTERNAL_TOKEN"],
    ssl_cert="/path/to/company-ca.pem",
)
```

### Test Server (No SSL Verification)

For development/test servers only:

```python
# ⚠️ INSECURE - Only for development!
register_api_service(
    name="test_api",
    base_url="https://localhost:8443",
    ssl_verify=False,
)
```

### Service Options Reference

| Option | Description |
|--------|-------------|
| `token` | Bearer token for authentication |
| `headers` | Custom HTTP headers dict |
| `timeout` | Request timeout in seconds (default: 30) |
| `max_retries` | Retry attempts (default: 3) |
| `rate_limit` | Requests per hour limit |
| `ssl_cert` | Path to SSL certificate file |
| `ssl_verify` | Verify SSL (default: True) |

See `macsdk list-tools` for all available API tools.

## Defining Capabilities

Edit `agent.py`:

```python
CAPABILITIES = """The infra_agent monitors infrastructure services.

Things this agent does:
- Check service health and status
- Search application logs
- Monitor infrastructure components

Use this agent when users ask about service status, logs, or infrastructure."""
```

**Important**: Write detailed capabilities so the supervisor routes queries correctly.

## Customizing the Prompt

Edit `prompts.py`:

```python
SYSTEM_PROMPT = """You are an infrastructure monitoring specialist.

When asked about services or logs, use your tools to get accurate information.
Always include the service name and status in your response.
If the user doesn't specify a service, ask them which one they want.

Guidelines:
- Be concise but informative
- Include timestamps when showing log entries
- Highlight any errors or warnings
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
    details: str = Field(default="", description="Additional details")
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
    tools: list = TOOLS

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
            """Monitor infrastructure services.
            
            Use this when the user asks about service status,
            logs, or infrastructure health.
            """
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

>> Is the database service running?
[infra_agent] Processing query...
[infra_agent] 🔧 Using tool: get_service_status

╭─────────────────────── Response ───────────────────────╮
│ Service database: Running (healthy)                    │
╰────────────────────────────────────────────────────────╯
```

### Run Tests

```bash
uv run pytest
```

## Adding to a Chatbot

```bash
# From local path (inside chatbot directory)
cd my-chatbot
macsdk add-agent . --path ../infra-agent

# Or publish to PyPI and install
macsdk add-agent . --package infra-agent
```

## Best Practices

1. **Clear capabilities**: Write detailed CAPABILITIES so the supervisor routes correctly
2. **Helpful tool docstrings**: The LLM uses docstrings to decide when to use tools
3. **Handle errors gracefully**: Return helpful error messages
4. **Test thoroughly**: Write tests for all tools
5. **Use streaming**: Call `log_progress` for long operations to show progress
6. **Export TOOLS**: Always export a `TOOLS` list for CLI inspection

## Advanced: Using Subgraphs

For agents that need multi-step processing, you can use LangGraph:

```python
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: list
    current_step: str
    intermediate_results: dict

def create_complex_agent():
    graph = StateGraph(AgentState)
    
    # Add nodes for each processing step
    graph.add_node("analyze", analyze_node)
    graph.add_node("gather_data", gather_data_node)
    graph.add_node("synthesize", synthesize_node)
    
    # Add edges (workflow)
    graph.add_edge("analyze", "gather_data")
    graph.add_edge("gather_data", "synthesize")
    graph.add_edge("synthesize", END)
    
    graph.set_entry_point("analyze")
    return graph.compile()
```

See the [LangGraph documentation](https://langchain-ai.github.io/langgraph/) for more details.

## Container Deployment

Each generated agent includes a `Containerfile` for building container images.

### Build the Container

```bash
cd my-agent
podman build -t my-agent .
# Or with Docker
docker build -t my-agent -f Containerfile .
```

### Run the Container

```bash
# Interactive chat
podman run --rm -it -e GOOGLE_API_KEY=$GOOGLE_API_KEY my-agent chat

# Show help
podman run --rm my-agent --help
```

### Container Features

- **Multi-stage build**: Keeps final image small
- **UBI base image**: Red Hat Universal Base Image for enterprise use
- **Pre-built wheel**: Fast container startup
- **Configurable**: Override CMD for different commands
