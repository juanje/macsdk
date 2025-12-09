# Configuration Reference

MACSDK supports flexible configuration through multiple sources.

## Configuration Priority

Configuration is loaded in the following order (highest to lowest):

1. **Explicit values** passed to constructors
2. **Environment variables**
3. **`.env` file** in the project root
4. **`config.yml` file** in the project root
5. **Default values**

## Configuration File (config.yml)

Create a `config.yml` file in your project root:

```yaml
# =============================================================================
# LLM Configuration
# =============================================================================
llm_model: gemini-2.5-flash
llm_temperature: 0.3
llm_reasoning_effort: medium  # low, medium, high

# =============================================================================
# Classifier Configuration (for routing queries)
# =============================================================================
classifier_model: gemini-2.5-flash
classifier_temperature: 0.0
classifier_reasoning_effort: low

# =============================================================================
# Middleware Configuration
# =============================================================================
include_datetime: true  # Inject current datetime into prompts

# Context summarization (for long conversations)
summarization_enabled: false
summarization_trigger_tokens: 100000
summarization_keep_messages: 6

# =============================================================================
# Web Server Configuration
# =============================================================================
server_host: 0.0.0.0
server_port: 8000
message_max_length: 5000
warmup_timeout: 15.0
```

## RAG Configuration

If your chatbot was created with `--with-rag`, configure the RAG agent:

```yaml
# =============================================================================
# RAG (Retrieval-Augmented Generation) Configuration
# =============================================================================
rag:
  enabled: true

  # Documentation sources
  # Supported types: html (default), markdown
  sources:
    # HTML - Web pages (crawled recursively)
    - name: "api_docs"
      url: "https://docs.example.com/"
      tags: ["api", "reference"]

    # Markdown - Remote file
    - name: "readme"
      url: "https://raw.githubusercontent.com/org/repo/main/README.md"
      type: "markdown"
      tags: ["readme"]

    # Markdown - Local file
    - name: "guide"
      url: "./docs/user-guide.md"
      type: "markdown"
      tags: ["guide"]

    # Markdown - Local directory (loads all .md files recursively)
    - name: "all_docs"
      url: "./docs/"
      type: "markdown"
      tags: ["documentation"]

    # HTML with custom SSL certificate
    - name: "internal_docs"
      url: "https://docs.internal.company.com/"
      tags: ["internal"]
      cert_url: "https://certs.company.com/root-ca.pem"
      # Or use local cert: cert_path: "/path/to/cert.pem"

  # Indexing settings
  chunk_size: 1000          # Size of text chunks
  chunk_overlap: 200        # Overlap between chunks
  max_depth: 3              # Crawl depth for HTML URLs
  embedding_model: "models/embedding-001"

  # Retrieval settings
  retriever_k: 6            # Documents to retrieve
  max_rewrites: 2           # Max query rewrites
  model_name: "gemini-2.5-flash"
  temperature: 0.3

  # Caching
  enable_llm_cache: true    # Cache LLM responses

  # Domain glossary (helps RAG understand your terms)
  glossary:
    API: "Application Programming Interface"
    SDK: "Software Development Kit"
    RAG: "Retrieval-Augmented Generation"
    LLM: "Large Language Model"

  # Storage paths
  chroma_db_dir: "./chroma_db"
```

## API Services Configuration

Configure external API services for your agents to use with MACSDK's API tools:

```yaml
# =============================================================================
# API Services Configuration
# =============================================================================
api_services:
  # Public API with authentication
  github:
    base_url: "https://api.github.com"
    token: ${GITHUB_TOKEN}  # Bearer token (from env var)
    rate_limit: 5000
    timeout: 30
    max_retries: 3

  # Internal API with custom SSL certificate
  internal_api:
    base_url: "https://api.internal.company.com"
    token: ${INTERNAL_TOKEN}
    ssl_cert: "/path/to/company-ca.pem"
    headers:
      X-Custom-Header: "value"

  # Test server (disable SSL verification)
  test_server:
    base_url: "https://localhost:8443"
    ssl_verify: false  # ⚠️ Insecure! Only for development
```

### API Service Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | string | required | Base URL for the API |
| `token` | string | - | Bearer token for authentication |
| `headers` | dict | `{}` | Custom HTTP headers |
| `timeout` | int | `30` | Request timeout in seconds |
| `max_retries` | int | `3` | Number of retry attempts |
| `rate_limit` | int | - | Requests per hour limit |
| `ssl_cert` | string | - | Path to SSL certificate file |
| `ssl_verify` | bool | `true` | Verify SSL certificates |

### Using API Services in Code

```python
from macsdk.core.api_registry import register_api_service
from macsdk.tools import api_get

# Register programmatically
register_api_service(
    name="github",
    base_url="https://api.github.com",
    token=os.environ["GITHUB_TOKEN"],
)

# Use in tools
result = await api_get.ainvoke({
    "service": "github",
    "endpoint": "/repos/owner/repo",
    "extract": "$.name",  # JSONPath
})
```

## Environment Variables

All configuration options can be set via environment variables:

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key (required) | - |
| `LLM_MODEL` | Model for responses | `gemini-2.5-flash` |
| `LLM_TEMPERATURE` | Response creativity (0.0-1.0) | `0.3` |
| `LLM_REASONING_EFFORT` | Reasoning level | `medium` |

### Classifier Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CLASSIFIER_MODEL` | Model for routing | `gemini-2.5-flash` |
| `CLASSIFIER_TEMPERATURE` | Routing precision | `0.0` |
| `CLASSIFIER_REASONING_EFFORT` | Routing reasoning | `low` |

### Server Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_HOST` | Web server host | `0.0.0.0` |
| `SERVER_PORT` | Web server port | `8000` |
| `MESSAGE_MAX_LENGTH` | Max message length | `5000` |
| `WARMUP_TIMEOUT` | Startup timeout | `15.0` |

### Other

| Variable | Description | Default |
|----------|-------------|---------|
| `MACSDK_CONFIG_FILE` | Custom config path | - |

## .env File

Create a `.env` file for sensitive values:

```bash
# .env
GOOGLE_API_KEY=your_key_here
```

**Security Note**: Never commit `.env` files to version control.

## Programmatic Configuration

### Using create_config()

```python
from macsdk.core import create_config

# Load from default location (config.yml in cwd)
config = create_config()

# Load from specific file
config = create_config(config_path="./custom.yml")

# Search from a specific directory
config = create_config(search_path="/path/to/project")
```

### Extending MACSDKConfig

Create custom configuration for your chatbot:

```python
from macsdk.core import MACSDKConfig
from pydantic_settings import SettingsConfigDict

class MyChatbotConfig(MACSDKConfig):
    """Custom config with additional settings."""
    
    # Your custom settings
    my_api_url: str = "https://api.example.com"
    debug_mode: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
```

Set in `config.yml`:

```yaml
my_api_url: https://api.production.com
debug_mode: true
```

Or via environment:

```bash
export MY_API_URL=https://api.production.com
export DEBUG_MODE=true
```

## Configuration for Agents vs Chatbots

### Standalone Agent Testing

When testing an agent directly, it loads its own `config.yml`:

```bash
cd my-agent/
uv run my-agent chat  # Loads ./config.yml if present
```

### Agent in Chatbot

When registered with a chatbot, the chatbot's configuration is used:

```bash
cd my-chatbot/
uv run my-chatbot chat  # Agents use chatbot's config
```

This ensures consistent LLM settings across all agents.

## Best Practices

1. **API keys in .env**: Keep secrets in `.env`, not in `config.yml`
2. **Example files**: Provide `config.yml.example` and `.env.example`
3. **Default values**: Use sensible defaults so config is optional
4. **Document custom settings**: Add comments explaining custom options
5. **Validate early**: Call `config.validate_api_key()` at startup
6. **RAG glossary**: Add domain-specific terms for better retrieval
