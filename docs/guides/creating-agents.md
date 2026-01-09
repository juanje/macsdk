# Creating Agents

This guide covers how to create specialist agents for MACSDK chatbots.

## Philosophy: Simple, Specialized Agents

MACSDK agents follow a **single-responsibility principle**:

- **One definition**: `CAPABILITIES` defines what the agent does
- **Minimal configuration**: Agents work out of the box
- **Extension without code changes**: Use tools, skills, and facts

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ARCHITECTURE                       │
│                                                             │
│   CAPABILITIES  ─────►  System prompt (what I do)           │
│        │                        +                           │
│        │                 Planning guidance (CoT)            │
│        │                        +                           │
│        │                 Tools (what I can execute)         │
│        │                                                    │
│        └────────►  Supervisor routing (when to use me)      │
│                                                             │
│   Extension (no code changes):                              │
│   • Tools   → New actions                                   │
│   • Skills  → How to do complex tasks                       │
│   • Facts   → Domain context and reference data             │
└─────────────────────────────────────────────────────────────┘
```

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
│   ├── agent.py             # CAPABILITIES + agent implementation
│   ├── config.py            # Agent configuration
│   ├── models.py            # Response models
│   ├── tools.py             # Tool configuration
│   └── cli.py               # Testing CLI (Rich-powered)
├── config.yml.example
├── .env.example
├── .gitignore
└── README.md
```

## Defining Your Agent

The `CAPABILITIES` constant in `agent.py` is the **single source of truth**:

```python
CAPABILITIES = """DevOps monitoring assistant.

This agent can:
- Check infrastructure service health and status
- Monitor CI/CD pipelines and their jobs
- Review alerts (critical, warnings, unacknowledged)
- Track deployments across environments

Use this agent for infrastructure monitoring and DevOps queries."""

# CAPABILITIES is the system prompt
SYSTEM_PROMPT = CAPABILITIES
```

### Why This Matters

| Use | Purpose |
|-----|---------|
| **Supervisor routing** | Decides when to delegate to this agent |
| **System prompt** | Base instructions for the LLM |
| **Self-documentation** | Clear description of agent purpose |

### Writing Good CAPABILITIES

**Be specific and bounded:**

```python
# ✅ Good - Clear, specific, bounded
CAPABILITIES = """Database monitoring specialist.

This agent can:
- Check PostgreSQL connection status
- Monitor query performance metrics
- Review slow query logs
- Analyze table sizes and indexes

Limitations:
- Does NOT execute DDL commands
- Does NOT access production data directly"""

# ❌ Bad - Vague, unbounded
CAPABILITIES = """General database assistant that helps with databases."""
```

!!! tip "Keep CAPABILITIES Concise"
    Remember that `CAPABILITIES` is injected into the **supervisor's prompt** for routing.
    If you have many agents with very detailed CAPABILITIES, consider moving extensive
    documentation (API schemas, detailed instructions) to **Facts** or **Skills** instead.

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

## Using API Tools

MACSDK uses a minimalist approach: **few generic tools** instead of many specific tools. The LLM decides which endpoints to call based on the API description.

### The Recommended Pattern

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

**2. Describe the API in CAPABILITIES** (in `agent.py`):

```python
CAPABILITIES = """DevOps assistant monitoring infrastructure.

This agent can check service health, monitor alerts, and track deployments

## API Service: "devops"

Available endpoints:
- GET /services - List all services
- GET /services/{id} - Service details
- GET /alerts - List alerts
- GET /alerts with params {"severity": "critical"} - Filter by severity

Always use service="devops" when calling api_get."""

SYSTEM_PROMPT = CAPABILITIES
```

**3. The LLM does the rest**: When the user asks "Are there any critical alerts?", the LLM automatically chooses the right endpoint.

### Why This Approach?

| Traditional | MACSDK |
|-------------|--------|
| 20 tools for 20 endpoints | 2 generic tools |
| Lots of repetitive code | Simple code |
| Hard to maintain | Adding endpoints = updating CAPABILITIES |
| LLM chooses between many options | LLM reads API description |

### Using Skills for Complex APIs

For detailed API documentation, use **facts** instead of putting everything in CAPABILITIES:

```markdown
<!-- facts/api-reference.md -->
---
name: api-reference
description: Complete DevOps API reference
---

## Services API

### GET /services
Returns all services with their status.

Response fields:
- id: Service identifier
- name: Display name
- status: healthy | degraded | warning
- uptime: Percentage uptime
...
```

The middleware automatically injects this into the prompt when the agent has knowledge tools.

## Extending Your Agent

### Adding Tools

Edit `tools.py` to add custom tools:

```python
from langchain_core.tools import tool

@tool
async def get_service_health_summary() -> str:
    """Quick summary of service health status."""
    # Custom logic here
    ...

def get_tools():
    return [api_get, fetch_file, get_service_health_summary]
```

### Adding Knowledge (Skills and Facts)

Create an agent with knowledge tools:

```bash
macsdk new agent devops-specialist --with-knowledge
```

Or add knowledge to an existing agent manually:

**Skills** (`skills/deploy-service.md`):
```markdown
---
name: deploy-service
description: How to deploy a service safely
---

# Deploy Service

## Steps
1. Check service health
2. Review alerts
3. Deploy using API
4. Monitor deployment
```

**Facts** (`facts/service-catalog.md`):
```markdown
---
name: service-catalog
description: Information about available services
---

# Service Catalog

## Production Services
- API Gateway (ID: 1)
- Auth Service (ID: 2)
```

📖 **See [Using Knowledge Tools](./using-knowledge-tools.md)** for complete documentation.

## Response Models

By default, agents use `BaseAgentResponse` from the SDK, which provides:
- `response_text`: Human-readable response
- `tools_used`: List of tools that were called

This is sufficient for most agents. For advanced use cases (like inter-agent data coordination), you can extend the base model in `models.py`.

## The SpecialistAgent Protocol

Every agent must implement the `SpecialistAgent` protocol:

```python
class InfraAgent:
    name: str = "infra_agent"
    capabilities: str = CAPABILITIES  # Same as SYSTEM_PROMPT
    tools: list = []

    def __init__(self):
        self.tools = get_tools()

    async def run(self, query: str, ...) -> dict:
        """Execute the agent."""
        ...

    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for the supervisor."""
        ...
```

## Testing Your Agent

### Interactive Testing

```bash
uv run infra-agent chat
```

### Run Tests

```bash
uv run pytest
```

## Adding to a Chatbot

### Remote Agents (Multi-repo)

```bash
cd my-chatbot
macsdk add-agent . --path ../infra-agent
```

### Local Agents (Mono-repo)

Create an agent inside your chatbot project:

```bash
cd my-chatbot
macsdk add-agent . --new weather --description "Weather information service"
```

This creates the agent in `src/my_chatbot/local_agents/weather/` and automatically registers it.

## Task Planning

The `SPECIALIST_PLANNING_PROMPT` is automatically included, providing:

- Chain-of-thought reasoning guidance
- Multi-step investigation support
- Task decomposition patterns

For complex queries, the agent breaks them into steps:

```
User: "Why did the deployment fail?"
Agent:
1. Check recent deployments
2. Get failed pipeline details
3. Fetch error logs
4. Analyze and respond
```

## Best Practices

1. **Clear CAPABILITIES**: Write detailed, specific CAPABILITIES for correct routing
2. **Use generic tools**: Start with `api_get` + `fetch_file`, add custom tools only when needed
3. **Extend with knowledge**: Use skills for procedures, facts for context
4. **Keep agents focused**: One agent = one domain
5. **Test interactively**: Use `uv run my-agent chat` for quick testing

## Container Deployment

Each generated agent includes a `Containerfile`:

```bash
# Build
podman build -t my-agent .

# Run
podman run --rm -it -e GOOGLE_API_KEY=$GOOGLE_API_KEY my-agent chat
```

## Summary

| Component | Purpose | Location |
|-----------|---------|----------|
| **CAPABILITIES** | What the agent does (single source of truth) | `agent.py` |
| **Tools** | What actions the agent can execute | `tools.py` |
| **Skills** | How to do complex tasks | `skills/*.md` |
| **Facts** | Domain context and reference data | `facts/*.md` |
| **Models** | Response structure (usually unchanged) | `models.py` |
