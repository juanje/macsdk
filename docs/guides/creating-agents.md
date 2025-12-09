# Creating Agents

This guide covers how to create specialist agents for MACSDK chatbots.

## Creating an Agent

```bash
macsdk new agent weather-agent --description "Provides weather information"
```

### Project Structure

```
weather-agent/
├── pyproject.toml
├── Containerfile            # Container build instructions
├── src/weather_agent/
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
uv run weather-agent
```

```
╭────────────────────── weather-agent ──────────────────────╮
│                                                           │
│    chat      Start interactive chat                       │
│    tools     List available tools                         │
│    info      Show agent information                       │
│                                                           │
╰───────────────────────────────────────────────────────────╯
```

### Start Interactive Chat

```bash
uv run weather-agent chat
```

### List Tools

```bash
uv run weather-agent tools
```

```
🔧 Available Tools
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool          ┃ Description                               ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ get_weather   │ Get current weather for a city.           │
│ get_forecast  │ Get weather forecast for a city.          │
└───────────────┴───────────────────────────────────────────┘
```

## Implementing Tools

Edit `tools.py`:

```python
from langchain_core.tools import tool

@tool
async def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: Name of the city.
        
    Returns:
        Weather description.
    """
    # Implement your logic here
    return f"Weather in {city}: Sunny, 22°C"

@tool
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.
    
    Args:
        city: Name of the city.
        days: Number of days to forecast.
        
    Returns:
        Weather forecast.
    """
    return f"Forecast for {city}: Sunny for the next {days} days"

# Export tools for CLI inspection
TOOLS = [get_weather, get_forecast]
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
CAPABILITIES = """The weather_agent provides weather information.

Things this agent does:
- Get current weather for any city
- Get weather forecasts
- Answer questions about weather conditions

Use this agent when users ask about weather, temperature, or forecasts."""
```

**Important**: Write detailed capabilities so the supervisor routes queries correctly.

## Customizing the Prompt

Edit `prompts.py`:

```python
SYSTEM_PROMPT = """You are a weather specialist.

When asked about weather, use your tools to get accurate information.
Always include the city name and temperature in your response.
If the user doesn't specify a city, ask them which city they want.

Guidelines:
- Be concise but informative
- Include temperature in both Celsius and Fahrenheit
- Mention any weather warnings if applicable
"""
```

## Response Models

Edit `models.py`:

```python
from macsdk.core import BaseAgentResponse
from pydantic import Field

class WeatherResponse(BaseAgentResponse):
    """Weather agent response model."""
    
    city: str = Field(default="", description="City name")
    temperature: float | None = Field(default=None, description="Temperature in Celsius")
    conditions: str = Field(default="", description="Weather conditions")
```

## The SpecialistAgent Protocol

Every agent must implement the `SpecialistAgent` protocol:

```python
from typing import Annotated
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, tool
from macsdk.core import run_agent_with_tools

class WeatherAgent:
    name: str = "weather_agent"
    capabilities: str = CAPABILITIES
    tools: list = TOOLS

    async def run(
        self,
        query: str,
        context: dict | None = None,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Execute the agent."""
        return await run_weather_agent(query, context, config)

    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for the supervisor."""
        agent_instance = self

        @tool
        async def invoke_weather_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Get weather information.
            
            Use this when the user asks about weather, temperature,
            or forecasts for any location.
            """
            result = await agent_instance.run(query, config=config)
            return result["response"]

        return invoke_weather_agent
```

## Testing Your Agent

### Interactive Testing

```bash
uv run weather-agent chat
```

```
╭─────────────────── weather-agent Chat ───────────────────╮
│ Type exit or press Ctrl+C to quit                        │
╰──────────────────────────────────────────────────────────╯

>> What's the weather in Tokyo?
[weather_agent] Processing query...
[weather_agent] 🔧 Using tool: get_weather

╭─────────────────────── Response ───────────────────────╮
│ Weather in Tokyo: Sunny, 22°C                          │
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
macsdk add-agent . --path ../weather-agent

# Or publish to PyPI and install
macsdk add-agent . --package weather-agent
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
