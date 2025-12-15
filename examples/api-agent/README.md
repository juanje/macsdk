# api-agent

A DevOps monitoring agent demonstrating **MACSDK's API tools**.

Uses the [DevOps Mock API](https://github.com/juanje/devops-mock-api) hosted on
[my-json-server.typicode.com](https://my-json-server.typicode.com/juanje/devops-mock-api).

## Features

- 🔄 **Pipeline monitoring**: Check CI/CD pipeline status
- 🔍 **Job investigation**: Find failed jobs and download logs
- 💚 **Service health**: Monitor infrastructure services
- 🚨 **Alert management**: Track warnings and critical issues
- 📦 **Deployment tracking**: View deployment history

## Two Approaches to API Tools

This example demonstrates both approaches:

### Approach 1: Generic Tools (Recommended)

Use `api_get` and `fetch_file` directly. The API schema is in the prompt,
and the LLM decides which endpoints to call:

```python
from macsdk.tools import api_get, fetch_file

# The LLM calls these with appropriate parameters
tools = [api_get, fetch_file]
```

### Approach 2: Custom Tools (For specialized cases)

Use `make_api_request` with JSONPath extraction for complex operations:

```python
from macsdk.tools import make_api_request

@tool
async def get_failed_pipeline_names() -> str:
    """Get just the names of failed pipelines."""
    result = await make_api_request(
        "GET", "devops", "/pipelines",
        params={"status": "failed"},
        extract="$[*].name",  # JSONPath extraction
    )
    return ", ".join(result["data"]) if result["success"] else "Error"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      api-agent                              │
├─────────────────────────────────────────────────────────────┤
│  Generic Tools        │    Custom Tools                     │
│  (api_get, fetch_file)│    (with make_api_request)          │
│  LLM decides endpoint │    JSONPath, business logic         │
│           │           │             │                       │
│           └───────────┴─────────────┘                       │
│                       │                                     │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         DevOps Mock API                              │   │
│  │  /pipelines  /jobs  /services  /alerts  /deployments │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
uv sync
```

## Configuration

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Usage

### Show Commands

```bash
uv run api-agent
```

### Interactive Chat

```bash
uv run api-agent chat
```

### List Tools

```bash
uv run api-agent tools
```

### Show Agent Info

```bash
uv run api-agent info
```

## Example Queries

### Pipeline Monitoring

```
>> Show me all pipelines
>> Which pipelines failed?
>> Get details of pipeline 1
```

### Job Investigation

```
>> What jobs are in pipeline 1?
>> Show me the failed jobs
>> Investigate failed job 5
```

### Service Health

```
>> Give me a service health summary
>> Are there any unhealthy services?
>> What's the status of the api-gateway?
```

### Alerts

```
>> Show me all alerts
>> Are there any critical alerts?
>> What alerts need acknowledgment?
```

### Deployments

```
>> Show deployment history
>> What's deployed to production?
```

## Available Tools

| Tool | Type | Description |
|------|------|-------------|
| `api_get` | Generic | Make GET requests to any endpoint |
| `fetch_file` | Generic | Download files (logs, configs) |
| `get_service_health_summary` | Custom | Quick health overview with emojis |
| `get_failed_pipeline_names` | Custom | Just names of failed pipelines |
| `investigate_failed_job` | Custom | Full investigation with log excerpt |

## Using with Chatbots

Register the agent in your chatbot:

```python
from api_agent import ApiAgent
from macsdk.core import register_agent

register_agent(ApiAgent())
```

## Development

```bash
uv run ruff check src/
uv run ruff format src/
```

## 🤖 AI Tools Disclaimer

This project was developed with the assistance of artificial intelligence tools:

**Tools used:**
- **Cursor**: Code editor with AI capabilities
- **Claude-4.5-Opus**: Anthropic's language model

**Division of responsibilities:**

**Human (Juanje Ojeda)**:
- 🎯 Specification of objectives and requirements
- 🔍 Critical review of code and documentation
- ✅ Final validation of concepts and approaches

**AI (Cursor + Claude-4.5-Opus)**:
- 🔧 Code prototyping and implementation
- 📝 Generation of examples and test cases
- 📚 Documentation writing
