# MACSDK - Multi-Agent Chatbot SDK

A comprehensive SDK for building customizable multi-agent chatbots with RAG support, web interfaces, and reusable API tools.

## What can it do?

- Create a **chatbot** with CLI and Web UI, ready to be used immediately.
- Create **agents** with a CLI chat (for testing purposes) ready to be used.
- **Register agents** into chatbots, so your chatbot can call any of the agents you add.

## How does it work?

MACSDK follows a **supervisor + specialist agents** architecture:

- **Supervisor**: Routes user queries to the right specialist agent
- **Specialist Agents**: Focused experts that handle specific tasks (APIs, monitoring, etc.)
- **Formatter**: Ensures consistent, user-friendly responses

**Philosophy**: Agents are **simple by default, extensible without code changes**:
- Start with just `CAPABILITIES` (what the agent does)
- Add tools for new actions (`api_get`, `fetch_file`, etc.)
- Extend with **Skills** (how-to guides) and **Facts** (domain knowledge) - auto-detected
- Use `EXTENDED_INSTRUCTIONS` for critical per-request guidelines

## Key Features

- **🏗️ Zero-Config Scaffolding**: Generate production-ready chatbots and agents instantly
- **🤖 Intelligent Supervisor**: Automatic routing and orchestration of specialist agents
- **🔧 Auto-Detected Tools**: `calculate`, `read_skill`, `read_fact` included automatically
- **📚 Knowledge Extension**: Add Skills and Facts without code changes - just drop .md files
- **🌐 Web Interface**: Built-in FastAPI + WebSocket server with real-time streaming
- **⏱️ Time Awareness**: Agents automatically know current date/time
- **🔄 Progress Tracking**: Real-time visibility into agent selection and tool usage
- **🎯 Simple & Extensible**: Agents work out-of-box, extend via tools/skills/facts

## Quick Start

### Installation

For detailed installation instructions, see the [Installation Guide](docs/getting-started/installation.md).

```bash
# Clone and install
git clone https://github.com/juanje/macsdk
cd macsdk
uv sync

# Or install via pip/uv (once published)
# uv add macsdk
```

### 1. Create a Chatbot

Learn more in the [Creating Chatbots Guide](docs/guides/creating-chatbots.md).

```bash
macsdk new chatbot my-chatbot --display-name "My First Chatbot"
cd my-chatbot
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
uv sync
uv run my-chatbot
```
*It's ready to use immediately.*

### 2. Create an Agent

Learn more in the [Creating Agents Guide](docs/guides/creating-agents.md).

```bash
cd ..
macsdk new agent infra-agent --description "Monitors infrastructure services"
cd infra-agent
uv sync
uv run infra-agent chat
```

*Agents work immediately. Extend with:*
- Tools in `tools.py` (actions)
- Skills in `skills/*.md` (procedures)
- Facts in `facts/*.md` (domain knowledge)

### 3. Register the Agent to the Chatbot

```bash
cd ../my-chatbot/
macsdk add-agent . --path ../infra-agent
```

Now you'll be able to use the chat, which can delegate to the agent if needed.

```bash
uv run my-chatbot chat
# Or using the Web UI
uv run my-chatbot web
```

You can add as many agents as you want!

## Configuration

### Environment Variables (.env)

```bash
GOOGLE_API_KEY=your_key_here
```

### YAML Configuration (config.yml)

```yaml
# LLM settings
llm_model: gemini-3-flash-preview
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

- **api-agent**: REST API interactions with JSONPlaceholder.
- **devops-chatbot**: Multi-agent chatbot with RAG and API tools.

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

<details>
<summary>This project was developed with the assistance of artificial intelligence tools</summary>

**Tools used:**
- **Cursor**: Code editor with AI capabilities
- **Claude-4.5-Opus**: Anthropic's language model

**Division of responsibilities:**

**Human (Juanje Ojeda)**:
- 🎯 Specification of objectives and requirements
- 📋 Definition of project's architecture
- 🔍 Critical review of code and documentation
- 💬 Iterative feedback and solution refinement
- ✅ Final validation of concepts and approaches

**AI (Cursor + Claude-4.5-Opus)**:
- 🔧 Initial code prototyping
- 📝 Generation of examples and test cases
- 🐛 Assistance in debugging and error resolution
- 📚 Documentation and comments writing
- 💡 Technical implementation suggestions

**Collaboration philosophy**: AI tools served as a highly capable technical assistant, while all design decisions and project directions were defined and validated by the human.
</details>

---
- author: Juanje Ojeda
- email: juanje@redhat.com
