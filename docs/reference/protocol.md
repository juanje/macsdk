# SpecialistAgent Protocol Reference

The `SpecialistAgent` protocol defines the interface that all specialist agents must implement.

## Protocol Definition

```python
from typing import Protocol, runtime_checkable
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

@runtime_checkable
class SpecialistAgent(Protocol):
    """Protocol that all specialist agents must implement."""
    
    name: str
    capabilities: str
    
    async def run(
        self,
        query: str,
        context: dict | None = None,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Execute the agent with a user query."""
        ...
    
    def as_tool(self) -> BaseTool:
        """Return the agent wrapped as a LangChain tool."""
        ...
```

## Required Attributes

### `name: str`

Unique identifier for the agent. Used by the registry and for logging.

```python
name = "weather_agent"
```

### `capabilities: str`

Human-readable description of what the agent can do. The supervisor uses this to decide which agent to route queries to.

```python
capabilities = """The weather_agent provides weather information.

Things this agent does:
- Get current weather for any city
- Get weather forecasts
- Answer questions about weather conditions

Use this agent when users ask about weather, temperature, or forecasts."""
```

**Tip**: Write detailed capabilities for better routing accuracy.

## Required Methods

### `async def run(query, context=None, config=None) -> dict`

Execute the agent with a user query.

**Parameters:**
- `query: str` - The user's query
- `context: dict | None` - Optional context dictionary
- `config: RunnableConfig | None` - Optional config for streaming support

**Returns:**
A dictionary containing at minimum:
- `response: str` - The agent's response text
- `agent_name: str` - Name of the agent
- `tools_used: list[str]` - List of tools called

**Example:**
```python
async def run(
    self,
    query: str,
    context: dict | None = None,
    config: RunnableConfig | None = None,
) -> dict:
    return await run_my_agent(query, context, config)
```

### `def as_tool() -> BaseTool`

Return the agent wrapped as a LangChain tool for use by the supervisor.

**Returns:**
A `BaseTool` instance that invokes the agent.

**Example:**
```python
def as_tool(self) -> BaseTool:
    agent_instance = self

    @tool
    async def invoke_my_agent(
        query: str,
        config: Annotated[RunnableConfig, InjectedToolArg],
    ) -> str:
        """Invoke my agent.
        
        Use this when the user asks about X.
        """
        result = await agent_instance.run(query, config=config)
        return result["response"]

    return invoke_my_agent
```

**Important**: The tool docstring is used by the supervisor to decide when to call this agent.

## Complete Implementation Example

```python
from typing import Annotated
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg, tool
from macsdk.core import get_answer_model, run_agent_with_tools

from .prompts import SYSTEM_PROMPT
from .tools import TOOLS

CAPABILITIES = """My agent does X, Y, and Z.

Things this agent handles:
- Task A
- Task B
- Task C

Use this agent when users ask about X, Y, or Z."""


def create_my_agent():
    """Create the agent with tools."""
    return create_agent(
        model=get_answer_model(),
        tools=TOOLS,
        middleware=[],
    )


async def run_my_agent(
    query: str,
    context: dict | None = None,
    config: RunnableConfig | None = None,
) -> dict:
    """Run the agent."""
    agent = create_my_agent()
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        system_prompt=SYSTEM_PROMPT,
        agent_name="my_agent",
        context=context,
        config=config,
    )


class MyAgent:
    """My specialist agent."""
    
    name: str = "my_agent"
    capabilities: str = CAPABILITIES
    tools: list = TOOLS  # For CLI inspection

    async def run(
        self,
        query: str,
        context: dict | None = None,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Execute the agent."""
        return await run_my_agent(query, context, config)

    def as_tool(self) -> BaseTool:
        """Return this agent as a tool."""
        agent_instance = self

        @tool
        async def invoke_my_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Invoke my agent for X, Y, Z queries.
            
            Use this when users ask about:
            - Task A
            - Task B
            - Task C
            """
            result = await agent_instance.run(query, config=config)
            return result["response"]

        return invoke_my_agent
```

## Type Checking

The protocol is `@runtime_checkable`, so you can use `isinstance`:

```python
from macsdk.core import SpecialistAgent

agent = MyAgent()
assert isinstance(agent, SpecialistAgent)  # True
```

## Registration

Once implemented, register your agent:

```python
from macsdk.core import register_agent

agent = MyAgent()
register_agent(agent)
```

Or in your chatbot's `agents.py`:

```python
from macsdk.core import get_registry, register_agent
from my_agent import MyAgent

def register_all_agents() -> None:
    registry = get_registry()
    if not registry.is_registered("my_agent"):
        register_agent(MyAgent())
```

## Progress Logging

For long operations, use `log_progress` to show status:

```python
from macsdk.core.utils import log_progress

async def my_long_operation(config: RunnableConfig | None = None):
    log_progress("[my_agent] Starting operation...\n", config)
    # ... do work ...
    log_progress("[my_agent] Operation complete!\n", config)
```

This shows progress in both CLI and web interfaces.
