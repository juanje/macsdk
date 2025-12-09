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

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      api-agent                              │
├─────────────────────────────────────────────────────────────┤
│  Domain Tools (get_pipeline, get_failed_jobs, etc.)         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         MACSDK API Tools (api_get, fetch_file)      │    │
│  │  • Automatic retries with exponential backoff        │    │
│  │  • JSONPath extraction for specific fields           │    │
│  │  • Log file download for investigation               │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         DevOps Mock API                              │    │
│  │  /pipelines  /jobs  /services  /alerts  /deployments │    │
│  └─────────────────────────────────────────────────────┘    │
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
>> Get the log for the failed deploy job
```

### Service Health

```
>> List all services
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

| Tool | Description |
|------|-------------|
| `list_pipelines` | Get all pipelines |
| `get_pipeline` | Get pipeline details |
| `get_failed_pipelines` | Find failed pipelines |
| `get_jobs_for_pipeline` | Get jobs in a pipeline |
| `get_failed_jobs` | Find all failed jobs |
| `get_job` | Get job with error details |
| `get_job_log` | Download job log file |
| `list_services` | Get all services |
| `get_unhealthy_services` | Find degraded services |
| `list_alerts` | Get all alerts |
| `get_critical_alerts` | High-priority alerts |
| `list_deployments` | Deployment history |

## Using with Chatbots

Register the agent in your chatbot:

```python
from api_agent import ApiAgentAgent
from macsdk.core import register_agent

register_agent(ApiAgentAgent())
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
