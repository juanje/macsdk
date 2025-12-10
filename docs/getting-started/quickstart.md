# Quick Start

This guide will help you create your first chatbot with MACSDK in under 5 minutes.

## 1. Create a Chatbot Project

```bash
macsdk new chatbot my-chatbot --display-name "My First Chatbot"
cd my-chatbot
```

This creates:

```
my-chatbot/
├── pyproject.toml
├── Containerfile         # For container deployment
├── src/my_chatbot/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── prompts.py
│   └── agents.py
├── static/
│   └── index.html        # Web interface
├── config.yml.example
├── .env.example
├── .gitignore
└── README.md
```

## 2. Configure Your API Key

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## 3. Install Dependencies

```bash
uv sync
```

## 4. Explore Available Commands

```bash
uv run my-chatbot
```

This shows the available commands:

```
╭────────────────────── My First Chatbot ──────────────────────╮
│                                                              │
│    chat      Start interactive CLI chat                      │
│    web       Start web interface                             │
│    agents    List registered agents                          │
│    info      Show configuration                              │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

## 5. Start the Chat

```bash
# CLI interface
uv run my-chatbot chat

# Or web interface
uv run my-chatbot web
# Open http://localhost:8000
```

You now have a working chatbot! But it doesn't have any agents yet.

## 6. Create an Agent

In a new terminal:

```bash
macsdk new agent infra-agent --description "Monitors infrastructure services"
cd infra-agent
```

The generated agent includes tools that connect to a demo DevOps API.
You can see them with:

```bash
uv run infra-agent tools
```

```
🔧 Available Tools (Generic SDK)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool       ┃ Description                                      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_get    │ Make a GET request to a registered API service.  │
│ fetch_file │ Fetch a file from a URL with optional filtering. │
└────────────┴──────────────────────────────────────────────────┘
```

These are **generic SDK tools** that work with any API. The API schema is in the prompt,
so the LLM decides which endpoints to call. Edit `prompts.py` to describe your API.

## 7. Add Agent to Chatbot

```bash
cd ../my-chatbot
macsdk add-agent . --path ../infra-agent
```

## 8. Test It

```bash
uv run my-chatbot chat
```

```
>> Is the authentication service running?
[infra_agent] Processing query...
[infra_agent] 🔧 Using tool: get_service_status

╭─────────────────────── Response ───────────────────────╮
│ Service auth-service: Running (healthy)                │
╰────────────────────────────────────────────────────────╯
```

## 9. Create a Chatbot with RAG (Optional)

For documentation Q&A capabilities:

```bash
macsdk new chatbot docs-assistant --with-rag
cd docs-assistant
cp config.yml.example config.yml
```

Edit `config.yml` to add your documentation sources:

```yaml
rag:
  enabled: true
  sources:
    - name: "my_docs"
      url: "https://docs.example.com/"
      tags: ["documentation"]
```

Index the documentation:

```bash
uv run docs-assistant index
```

Then start chatting:

```bash
uv run docs-assistant chat
```

## Next Steps

- [Creating Chatbots](../guides/creating-chatbots.md) - More chatbot customization
- [Creating Agents](../guides/creating-agents.md) - Build more sophisticated agents
- [CLI Reference](../reference/cli.md) - All CLI commands
- [Configuration Reference](../reference/configuration.md) - All configuration options
