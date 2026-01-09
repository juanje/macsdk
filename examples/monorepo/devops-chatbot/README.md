# DevOps Assistant (Mono-repo)

A multi-agent DevOps chatbot with RAG for documentation and API tools.

> **This is the mono-repo version** where the API agent is an internal module.
> See [`../multirepo/`](../multirepo/) for the multi-repo approach.

This example demonstrates a MACSDK chatbot with internal agents:
- **RAG Agent**: Query indexed documentation using semantic search
- **API Agent**: Interact with REST APIs (JSONPlaceholder as example)

## Features

- 📚 **Documentation Q&A**: Index and query documentation using RAG
- 🔌 **API Integration**: Query external APIs through the API agent
- 🤖 **Multi-Agent Architecture**: Supervisor routes queries to appropriate agents
- ⚙️ **Configurable**: Customize via `config.yml`

## Installation

```bash
uv sync
```

## Configuration

### 1. API Key

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. RAG Configuration (optional)

```bash
cp config.yml.example config.yml
# Edit config.yml to configure documentation sources
```

Example configuration:

```yaml
rag:
  enabled: true
  sources:
    - url: "https://docs.example.com/"
      tags: ["documentation", "api"]
```

## Usage

### Show Commands

```bash
uv run devops-chatbot
```

### Interactive Chat (CLI)

```bash
uv run devops-chatbot chat
```

### Web Interface

```bash
uv run devops-chatbot web
# Open http://localhost:8000
```

### Index Documentation (for RAG)

```bash
uv run devops-chatbot index
# Use --force to re-index
uv run devops-chatbot index --force
```

### List Registered Agents

```bash
uv run devops-chatbot agents
```

### Show Chatbot Info

```bash
uv run devops-chatbot info
```

## Registered Agents

| Agent | Description |
|-------|-------------|
| `rag_agent` | Answers questions from indexed documentation |
| `api_agent` | Interacts with JSONPlaceholder REST API |

## Example Queries

### Documentation (RAG)

```
>> What is the installation process?
>> How do I configure authentication?
>> Explain the architecture overview
```

### API Queries

```
>> List all users from the API
>> Get posts by user 1
>> Show pending TODOs for user 3
```

### General

```
>> Help me understand how to deploy this
>> What services are available?
```

## Project Structure

```
devops-chatbot/
├── src/devops_chatbot/
│   ├── __init__.py
│   ├── local_agents/   # Internal agents (mono-repo)
│   │   ├── __init__.py
│   │   └── api/           # API agent as internal module
│   │       ├── __init__.py
│   │       ├── agent.py   # CAPABILITIES + agent implementation
│   │       ├── config.py
│   │       ├── models.py
│   │       └── tools.py
│   ├── agents.py          # Agent registration (relative imports)
│   ├── cli.py             # CLI entry point
│   ├── config.py          # Custom configuration
│   └── prompts.py         # Supervisor prompts (chatbot customization)
├── config.yml.example     # RAG configuration example
├── .env.example           # Environment variables
└── pyproject.toml
```

## Customization

### Adding More Internal Agents (Mono-repo)

Use the CLI to create a new internal agent:

```bash
macsdk add-agent . --new weather --description "Weather forecasts"
```

This creates a new agent in `src/devops_chatbot/local_agents/weather/` and automatically updates `agents.py`.

Or manually create an agent in `src/devops_chatbot/local_agents/my_agent/` and update `agents.py`:

```python
from .local_agents.my_agent import MyAgent

def register_all_agents() -> None:
    # ... existing agents ...

    if not registry.is_registered("my_agent"):
        register_agent(MyAgent())
```

### Modifying RAG Sources

Edit `config.yml`:

```yaml
rag:
  enabled: true
  sources:
    - url: "https://your-docs.example.com/"
      tags: ["internal", "api"]
    - url: "https://other-docs.example.com/"
      tags: ["reference"]
      cert_url: "https://example.com/cert.pem"  # For internal SSL
```

## Development

```bash
# Run linting
uv run ruff check src/

# Format code
uv run ruff format src/
```

## 🤖 AI Tools Disclaimer

This project was developed with the assistance of artificial intelligence tools:

**Tools used:**
- **Cursor**: Code editor with AI capabilities
- **Claude-4-Sonnet**: Anthropic's language model

**Division of responsibilities:**

**AI (Cursor + Claude-4-Sonnet)**:
- 🔧 Initial code prototyping
- 📝 Generation of examples and test cases
- 🐛 Assistance in debugging and error resolution
- 📚 Documentation and comments writing
- 💡 Technical implementation suggestions

**Human (Juanje Ojeda)**:
- 🎯 Specification of objectives and requirements
- 🔍 Critical review of code and documentation
- 💬 Iterative feedback and solution refinement
- 📋 Definition of project's educational structure
- ✅ Final validation of concepts and approaches

**Collaboration philosophy**: AI tools served as a highly capable technical assistant, while all design decisions, educational objectives, and project directions were defined and validated by the human.
