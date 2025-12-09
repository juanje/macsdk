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
macsdk new agent weather-agent --description "Provides weather information"
cd weather-agent
```

Edit `src/weather_agent/tools.py`:

```python
from langchain_core.tools import tool

@tool
async def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: Name of the city.
        
    Returns:
        Weather information.
    """
    # In a real agent, you'd call a weather API
    return f"The weather in {city} is sunny, 22°C"
```

## 7. Add Agent to Chatbot

```bash
cd ../my-chatbot
macsdk add-agent . --path ../weather-agent
```

## 8. Test It

```bash
uv run my-chatbot chat
```

```
>> What's the weather in Madrid?
[weather_agent] Processing query...
[weather_agent] 🔧 Using tool: get_weather

╭─────────────────────── Response ───────────────────────╮
│ The weather in Madrid is sunny, 22°C                   │
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
