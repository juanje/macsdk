# CLI Reference

Complete reference for MACSDK CLI commands.

## Global Options

```bash
macsdk --version    # Show version
macsdk --help       # Show help
```

## Commands

### `macsdk new`

Create new projects.

#### `macsdk new chatbot`

Create a new chatbot project.

```bash
macsdk new chatbot NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Project name (e.g., my-chatbot)

**Options:**
- `--display-name, -n TEXT`: Display name for the chatbot
- `--description, -d TEXT`: Description of the chatbot
- `--output-dir, -o PATH`: Output directory (default: current)
- `--with-rag`: Include RAG agent for documentation Q&A

**Examples:**
```bash
# Basic chatbot
macsdk new chatbot my-assistant \
  --display-name "My Assistant" \
  --description "A helpful assistant"

# Chatbot with RAG support
macsdk new chatbot docs-bot --with-rag
```

#### `macsdk new agent`

Create a new agent project.

```bash
macsdk new agent NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Agent name (e.g., my-agent)

**Options:**
- `--description, -d TEXT`: Description of the agent
- `--output-dir, -o PATH`: Output directory (default: current)

**Example:**
```bash
macsdk new agent infra-agent --description "Monitors infrastructure services"
```

### `macsdk add-agent`

Add an agent to a chatbot project. Supports both remote agents (external packages)
and local agents (mono-repo).

```bash
macsdk add-agent [CHATBOT_DIR] [OPTIONS]
```

**Arguments:**
- `CHATBOT_DIR`: Path to the chatbot project directory (default: `.`)

**Remote Agent Options (multi-repo):**
- `--package, -p TEXT`: Install from pip package
- `--git, -g TEXT`: Install from git repository
- `--path, -P TEXT`: Install from local path

**Local Agent Options (mono-repo):**
- `--new, -n TEXT`: Create a new agent inside the chatbot project
- `--description, -d TEXT`: Description for the new local agent

**Examples:**
```bash
# Remote agents (multi-repo approach)
macsdk add-agent . --package infra-agent
macsdk add-agent ./my-chatbot --git https://github.com/org/agent.git
macsdk add-agent . --path ../infra-agent

# Local agents (mono-repo approach)
macsdk add-agent . --new weather --description "Weather information service"
```

The local agent approach creates the agent inside the chatbot's source directory
under `src/{chatbot}/local_agents/{agent}/` and uses relative imports.

### `macsdk list-tools`

List tools provided by the MACSDK.

```bash
macsdk list-tools
```

Shows all reusable tools and API service configuration options:

```
🔧 MACSDK Tools
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool           ┃ Category ┃ Description                           ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_get        │ API      │ GET request to a registered service   │
│ api_post       │ API      │ POST request with JSON body           │
│ api_put        │ API      │ PUT request with JSON body            │
│ api_delete     │ API      │ DELETE request to an endpoint         │
│ api_patch      │ API      │ PATCH request with JSON body          │
│ fetch_file     │ Remote   │ Fetch file with grep/head/tail        │
│ fetch_and_save │ Remote   │ Download and save a file locally      │
│ fetch_json     │ Remote   │ Fetch JSON with JSONPath extraction   │
└────────────────┴──────────┴───────────────────────────────────────┘

⚙️  API Service Options
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Option      ┃ Description                                         ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ token       │ Bearer token for authentication                     │
│ headers     │ Custom HTTP headers                                 │
│ timeout     │ Request timeout (default: 30s)                      │
│ max_retries │ Retry attempts (default: 3)                         │
│ rate_limit  │ Requests per hour limit                             │
│ ssl_cert    │ Path to SSL certificate file                        │
│ ssl_verify  │ Verify SSL (default: true, false for test servers)  │
└─────────────┴─────────────────────────────────────────────────────┘
```

---

## Generated Project Commands

When you create a chatbot or agent, it gets its own CLI commands.

### Chatbot Commands

```bash
# Show available commands (default)
my-chatbot

# Start CLI chat
my-chatbot chat

# Start web interface
my-chatbot web
my-chatbot web --host 0.0.0.0 --port 8080

# List registered agents
my-chatbot agents

# Show configuration
my-chatbot info

# Index documentation (only with --with-rag)
my-chatbot index
my-chatbot index --force  # Force re-index

# Show version
my-chatbot --version
```

### Agent Commands

```bash
# Show available commands (default)
my-agent

# Start interactive chat
my-agent chat

# List available tools
my-agent tools

# Show agent info
my-agent info

# Show version
my-agent --version
```

---

## Environment Variables

The CLI respects these environment variables:

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google AI API key (required) |
| `LLM_MODEL` | Default LLM model |
| `LLM_TEMPERATURE` | Default temperature |
| `MACSDK_CONFIG_FILE` | Custom config file path |

---

## Exit Codes

- `0`: Success
- `1`: Error (directory exists, file not found, etc.)

---

## Examples

### Multi-Repo Workflow

Each agent is a separate project with its own repository:

```bash
# 1. Create a chatbot with RAG
macsdk new chatbot devops-assistant --with-rag
cd devops-assistant

# 2. Configure
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

cp config.yml.example config.yml
# Edit config.yml with your documentation sources

# 3. Install dependencies
uv sync

# 4. Index documentation
uv run devops-assistant index

# 5. Create a custom agent (separate project)
cd ..
macsdk new agent monitoring-agent --description "Monitors infrastructure"
cd monitoring-agent
uv sync

# 6. Add agent to chatbot
cd ../devops-assistant
macsdk add-agent . --path ../monitoring-agent

# 7. Run the chatbot
uv run devops-assistant chat
# Or: uv run devops-assistant web
```

### Mono-Repo Workflow

Agents live inside the chatbot project:

```bash
# 1. Create a chatbot
macsdk new chatbot devops-assistant
cd devops-assistant

# 2. Configure
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# 3. Install dependencies
uv sync

# 4. Create local agents (inside the chatbot)
macsdk add-agent . --new weather --description "Weather information"
macsdk add-agent . --new monitoring --description "Infrastructure monitoring"

# 5. Implement your agents
# Edit: src/devops_assistant/local_agents/weather/tools.py
# Edit: src/devops_assistant/local_agents/monitoring/tools.py

# 6. Run the chatbot
uv run devops-assistant chat
```

### Quick Test

```bash
# Create and test an agent standalone
macsdk new agent test-agent
cd test-agent
cp .env.example .env
# Edit .env
uv sync
uv run test-agent chat
```
