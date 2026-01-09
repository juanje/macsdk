# DevOps Specialist Agent

Example agent demonstrating the use of knowledge tools (skills and facts) with MACSDK.

## Quick Start

1. **Install dependencies**:
```bash
uv sync
```

2. **Set your API key**:
```bash
export GOOGLE_API_KEY="your-key-here"
```

3. **Run the agent**:
```bash
# Show available commands
devops-specialist --help

# List available tools
devops-specialist tools

# Show agent capabilities
devops-specialist info

# Start interactive chat
devops-specialist chat
```

## Features

### Knowledge Tools
This agent uses the MACSDK knowledge system with:
- **Skills**: Task instructions (how to check service health, investigate failures, etc.)
- **Facts**: Contextual information (service catalog, deployment environments, etc.)

The agent automatically discovers and uses these knowledge documents to provide accurate, context-aware responses.

### API Integration
The agent can interact with a DevOps monitoring API (mock) to:
- Check service health status
- Monitor CI/CD pipelines
- Review alerts
- Track deployments

## Example Queries

```
>> lista los servicios disponibles
>> dime el estado del api-gateway
>> ¿hay alguna alerta crítica?
>> ¿cuál es el proceso de respuesta a incidentes?
```

## Configuration

Copy `config.yml.example` to `config.yml` to customize:
- LLM model and temperature
- Recursion limits
- Debug settings

## Skills and Facts

### Skills (src/devops_specialist/skills/)
- `check-service-health.md`: General service health checking
- `check-service-health/api-gateway.md`: API Gateway specific troubleshooting
- `check-service-health/auth-service.md`: Auth service monitoring
- `check-service-health/postgres-primary.md`: Database health checks
- `investigate-pipeline-failures.md`: CI/CD troubleshooting
- `monitor-critical-alerts.md`: Alert management

### Facts (src/devops_specialist/facts/)
- `devops-services-catalog.md`: Complete service catalog with dependencies
- `deployment-environments.md`: Environment configurations
- `company-incident-response-protocol.md`: Incident response procedures

## How It Works

### Architecture Overview

This example demonstrates the clean integration pattern for knowledge tools:

**1. Tools (`tools.py`)** - Single source of truth:
```python
def get_tools() -> list:
    """All tools collected in one place."""
    from macsdk.tools.knowledge import get_knowledge_bundle
    
    _ensure_api_registered()
    knowledge_tools, _ = get_knowledge_bundle(__package__)
    
    return [
        api_get,
        fetch_file,
        calculate,
        *knowledge_tools,  # Automatically includes: list_skills, read_skill, list_facts, read_fact
    ]
```

**2. Agent (`agent.py`)** - Direct middleware setup:
```python
def create_devops_specialist(debug: bool = False) -> Any:
    tools = get_tools()  # All tools in one call
    
    middleware = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]
    
    # Add knowledge middleware directly
    _, knowledge_middleware = get_knowledge_bundle(__package__)
    middleware.extend(knowledge_middleware)
    
    return create_agent(...)
```

**3. Models (`models.py`)** - Extensible responses:
```python
class AgentResponse(BaseAgentResponse):
    """Can be extended with custom fields if needed."""
    pass
```

### Key Features

1. **Zero Duplication**: Knowledge tools setup happens in one place (`get_tools()`)
2. **Lazy Initialization**: Tools and middleware created on-demand
3. **Package-Relative Paths**: Skills/facts discovered via `importlib.resources.files(__package__)`
4. **Auto-Instruction Injection**: `ToolInstructionsMiddleware` detects tools and adds usage instructions
5. **Tools Visibility**: All tools (including knowledge) appear in `devops-specialist tools` command

### What Gets Packaged

When you install this agent as a Python package:
- ✅ Skills markdown files (`src/devops_specialist/skills/*.md`)
- ✅ Facts markdown files (`src/devops_specialist/facts/*.md`)
- ✅ All Python code

The agent can discover and use these resources whether installed system-wide or run in development mode.

## Development

The agent structure:
- `agent.py`: CAPABILITIES (system prompt) + agent creation + middleware
- `tools.py`: Single source of truth for all tools
- `models.py`: Response model (extends BaseAgentResponse)
- `cli.py`: Command-line interface (chat, tools, info commands)
- `skills/`: Task instruction documents (6 DevOps skills)
- `facts/`: Contextual information (3 reference documents)

**Note**: `CAPABILITIES` in `agent.py` is the single source of truth - it's
used both as the system prompt and for supervisor routing. Skills and facts
extend the agent's knowledge without code changes.
