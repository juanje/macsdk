# MACSDK - Multi-Agent Chatbot SDK

A comprehensive SDK for building customizable multi-agent chatbots with RAG support, web interfaces, and reusable API tools.

## Features

- **🏗️ Scaffolding CLI**: Generate chatbot and agent projects with a single command
- **🤖 Intelligent Supervisor**: Automatic routing and orchestration of specialist agents
- **📚 RAG Agent**: Built-in retrieval-augmented generation for documentation queries
- **🌐 Web Interface**: FastAPI + WebSocket server with real-time streaming
- **🔧 API Tools**: Reusable tools for REST APIs with JSONPath extraction
- **🔄 Streaming**: Real-time progress updates for CLI and web interfaces

## Quick Start

### Installation

```bash
pip install macsdk
# or with uv
uv add macsdk
```

### Create a Chatbot

```bash
# Basic chatbot
macsdk new chatbot my-assistant --display-name "My Assistant"

# With RAG support for documentation queries
macsdk new chatbot my-assistant --with-rag

cd my-assistant
uv sync
```

### Create an Agent

```bash
macsdk new agent weather-agent --description "Fetches weather data"
```

### Run Your Chatbot

```bash
# Show available commands
my-assistant

# Start CLI chat
my-assistant chat

# Start web interface
my-assistant web

# List registered agents
my-assistant agents

# Show configuration
my-assistant info
```

### Run Your Agent (standalone)

```bash
# Show available commands
my-agent

# Start interactive chat
my-agent chat

# List tools
my-agent tools
```

## Configuration

### Environment Variables (.env)

```bash
GOOGLE_API_KEY=your_key_here
```

### YAML Configuration (config.yml)

```yaml
# LLM settings
llm_model: gemini-2.5-flash
llm_temperature: 0.3

# RAG sources (if --with-rag)
rag:
  enabled: true
  sources:
    - name: "My Docs"
      url: "https://docs.example.com/"
      tags: ["docs", "api"]
```

## Examples

The `examples/` directory contains working examples:

- **api-agent**: REST API interactions with JSONPlaceholder
- **devops-chatbot**: Multi-agent chatbot with RAG and API tools

## Development

```bash
git clone https://github.com/juanje/macsdk
cd macsdk
uv sync

# Run tests
uv run pytest

# Type checking & linting
uv run mypy src/
uv run ruff check .
```

## License

MIT

## 🤖 AI Tools Disclaimer

This project was developed with the assistance of artificial intelligence tools:

**Tools used:**
- **Cursor**: Code editor with AI capabilities
- **Claude-4.5-Opus**: Anthropic's language model

**Division of responsibilities:**

**Human (Juanje Ojeda)**:
- 🎯 Specification of objectives and requirements
- 📋 Definition of project's architecture
- 🔍 Critical review of code and documentation
- ✅ Final validation of concepts and approaches

**AI (Cursor + Claude-4.5-Opus)**:
- 🔧 Code prototyping and implementation
- 📝 Generation of examples and test cases
- 🐛 Debugging and error resolution
- 📚 Documentation writing

**Collaboration philosophy**: AI tools served as a highly capable technical assistant, while all design decisions and project directions were defined and validated by the human.
