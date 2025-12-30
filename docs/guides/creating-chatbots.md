# Creating Chatbots

This guide covers how to create and customize chatbot projects with MACSDK.

## Basic Creation

```bash
macsdk new chatbot my-assistant \
  --display-name "My Assistant" \
  --description "A helpful assistant for my team"
```

### With RAG Support

To include the built-in RAG agent for documentation Q&A:

```bash
macsdk new chatbot docs-assistant \
  --display-name "Docs Assistant" \
  --with-rag
```

## Project Structure

```
my-assistant/
├── pyproject.toml           # Dependencies and metadata
├── Containerfile            # Container build instructions
├── src/my_assistant/
│   ├── __init__.py          # Package marker
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI implementation (Rich-powered)
│   ├── config.py            # Custom configuration
│   ├── prompts.py           # Supervisor prompts
│   └── agents.py            # Agent registration
├── static/
│   └── index.html           # Web interface
├── config.yml.example       # Configuration template
├── .env.example             # Environment variables template
├── .gitignore
└── README.md
```

## Running Your Chatbot

### Show Available Commands

```bash
uv run my-assistant
```

```
╭────────────────────── My Assistant ──────────────────────╮
│                                                          │
│    chat      Start interactive CLI chat                  │
│    web       Start web interface                         │
│    agents    List registered agents                      │
│    info      Show configuration                          │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

### Start CLI Chat

```bash
uv run my-assistant chat
```

### Start Web Interface

```bash
uv run my-assistant web
# Open http://localhost:8000
```

### List Registered Agents

```bash
uv run my-assistant agents
```

```
🤖 Registered Agents
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Agent     ┃ Description              ┃ Tools ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ rag_agent │ Answers from docs...     │   0   │
│ api_agent │ API interactions...      │  18   │
└───────────┴──────────────────────────┴───────┘
```

### Show Configuration

```bash
uv run my-assistant info
```

```
╭────────────────────── My Assistant ──────────────────────╮
│                                                          │
│  Supervisor Model: gemini-2.5-flash                      │
│  Temperature: 0.3                                        │
│  Agents: rag_agent, api_agent                            │
│  RAG Sources: 2 configured                               │
│                                                          │
│  ✓ Configuration loaded successfully                     │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

## Configuring RAG

If you created your chatbot with `--with-rag`, configure the documentation sources:

```bash
cp config.yml.example config.yml
```

Edit `config.yml`:

```yaml
rag:
  enabled: true
  sources:
    # HTML documentation (web crawling)
    - name: "api_docs"
      url: "https://docs.example.com/"
      tags: ["api", "reference"]

    # Remote markdown file
    - name: "readme"
      url: "https://raw.githubusercontent.com/org/repo/main/README.md"
      type: "markdown"
      tags: ["readme"]

    # Local markdown directory
    - name: "guides"
      url: "./docs/"
      type: "markdown"
      tags: ["guides"]

  # Optional: Domain glossary
  glossary:
    API: "Application Programming Interface"
    SDK: "Software Development Kit"
```

Index the documentation:

```bash
uv run my-assistant index
# Use --force to re-index
uv run my-assistant index --force
```

## Registering Agents

The `agents.py` file manages agent registration:

```python
from macsdk.core import get_registry, register_agent

def get_registered_agents() -> list[dict]:
    """Return info about registered agents."""
    registry = get_registry()
    return [
        {
            "name": agent.name,
            "description": agent.capabilities[:100],
            "tools_count": len(getattr(agent, "tools", [])),
        }
        for agent in registry.get_all()
    ]

def register_all_agents() -> None:
    """Register all agents for the chatbot."""
    registry = get_registry()

    # Register RAG agent (if enabled)
    from macsdk.agents.rag import RAGAgent
    if not registry.is_registered("rag_agent"):
        register_agent(RAGAgent())

    # Register your custom agents
    from my_agent import MyAgent
    if not registry.is_registered("my_agent"):
        register_agent(MyAgent())
```

## Custom Configuration

Extend `config.py` for custom settings:

```python
from macsdk.core import MACSDKConfig

class MyConfig(MACSDKConfig):
    """Custom configuration."""
    
    # Add your custom settings
    custom_api_url: str = "https://api.example.com"
    custom_timeout: int = 30

config = MyConfig()
```

These can be set in `config.yml`:

```yaml
custom_api_url: https://api.production.com
custom_timeout: 60
```

## Customizing the Supervisor Prompt

Edit `prompts.py` to customize how the supervisor behaves:

```python
SUPERVISOR_CONTEXT = """You are a helpful DevOps assistant.

You have access to specialist agents:
- rag_agent: For documentation questions
- api_agent: For infrastructure monitoring

Always be concise and actionable in your responses.
"""
```

## Customizing Response Format

The response formatter synthesizes raw agent results into polished responses. You can customize the tone, format, and style by overriding specific prompt components in `prompts.py`.

### Composable Formatter Prompts

Instead of replacing the entire formatter prompt, override only the parts you need:

```python
from macsdk.prompts import build_formatter_prompt

# Change only the tone
FORMATTER_PROMPT = build_formatter_prompt(
    tone="""
## Tone Guidelines

- Always respond in Spanish
- Use formal language (usted)
- Be professional and respectful
- Keep responses brief and actionable
"""
)
```

### Available Components

You can override any of these components:

#### 1. Tone (`tone`)

Control the personality and style:

```python
FORMATTER_PROMPT = build_formatter_prompt(
    tone="""
## Tone Guidelines

- Friendly and encouraging
- Use emojis sparingly
- Be enthusiastic about helping
- Use simple, clear language
"""
)
```

#### 2. Format (`format_rules`)

Control the output structure:

```python
FORMATTER_PROMPT = build_formatter_prompt(
    format_rules="""
## Format Guidelines

- Use plain text (no markdown formatting)
- Always start with a summary sentence
- Use numbered lists for steps
- Keep responses under 200 words
- End with a follow-up question
"""
)
```

#### 3. Extra Instructions (`extra`)

Add domain-specific rules:

```python
FORMATTER_PROMPT = build_formatter_prompt(
    extra="""
## Additional Guidelines

- Always mention if data is from cache or live API
- Include timestamps for time-sensitive information
- Suggest relevant documentation links when applicable
- Flag any security concerns prominently
"""
)
```

### Combine Multiple Customizations

Override multiple components at once:

```python
FORMATTER_PROMPT = build_formatter_prompt(
    tone="""
## Tone Guidelines
- Technical and precise
- Use industry terminology
- Be direct and efficient
""",
    format_rules="""
## Format Guidelines
- Use markdown code blocks for commands
- Highlight warnings with ⚠️
- Use tables for comparisons
""",
    extra="""
## Additional Guidelines
- Always include links to relevant documentation
- Provide examples for complex concepts
"""
)
```

### Default Behavior

By default, the formatter:
- Uses plain text output (no markdown formatting)
- Maintains a professional yet friendly tone
- Synthesizes information from multiple agents
- Ensures conversation history consistency

## Container Deployment

Each generated chatbot includes a `Containerfile` for building container images.

### Build the Container

```bash
cd my-chatbot
podman build -t my-chatbot .
# Or with Docker
docker build -t my-chatbot -f Containerfile .
```

### Run the Container

```bash
# CLI chat
podman run --rm -it -e GOOGLE_API_KEY=$GOOGLE_API_KEY my-chatbot chat

# Web interface (expose port 8000)
podman run --rm -p 8000:8000 -e GOOGLE_API_KEY=$GOOGLE_API_KEY my-chatbot web --host 0.0.0.0

# Show help
podman run --rm my-chatbot --help
```

### Container Features

- **Multi-stage build**: Keeps final image small
- **UBI base image**: Red Hat Universal Base Image for enterprise use
- **Pre-built wheel**: Fast container startup
- **Configurable**: Override CMD for different commands

### Environment Variables in Containers

Pass configuration via environment variables:

```bash
podman run --rm -it \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -e LLM_MODEL=gemini-2.0-pro \
  -e SERVER_PORT=8080 \
  -p 8080:8080 \
  my-chatbot web --host 0.0.0.0 --port 8080
```

## Best Practices

1. **Keep agents separate**: Each agent should be its own package
2. **Use environment variables**: Store API keys in `.env`
3. **Configure RAG glossary**: Add domain-specific terms for better retrieval
4. **Test locally**: Run `uv run pytest` before deploying
5. **Index before chatting**: Run `index` command after changing RAG sources
