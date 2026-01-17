# Vm Provision

A multi-agent chatbot built with MACSDK

## Installation

```bash
uv sync
```

## Configuration

Before running the chatbot, you need to configure your Google API key.

### Option 1: Environment file (recommended)

Copy the example file and add your API key:

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Option 2: YAML configuration

Copy the example config and customize:

```bash
cp config.yml.example config.yml
# Edit config.yml to customize LLM models, temperatures, etc.
```

Note: API keys should always be in `.env`, not in `config.yml`.

### Option 3: Environment variable

Export the variable directly:

```bash
export GOOGLE_API_KEY=your_key_here
```

You can get an API key from: https://aistudio.google.com/apikey

### Configuration Options in config.yml

```yaml
# LLM Configuration
llm_model: gemini-3-flash-preview      # Model for responses
llm_temperature: 0.3             # Creativity (0.0 - 1.0)
llm_reasoning_effort: medium     # low, medium, high

# Server settings (for web interface)
server_host: 0.0.0.0
server_port: 8000
```

## Usage

### Show Commands

```bash
uv run vm-provision
```

### Interactive Chat (CLI)

```bash
uv run vm-provision chat
```

### Web Interface

```bash
uv run vm-provision web
# Open http://localhost:8000
```

### List Agents

```bash
uv run vm-provision agents
```

### Show Configuration

```bash
uv run vm-provision info
```

### Logging

Logs are written to `./logs/` by default. Each execution creates a new log file with a timestamp (e.g., `vm_provision-2026-01-04-15-30-45.log`):

```bash
# Show LLM prompts and responses (clean, without HTTP noise)
uv run vm-provision chat --show-llm-calls

# Verbose mode (INFO level)
uv run vm-provision chat -v

# Very verbose (DEBUG level, technical logs)
uv run vm-provision chat -vv

# Show LLM calls with DEBUG logs
uv run vm-provision chat -vv --show-llm-calls

# Quiet mode (only errors)
uv run vm-provision chat -q

# Custom log file
uv run vm-provision chat --log-file ./my-logs/debug.log

# Explicit log level
uv run vm-provision chat --log-level DEBUG
```

**⚠️ Security Warning:** When using `--show-llm-calls`, full LLM prompts and responses (including user inputs and conversation history) are logged to disk. This may include sensitive information such as:
- User queries containing personal data
- API responses with private information
- System prompts with business logic

**Recommendations:**
- Only enable `--show-llm-calls` during development/debugging
- Never enable in production environments with user data
- Review and sanitize log files before sharing
- Consider log file permissions and secure storage
- Rotate or delete logs containing sensitive data after debugging

Configure logging in `config.yml`:

```yaml
log_level: INFO        # DEBUG, INFO, WARNING, ERROR
log_dir: ./logs        # Directory for log files
```

Or via environment variables:

```bash
export LOG_LEVEL=DEBUG
export LOG_DIR=./my-logs
```

## Customization

### Adding Agents

Use the MACSDK CLI to add agents:

```bash
macsdk add-agent . --package my-agent
```

Or manually edit `src/vm_provision/agents.py`.

### Customizing Behavior

Edit `src/vm_provision/prompts.py` to customize:
- Chatbot name and description
- Additional context for the supervisor
- Response guidelines

### Custom Configuration

Edit `src/vm_provision/config.py` to add your own settings.
