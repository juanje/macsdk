# API Tools

> **Security Note**: When using tools that access URLs (`fetch_file`, `api_get`, etc.), consider enabling URL Security to protect against Server-Side Request Forgery (SSRF) attacks. See [URL Security Configuration](configuration.md#url-security-configuration) for details.

## Philosophy: Fewer tools, more intelligence

MACSDK adopts a minimalist approach to API tools: instead of creating a specific tool for each endpoint, we use **generic tools** and let the LLM decide which endpoints to call based on the API description in the prompt.

### The problem with many specific tools

Imagine an API with 20 endpoints. The traditional approach would be to create 20 tools:

```python
# ❌ Traditional approach: one tool per endpoint
@tool
async def get_services(): ...
@tool  
async def get_service_by_id(id: int): ...
@tool
async def get_failed_services(): ...
@tool
async def get_alerts(): ...
@tool
async def get_critical_alerts(): ...
@tool
async def get_unacknowledged_alerts(): ...
# ... 14 more tools
```

This approach has significant problems, both from a code maintenance perspective and from a **context engineering** standpoint:

**Code problems:**
- 🔧 Lots of repetitive code
- 📝 Each new feature requires a new tool
- 🐛 More code = more potential bugs

**Context engineering problems:**

Research shows that LLM performance **degrades significantly** when given access to many tools:

- **Performance Degradation**: Models perform worse—and in some cases fail completely—when presented with a large number of tools
- **Context Confusion**: Many similar tool descriptions confuse the model, leading it to call the wrong tool or hallucinate parameters
- **Ambiguity**: If a human developer cannot definitively say which tool should be used for a given situation, an AI agent cannot be expected to do better
- **Context Overload**: Each tool definition adds to the context window (the LLM's working memory), increasing API costs and latency

The solution from context engineering best practices is clear: **curate a minimal viable set of tools** that are flexible enough to handle multiple use cases

### The solution: generic tools + descriptive prompt

With MACSDK, you use **2 tools** that work for everything:

```python
# ✅ MACSDK approach: generic tools
from macsdk.tools import api_get, fetch_file

tools = [api_get, fetch_file]
```

And describe the API in the prompt:

```python
SYSTEM_PROMPT = """
## API Service: "devops"

Available endpoints:
- GET /services - List all services
- GET /services/{id} - Get a specific service
- GET /alerts - List alerts
- GET /alerts with params {"severity": "critical"} - Filter by severity

Always use service="devops" when calling api_get.
"""
```

**Advantages:**
- ✨ Simple and maintainable code
- 🧠 LLMs are very good at choosing endpoints based on descriptions
- 🔄 Adding endpoints is just updating the prompt
- 🎯 Fewer decisions = fewer LLM errors

## How it works

### 1. Register your API service

```python
from macsdk.core.api_registry import register_api_service

register_api_service(
    name="devops",  # Name the LLM will use
    base_url="https://api.example.com",
    timeout=10,
)
```

### 2. Describe the API in the prompt

```python
SYSTEM_PROMPT = """You are a DevOps assistant.

## API Service: "devops"

Endpoints:
- GET /services - List services with status (healthy/degraded/warning)
- GET /services/{id} - Service details
- GET /pipelines - List CI/CD pipelines
- GET /pipelines with params {"status": "failed"} - Failed pipelines
- GET /alerts - List alerts
- GET /alerts with params {"severity": "critical"} - Critical only

Always use service="devops" when calling api_get.
"""
```

### 3. Use the generic tools

```python
from macsdk.tools import api_get, fetch_file

def get_tools():
    return [api_get, fetch_file]
```

### 4. The LLM does the rest

When the user asks "Are there any failed pipelines?", the LLM:
1. Reads the prompt and sees that `/pipelines` with `{"status": "failed"}` is what's needed
2. Calls `api_get` with the correct parameters
3. Processes the response and answers the user

```
User: Are there any failed pipelines?

LLM: [Calls api_get with service="devops", endpoint="/pipelines", params={"status": "failed"}]

Response: Yes, there is 1 failed pipeline: "deploy-production".
```

## Available tools

### api_get

For querying data from REST APIs:

```python
await api_get.ainvoke({
    "service": "devops",           # The registered service
    "endpoint": "/services",        # Endpoint path
    "params": {"status": "failed"}, # Query parameters (optional)
})
```

### fetch_file

For downloading files (logs, configs, etc.):

```python
await fetch_file.ainvoke({
    "url": "https://example.com/logs/job-5.log",
})
```

### api_post, api_put, api_patch, api_delete

For write operations (if your API supports them):

```python
await api_post.ainvoke({
    "service": "devops",
    "endpoint": "/alerts",
    "body": {"title": "New alert", "severity": "warning"},
})
```

## When to create custom tools

Sometimes it makes sense to create specific tools:

1. **Complex business logic**: Combining multiple calls or transforming data
2. **JSONPath extraction**: When you need specific fields to reduce tokens
3. **Special validation**: When you need to validate parameters before calling

### Example: Tool with JSONPath

Use `make_api_request` to create tools that extract specific fields:

```python
from langchain_core.tools import tool
from macsdk.tools import make_api_request

@tool
async def get_service_health_summary() -> str:
    """Quick summary of all services health status."""
    result = await make_api_request(
        "GET", "devops", "/services",
        extract="$[*].{name: name, status: status}",  # Only name and status
    )
    
    if not result["success"]:
        return "Error fetching services"
    
    lines = []
    for svc in result["data"]:
        emoji = {"healthy": "✅", "degraded": "⚠️"}.get(svc["status"], "❌")
        lines.append(f"{emoji} {svc['name']}: {svc['status']}")
    
    return "\n".join(lines)
```

### Example: Tool that combines calls

```python
@tool
async def investigate_failed_job(job_id: int) -> str:
    """Investigate a failed job including its log."""
    # Get job details
    job = await make_api_request("GET", "devops", f"/jobs/{job_id}")
    
    if not job["success"]:
        return f"Error: {job['error']}"
    
    # Download log if available
    log_content = ""
    if job["data"].get("log_url"):
        log_content = await fetch_file.ainvoke({"url": job["data"]["log_url"]})
    
    return f"""
## Job: {job["data"]["name"]}
Status: {job["data"]["status"]}
Error: {job["data"].get("error", "N/A")}

### Log:
{log_content[-500:] if log_content else "Not available"}
"""
```

## Registering API services

### Registration options

```python
from macsdk.core.api_registry import register_api_service

# Basic
register_api_service(
    name="myapi",
    base_url="https://api.example.com",
)

# With Bearer authentication
register_api_service(
    name="github",
    base_url="https://api.github.com",
    token=os.environ["GITHUB_TOKEN"],
)

# With custom headers
register_api_service(
    name="custom",
    base_url="https://api.example.com",
    headers={"X-API-Key": os.environ["API_KEY"]},
)

# With local SSL certificate file
register_api_service(
    name="internal",
    base_url="https://internal.company.com",
    ssl_cert="/path/to/ca-cert.pem",
)

# With remote SSL certificate (downloaded and cached automatically)
register_api_service(
    name="corporate",
    base_url="https://api.corporate.com",
    ssl_cert="https://certs.corporate.com/ca-bundle.pem",
)
```

### All options

| Option | Description |
|--------|-------------|
| `name` | Unique service identifier |
| `base_url` | Base URL for all requests |
| `token` | Bearer token for authentication |
| `headers` | Additional HTTP headers |
| `timeout` | Timeout in seconds (default: 30) |
| `max_retries` | Retry attempts (default: 3) |
| `ssl_cert` | Path or URL to SSL certificate (URLs are auto-cached) |
| `ssl_verify` | Verify SSL (default: True) |

## Calculate Tool

The `calculate` tool provides safe mathematical expression evaluation. LLMs are notoriously unreliable at arithmetic, so this tool ensures accurate calculations.

### Why Calculate?

```python
# ❌ Without calculate tool
User: "What's 15% of 237?"
Agent: "That's about 35.5"  # WRONG (correct: 35.55)

# ✅ With calculate tool
User: "What's 15% of 237?"
Agent: calculate("(237 * 15) / 100")
Result: "35.55"  # CORRECT
```

### Usage

The `calculate` tool is **included by default** in all agent templates. It should not be removed.

```python
from macsdk.tools import api_get, fetch_file, calculate

def get_tools():
    return [
        api_get,
        fetch_file,
        calculate,  # Required - LLMs cannot do math reliably
    ]
```

### Supported Operations

- **Arithmetic**: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- **Functions**: `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `log2`, `exp`, `abs`, `round`, `min`, `max`, `sum`, `pow`, `floor`, `ceil`, `factorial`, `gcd`
- **Constants**: `pi`, `e`, `tau`, `inf`
- **Comparisons**: `<`, `>`, `<=`, `>=`, `==`, `!=`

### Examples

```python
calculate("2 + 2")                    # "4"
calculate("sqrt(16) * 2")             # "8.0"
calculate("sin(pi/2)")                # "1.0"
calculate("(1000 * 0.15) + 500")      # "650.0"
calculate("factorial(5)")             # "120"
calculate("round(3.14159, 2)")        # "3.14"
```

### Safety

The tool uses `simpleeval` for safe expression evaluation - no access to file system, imports, or dangerous operations.

## Knowledge Tools

Knowledge tools enable agents to access task instructions (skills) and contextual information (facts) packaged with the agent.

### Overview

- **Skills**: Step-by-step instructions for tasks (e.g., "how to deploy a service")
- **Facts**: Contextual information (e.g., "service catalog with IDs and configurations")
- **Tools**: `list_skills`, `read_skill`, `list_facts`, `read_fact`
- **Middleware**: Auto-injects usage instructions

### Quick Start

```bash
# Create agent with knowledge tools
macsdk new agent my-agent --with-knowledge
```

This generates:

```
my-agent/
└── src/
    └── my_agent/
        ├── agent.py          # Pre-configured
        ├── skills/           # Task instructions
        │   └── example-skill.md
        └── facts/            # Contextual info
            └── example-fact.md
```

### Using the Bundle

The recommended pattern uses lazy initialization in `get_tools()`:

**`tools.py`** - Single source of truth:

```python
from macsdk.tools import api_get, calculate, fetch_file

def get_tools() -> list:
    """Get all tools for this agent."""
    from macsdk.tools.knowledge import get_knowledge_bundle
    
    _ensure_api_registered()
    knowledge_tools, _ = get_knowledge_bundle(__package__)
    
    return [
        api_get,
        fetch_file,
        calculate,
        *knowledge_tools,  # list_skills, read_skill, list_facts, read_fact
    ]
```

**`agent.py`** - Direct middleware setup:

```python
from macsdk.tools.knowledge import get_knowledge_bundle

def create_agent_name():
    tools = get_tools()  # Already includes knowledge tools
    
    middleware = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]
    
    _, knowledge_middleware = get_knowledge_bundle(__package__)
    middleware.extend(knowledge_middleware)
    
    return create_agent(tools=tools, middleware=middleware)
```

This pattern ensures:
- ✅ Tools visible in CLI `tools` command
- ✅ Zero duplication
- ✅ No middleware/tools mismatch

### File Format

All knowledge files use YAML frontmatter:

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

### Agent Workflow

When a user asks to perform a task:

1. Agent calls `list_skills()` to see available instructions
2. Agent calls `read_skill("deploy-service.md")` to get the steps
3. Agent follows the instructions systematically
4. Agent uses `list_facts()` / `read_fact()` for accurate data

### Why Knowledge Tools?

- **Consistency**: Same procedure every time
- **Accuracy**: Correct service names and IDs from facts
- **Maintainability**: Update knowledge files, not prompts
- **Portability**: Knowledge travels with the agent package

### Complete Guide

See [Using Knowledge Tools Guide](../guides/using-knowledge-tools.md) for:
- Advanced usage patterns
- Best practices for writing skills/facts
- Package distribution
- Troubleshooting

## Summary

| Approach | When to use |
|----------|-------------|
| **Generic tools** | For most cases. Describe the API in the prompt. |
| **Custom tools** | When you need JSONPath, business logic, or combining calls. |
| **Calculate tool** | Always include by default. LLMs are bad at math. |
| **Knowledge tools** | Package task instructions and contextual info with your agent. |

The key is trusting the LLM's ability to understand API descriptions and choose the right endpoints. Fewer tools = less complexity = fewer errors.
