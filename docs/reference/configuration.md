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
llm_model: gemini-3-flash-preview
llm_temperature: 0.3
llm_reasoning_effort: medium  # low, medium, high

# =============================================================================
# Middleware Configuration
# =============================================================================
include_datetime: true  # Inject datetime context with pre-calculated dates
debug: false            # Show prompts sent to LLM (for debugging)
# Note: Task planning now via CoT prompts (TodoListMiddleware deprecated)

# Context summarization (for long conversations)
summarization_enabled: false
summarization_trigger_tokens: 100000
summarization_keep_messages: 6

# See Middleware Reference for details: reference/middleware.md

# =============================================================================
# Agent Execution Configuration
# =============================================================================
recursion_limit: 50  # Max iterations for agent tool calls (default: 50)
# Use higher values (100+) for complex workflows with many steps

# Timeout configuration (seconds) - prevents hanging on long-running operations
supervisor_timeout: 120.0      # Supervisor execution (includes specialist calls)
specialist_timeout: 90.0       # Specialist agent execution (includes LLM + tools)
formatter_timeout: 30.0        # Response formatting
llm_request_timeout: 60.0      # Individual LLM HTTP requests

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
  model_name: "gemini-3-flash-preview"
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

  # Internal API with local SSL certificate
  internal_api:
    base_url: "https://api.internal.company.com"
    token: ${INTERNAL_TOKEN}
    ssl_cert: "/path/to/company-ca.pem"  # Local file path
    headers:
      X-Custom-Header: "value"

  # Corporate API with remote SSL certificate (auto-downloaded and cached)
  corporate_api:
    base_url: "https://api.corporate.company.com"
    token: ${CORPORATE_TOKEN}
    ssl_cert: "https://certs.company.com/ca-bundle.pem"  # Remote URL

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
| `ssl_cert` | string | - | Path or URL to SSL certificate file (URLs are cached locally) |
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

### Remote SSL Certificates

MACSDK supports downloading SSL certificates from remote URLs, which is useful in corporate environments where certificates are distributed via a certificate server:

**Benefits:**
- ✅ No need to distribute certificates in repositories
- ✅ Always get the latest version of the certificate
- ✅ Certificates are cached locally (in `~/.cache/macsdk/certs/`)
- ✅ Automatic re-download on cache miss

**Example:**

```yaml
api_services:
  corporate_api:
    base_url: "https://api.corporate.company.com"
    token: ${CORPORATE_TOKEN}
    ssl_cert: "https://certs.company.com/ca-bundle.pem"
```

Or programmatically:

```python
register_api_service(
    name="corporate_api",
    base_url="https://api.corporate.company.com",
    token=os.environ["CORPORATE_TOKEN"],
    ssl_cert="https://certs.company.com/ca-bundle.pem",
)
```

**How it works:**
1. The first API call detects that `ssl_cert` is a URL
2. Downloads the certificate using the system's default SSL certificates
3. Validates it's a valid PEM certificate
4. Caches it locally at `~/.cache/macsdk/certs/`
5. Uses the cached version for subsequent calls

**Requirements:**
- The certificate server must use standard SSL (no custom CA needed to access it)
- The certificate file must be in PEM format
- The URL must be accessible from where your agent runs

## URL Security Configuration

Control which URLs can be accessed by remote file tools (`fetch_file`, `fetch_and_save`, `fetch_json`) and API tools to protect against Server-Side Request Forgery (SSRF) attacks.

```yaml
# =============================================================================
# URL Security Configuration (SSRF Protection)
# =============================================================================
url_security:
  enabled: true                      # Enable URL filtering (default: false)
  allow_localhost: false             # Allow localhost/127.0.0.1 (default: false)
  log_blocked_attempts: true         # Log blocked URL attempts (default: true)
  
  # Allow list for domains (supports wildcards)
  allow_domains:
    - "api.github.com"              # Exact domain
    - "*.example.com"               # Wildcard subdomain
    - "internal.corp"
  
  # Allow list for IP ranges (CIDR notation)
  allow_ips:
    - "203.0.113.0/24"              # Public IP range
    - "192.168.1.0/24"              # Private network (if needed)
```

### Security Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable URL filtering (disabled by default) |
| `allow_domains` | list | `[]` | Allowed domain patterns (supports `*` wildcards) |
| `allow_ips` | list | `[]` | Allowed IP ranges in CIDR notation |
| `allow_localhost` | bool | `false` | Allow localhost/127.0.0.1 access |
| `log_blocked_attempts` | bool | `true` | Log blocked URL attempts for auditing |

### How It Works

1. **Disabled by default**: URL security is off for backward compatibility
2. **Allow list approach**: Only explicitly allowed URLs can be accessed
3. **Domain wildcards**: Use `*.example.com` to allow all subdomains
4. **IP ranges**: Use CIDR notation like `192.168.1.0/24` for IP ranges
5. **Private IP protection**: Private IPs (RFC1918) are blocked unless in `allow_ips`
6. **Localhost control**: Localhost is blocked by default, enable with `allow_localhost: true`

### Example Use Cases

**Development Environment:**
```yaml
url_security:
  enabled: true
  allow_localhost: true              # Allow local APIs
  allow_domains:
    - "api.github.com"
    - "*.test.com"
```

**Production Environment:**
```yaml
url_security:
  enabled: true
  allow_localhost: false             # Block localhost
  log_blocked_attempts: true         # Audit blocked attempts
  allow_domains:
    - "api.github.com"
    - "*.example.com"
    - "docs.internal.corp"
  allow_ips:
    - "203.0.113.0/24"              # Only specific public ranges
```

**Strict Internal Environment:**
```yaml
url_security:
  enabled: true
  allow_domains:
    - "internal-api.company.com"    # Only internal APIs
  allow_ips:
    - "192.168.1.0/24"              # Only internal network
```

### Security Considerations

- **SSRF Protection**: Prevents agents from accessing internal services or cloud metadata endpoints
- **No deny list**: Only allow lists are supported (more secure approach)
- **No redirect validation**: Redirects are followed but not re-validated (future enhancement)
- **No DNS rebinding protection**: Domain-to-IP resolution is not validated (future enhancement)

**Best Practices:**
1. Always enable URL security in production
2. Use the most restrictive allow list possible
3. Monitor `log_blocked_attempts` for security incidents
4. Keep `allow_localhost: false` in production
5. Use specific domains instead of broad wildcards when possible

## Logging Configuration

MACSDK uses a two-channel output system: user feedback (stdout) and application logs (file).

```yaml
# =============================================================================
# Logging Configuration
# =============================================================================
log_level: INFO              # DEBUG, INFO, WARNING, ERROR
log_dir: ./logs              # Directory for log files
log_filename:                # Custom filename (default: auto with timestamp)

# Debug middleware settings (when --debug or debug: true)
debug_prompt_max_length: 10000   # Max chars per prompt in logs
debug_show_response: true        # Show model responses in debug
```

### Logging Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_level` | string | `INFO` | Minimum log level to capture |
| `log_dir` | path | `./logs` | Directory for log files |
| `log_filename` | string | auto | Custom filename (default: `{app}-YYYY-MM-DD-HH-MM-SS.log`) |
| `debug_prompt_max_length` | int | `10000` | Max characters per prompt in debug logs |
| `debug_show_response` | bool | `true` | Show model responses in debug mode |

### Logging Behavior

**CLI Chat Mode:**
- Logs written to `./logs/{app}-YYYY-MM-DD-HH-MM-SS.log` by default (one file per execution)
- stdout remains clean for user interaction
- Log file path displayed at startup

**Web Mode (Containers/K8s):**
- Logs written to stderr ONLY (12-factor app pattern)
- No file logging by default (better for container environments)
- File logging can be enabled explicitly if needed for VM deployments

### CLI Logging Options

```bash
# Verbose mode (DEBUG level)
my-chatbot chat -v

# Very verbose (DEBUG + show prompts in logs)
my-chatbot chat -vv

# Quiet mode (only warnings and errors)
my-chatbot chat -q

# Custom log file
my-chatbot chat --log-file ./debug.log

# Explicit log level
my-chatbot chat --log-level DEBUG
```

### Environment Variables for Logging

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Minimum log level | `INFO` |
| `LOG_DIR` | Log file directory | `./logs` |
| `LOG_FILENAME` | Custom log filename | auto-generated |
| `DEBUG_PROMPT_MAX_LENGTH` | Max chars in debug prompts | `10000` |
| `DEBUG_SHOW_RESPONSE` | Show LLM responses in debug | `true` |

### Best Practices

1. **Always log to file in CLI mode** - Keeps stdout clean for user interaction
2. **Use `-v` for debugging** - Shows detailed logs without polluting the UI
3. **Check logs for errors** - Application errors are logged to file, not stdout
4. **Increase `debug_prompt_max_length`** - Default 10000 chars, increase if prompts are cut off
5. **Use `--log-file` in production** - Specify explicit log location for monitoring

## Environment Variables

All configuration options can be set via environment variables:

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key (required) | - |
| `LLM_MODEL` | Model for responses | `gemini-3-flash-preview` |
| `LLM_TEMPERATURE` | Response creativity (0.0-1.0) | `0.3` |
| `LLM_REASONING_EFFORT` | Reasoning level | `medium` |

### Server Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_HOST` | Web server host | `0.0.0.0` |
| `SERVER_PORT` | Web server port | `8000` |
| `MESSAGE_MAX_LENGTH` | Max message length | `5000` |
| `WARMUP_TIMEOUT` | Startup timeout | `15.0` |

### Middleware Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `INCLUDE_DATETIME` | Include datetime context | `true` |
| `ENABLE_TODO` | **DEPRECATED** (always enabled) | `true` |
| `DEBUG` | Show prompts sent to LLM | `false` |
| `SUMMARIZATION_ENABLED` | Enable context summarization | `false` |
| `SUMMARIZATION_TRIGGER_TOKENS` | Token threshold for summarization | `100000` |
| `SUMMARIZATION_KEEP_MESSAGES` | Recent messages to preserve | `6` |

**Note:** `TodoListMiddleware` is deprecated in v0.6.0+. Task planning is now handled via Chain-of-Thought prompts. The `ENABLE_TODO` setting is deprecated and has no effect.

### Agent Execution

| Variable | Description | Default |
|----------|-------------|---------|
| `RECURSION_LIMIT` | Max agent iterations | `50` |
| `SUPERVISOR_TIMEOUT` | Supervisor execution timeout (includes specialist calls) | `120.0` |
| `SPECIALIST_TIMEOUT` | Specialist agent timeout (includes LLM + tools) | `90.0` |
| `FORMATTER_TIMEOUT` | Response formatting timeout | `30.0` |
| `LLM_REQUEST_TIMEOUT` | Individual LLM HTTP request timeout | `60.0` |

**Timeout Hierarchy:**
- `llm_request_timeout`: Lowest level - times out individual HTTP calls to the LLM API
- `specialist_timeout`: Mid level - times out entire specialist execution (multiple LLM calls + tool usage)
- `supervisor_timeout`: Highest level - times out supervisor orchestration (can include multiple specialist calls)
- `formatter_timeout`: Independent - times out response formatting (returns raw results if exceeded)

Adjust these values if you experience frequent timeouts with complex queries or slow network connections.

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
