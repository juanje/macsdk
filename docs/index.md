# MACSDK Documentation

Welcome to the MACSDK (Multi-Agent Chatbot SDK) documentation.

## What is MACSDK?

MACSDK is a comprehensive SDK for building customizable multi-agent chatbots. It provides:

- **Core Framework**: Protocol definitions, agent registry, and supervisor orchestration
- **Built-in RAG Agent**: Index documentation and answer questions using retrieval-augmented generation
- **API Tools**: Ready-to-use tools for REST API interactions with JSONPath extraction
- **CLI Tools**: Scaffolding commands to generate chatbots and agents
- **Web & CLI Interfaces**: Beautiful Rich-powered CLI and FastAPI web server with WebSocket streaming
- **Extensible Architecture**: Agents as separate packages that can be independently maintained

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [Creating Chatbots](guides/creating-chatbots.md)
- [Creating Agents](guides/creating-agents.md)
- [API Tools Reference](reference/tools.md)
- [CLI Reference](reference/cli.md)
- [Configuration Reference](reference/configuration.md)
- [Protocol Reference](reference/protocol.md)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                            MACSDK                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │    Core     │  │    CLI      │  │   Tools     │  │   Agents   │ │
│  │             │  │             │  │             │  │            │ │
│  │ - Protocol  │  │ - new       │  │ - api_get   │  │ - RAG      │ │
│  │ - Registry  │  │ - add-agent │  │ - api_post  │  │   Agent    │ │
│  │ - Supervisor│  │ - list      │  │ - fetch_file│  │            │ │
│  │ - Config    │  │             │  │             │  │            │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                        Interfaces                                    │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │      CLI Interface          │  │      Web Interface          │  │
│  │  Rich tables, panels,       │  │  FastAPI + WebSocket        │  │
│  │  progress indicators        │  │  real-time streaming        │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                    Custom Chatbots                                   │
│  Uses macsdk.core, registers external agents                        │
├─────────────────────────────────────────────────────────────────────┤
│                    External Agents                                   │
│  Separate packages implementing SpecialistAgent protocol            │
└─────────────────────────────────────────────────────────────────────┘
```

## How It Works

1. **Create a Chatbot**: Use `macsdk new chatbot` to generate a new chatbot project
2. **Enable RAG** (optional): Add `--with-rag` to include documentation Q&A capabilities
3. **Create Agents**: Use `macsdk new agent` to generate specialist agent projects
4. **Register Agents**: Add agents to your chatbot with `macsdk add-agent`
5. **Run**: Start with `my-chatbot chat` (CLI) or `my-chatbot web` (web interface)

The supervisor automatically routes user queries to the appropriate specialist agents based on their declared capabilities.

## Features

### Built-in RAG Agent

Index documentation from multiple sources and answer questions:

```yaml
# config.yml
rag:
  enabled: true
  sources:
    - name: "docs"
      url: "https://docs.example.com/"
      type: "html"
    - name: "readme"
      url: "./docs/"
      type: "markdown"
```

### API Tools

Make REST API calls with automatic retries:

```python
from macsdk.tools import api_get

# The LLM uses api_get directly with any endpoint
result = await api_get.ainvoke({
    "service": "devops",
    "endpoint": "/services",
    "params": {"status": "healthy"},
})
```

For programmatic use with JSONPath extraction, use `make_api_request`:

```python
from macsdk.tools import make_api_request

result = await make_api_request(
    "GET", "devops", "/services",
    extract="$[*].name",  # JSONPath
)
```

### Beautiful CLI

Rich-powered interface with panels, tables, and progress indicators:

```
╭────────────────────── My Chatbot ──────────────────────╮
│  chat      Start interactive CLI chat                  │
│  web       Start web interface                         │
│  agents    List registered agents                      │
│  info      Show configuration                          │
╰────────────────────────────────────────────────────────╯
```

## Examples

Check the `examples/` directory for working examples:

- **api-agent**: DevOps monitoring agent using MACSDK's API tools
- **devops-chatbot**: Multi-agent chatbot with RAG and API agent
