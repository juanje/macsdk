# Project Context for AI Code Review

## Project Overview

**Purpose:** Provides a Python SDK for building, customizing, and orchestrating multi-agent chatbot systems with RAG support, web interfaces, and reusable API tools.
**Type:** Python library / SDK
**Domain:** Artificial Intelligence, Multi-Agent Systems, and LLM Orchestration
**Key Dependencies:** LangChain, LangGraph, FastAPI, httpx, ChromaDB (optional)

## Technology Stack

### Core Technologies
- **Primary Language:** Python 3.12+
- **Framework/Runtime:** FastAPI, LangChain, LangGraph
- **Architecture Pattern:** Asynchronous (FastAPI/httpx) & Agentic/RAG (LangGraph/ChromaDB)

### Key Dependencies (for Context7 & API Understanding)
- **langchain>=1.0.1 / langgraph>=1.0.0** - Critical for reviewing AI agent orchestration, state graphs, and LLM interaction logic. The supervisor uses LangGraph for workflow orchestration.
  - **IMPORTANT:** LangChain released version 1.0.0 in **October 2025**, moving from 0.3.x series. Current version in use: **1.1.2**
  - **NEW in 1.0+:** Native middleware system (human-in-the-loop, summarization, PII redaction). MACSDK previously used `TodoListMiddleware` but migrated to CoT prompts in v0.6.0+
  - LangChain 1.0 includes: `create_agent` abstraction, middleware system (built-in: human-in-the-loop, summarization, PII redaction), and support for custom middleware
  - If reviewing against older LangChain docs (0.3.x or earlier), note that middleware patterns and `create_agent()` signatures have changed significantly
- **langchain-google-genai>=2.0.0** - Default LLM provider integration with Google's Gemini models.
  - **Default Model:** `gemini-3-flash-preview` (latest Gemini Flash model as of January 2026)
- **pydantic>=2.0.0** - Enforces strict data validation and settings management using V2 syntax. All configuration and agent responses use Pydantic models.
- **fastapi>=0.115.0** - Powers the web interface with WebSocket support for real-time streaming of agent responses.
- **httpx>=0.27.0** - Async/sync HTTP client for API tools and RAG web crawler. Provides connection pooling, SSL certificate management, and HTTP/2 support.
- **chromadb>=0.4.0** - (Optional) Vector store for RAG implementations; used only when RAG features are enabled via `macsdk[rag]`.
- **beautifulsoup4>=4.12.0** - HTML parsing for RAG web crawler; used to extract content and links from crawled pages.
- **click>=8.0.0** - CLI framework for the `macsdk` scaffolding commands (new, add-agent, list).
- **jinja2>=3.0.0** - Template engine for project generation (chatbot/agent scaffolding).

### Development Tools & Quality Standards
- **Testing Framework:** pytest with pytest-asyncio for async tests (target: 90%+ coverage on core modules)
- **Code Quality:** ruff (linting/formatting), mypy with strict mode (`disallow_untyped_defs=true`)
- **Type Checking:** Full type annotations required on all functions; `from __future__ import annotations` in all modules
- **Async Testing:** All async functions must be tested with pytest-asyncio; external services (LLM, APIs) must be mocked

## Architecture & Code Organization

### Project Organization
```
macsdk/
├── src/macsdk/              # Core SDK package
│   ├── core/                # Core infrastructure (protocol, registry, config)
│   │   ├── protocol.py      # SpecialistAgent protocol definition
│   │   ├── registry.py      # Global agent registry
│   │   ├── graph.py         # LangGraph workflow builder
│   │   ├── state.py         # ChatbotState TypedDict
│   │   ├── config.py        # Configuration management (global singleton)
│   │   ├── llm.py           # LLM initialization
│   │   ├── api_registry.py  # API service registry
│   │   ├── cert_manager.py  # SSL certificate handling
│   │   └── url_security.py  # URL filtering & SSRF protection
│   │
│   ├── agents/              # Built-in agents (supervisor, formatter, RAG)
│   │   ├── supervisor/      # Supervisor agent (orchestrator)
│   │   │   ├── agent.py     # Supervisor implementation
│   │   │   └── prompts.py   # Supervisor prompts
│   │   ├── formatter/       # Response formatter agent
│   │   │   ├── agent.py     # Formatter implementation
│   │   │   └── prompts.py   # Composable formatter prompts
│   │   └── rag/             # RAG agent (ChromaDB + retrieval)
│   │       ├── agent.py     # RAGAgent implementation
│   │       ├── config.py    # RAG configuration
│   │       ├── indexer.py   # Document indexing & loading
│   │       ├── recursive_loader.py  # Custom httpx-based web crawler
│   │       ├── cache.py     # Document caching
│   │       ├── glossary.py  # Term glossary management
│   │       └── [other support modules]
│   │
│   ├── interfaces/          # User interfaces
│   │   ├── cli.py           # Rich-powered CLI interface
│   │   └── web/
│   │       └── server.py    # FastAPI + WebSocket server
│   │
│   ├── middleware/          # Cross-cutting concerns
│   │   ├── datetime_context.py  # Inject current datetime
│   │   ├── todo.py              # Task planning (DEPRECATED - now via CoT prompts)
│   │   ├── summarization.py     # Context compression
│   │   ├── debug_prompts.py     # Prompt debugging
│   │   └── tool_instructions.py # Auto-inject tool usage instructions
│   │
│   ├── tools/               # Reusable tools for agents
│   │   ├── api.py           # API interaction tools with URL security
│   │   ├── remote.py        # Remote file tools with redirect support
│   │   ├── calculate.py     # Safe math evaluation
│   │   └── knowledge/       # Skills & facts document tools
│   │
│   └── cli/                 # Scaffolding CLI
│       ├── main.py          # Entry point (macsdk command)
│       ├── commands/        # Subcommands (new, add-agent, list)
│       └── templates/       # Jinja2 templates
│           ├── agent/       # Agent project templates
│           ├── chatbot/     # Chatbot project templates
│           └── shared/      # Common templates
│
├── tests/
│   ├── unit/                # Unit tests (mocked externals)
│   │   ├── core/            # Core module tests
│   │   ├── cli/             # CLI command tests
│   │   └── middleware/      # Middleware tests
│   └── integration/         # Integration tests (real workflows)
│
├── examples/                # Working example projects
│   ├── multirepo/           # Independent agent packages
│   │   ├── api-agent/       # Example specialist agent
│   │   └── devops-chatbot/  # Example chatbot using agent
│   └── monorepo/            # Embedded agents in chatbot
│       └── devops-chatbot/  # Chatbot with local agents/
│
├── docs/                    # Documentation
│   ├── getting-started/     # Installation & quickstart
│   ├── guides/              # How-to guides
│   └── reference/           # API reference docs
│
└── pyproject.toml           # Package config + uv workspace
```

### Architecture Patterns
**Code Organization:** Modular SDK architecture with clear separation:
- `src/macsdk/core/` - Core infrastructure (protocol, registry, state, graph, config, LLM)
- `src/macsdk/agents/` - Built-in agents (supervisor orchestrator, RAG with ChromaDB)
- `src/macsdk/interfaces/` - User interfaces (CLI with Rich, Web with FastAPI/WebSocket)
- `src/macsdk/middleware/` - Cross-cutting concerns (datetime context, task planning, summarization, debug)
- `src/macsdk/tools/` - Reusable tools (API interactions, remote agents)
- `src/macsdk/cli/` - Scaffolding commands with Jinja2 templates

**Key Components:** 
- **SpecialistAgent Protocol:** Defines the contract all agents must implement (`name`, `capabilities`, `run()`, `as_tool()`). Enables type-safe agent registration.
- **AgentRegistry:** Singleton registry for dynamic agent discovery and tool conversion. Agents are registered at runtime and exposed as LangChain tools.
- **Supervisor Agent:** Central orchestrator using LangGraph to route queries. Dynamically builds prompts from registered agent capabilities.
- **Middleware Pipeline:** Wraps supervisor execution for datetime injection, task planning (LangChain 1.0+), context summarization, and prompt debugging.
- **State Management:** Uses `ChatbotState` (TypedDict) to track messages and workflow steps across LangGraph nodes.

**Entry Points:** 
- CLI: `macsdk new chatbot/agent` generates projects from templates
- Runtime: Generated chatbots use `create_graph()` to build LangGraph workflow, then `run_cli_chatbot()` or `run_web_server()` for interaction

### Important Files for Review Context
- **src/macsdk/core/protocol.py** - Defines the `SpecialistAgent` Protocol; the foundation of the entire agent system. All agents must implement this contract.
- **src/macsdk/core/registry.py** - Global agent registry for dynamic registration/discovery. Critical for understanding multi-agent orchestration.
- **src/macsdk/agents/supervisor/agent.py** - Supervisor agent implementation with dynamic prompt generation, middleware integration, and tool-based agent invocation.
- **src/macsdk/agents/supervisor/prompts.py** - Centralized supervisor prompts with CoT planning built-in, plus specialist planning prompt.
- **src/macsdk/core/graph.py** - LangGraph workflow construction; defines the supervisor→tool→supervisor routing loop.
- **src/macsdk/interfaces/cli.py** - CLI runtime loop with Rich formatting; shows state initialization and graph execution patterns.
- **src/macsdk/interfaces/web/server.py** - FastAPI/WebSocket server for real-time streaming; critical for async patterns.
- **src/macsdk/agents/rag/agent.py** - Built-in RAG agent implementation; demonstrates SpecialistAgent protocol usage and ChromaDB integration.
- **src/macsdk/agents/rag/indexer.py** - Document loading and indexing with parallel processing, supports HTML (web crawling) and Markdown sources.
- **src/macsdk/agents/rag/recursive_loader.py** - Custom httpx-based web crawler with connection pooling, progress callbacks, and SSL certificate support for RAG document ingestion.
- **src/macsdk/core/cert_manager.py** - SSL certificate management with download/caching of remote certificates and local path validation. Used by both API tools and RAG crawler.
- **src/macsdk/middleware/todo.py** - TodoListMiddleware (deprecated no-op); task planning now via CoT prompts in system messages.
- **src/macsdk/middleware/tool_instructions.py** - Auto-injects tool usage instructions based on detected tool patterns.
- **src/macsdk/prompts.py** - Re-exports supervisor prompts for backward compatibility. Actual prompts now in `agents/supervisor/prompts.py`.
- **src/macsdk/agents/__init__.py** - Implements lazy loading for RAGAgent using `__getattr__` with `TYPE_CHECKING` block for static analysis.
- **src/macsdk/tools/api.py** - API tools (`api_get`, `api_post`) with retry logic, JSONPath extraction, and certificate management.
- **src/macsdk/tools/calculate.py** - Safe math evaluator with DoS protection (factorial/pow limits, expression length).
- **src/macsdk/tools/knowledge/** - Skills/facts document tools with frontmatter parsing and path security.
- **src/macsdk/cli/commands/new.py** - Project scaffolding logic; generates chatbots/agents from Jinja2 templates.

### Development Conventions
- **Naming:** Standard Python conventions (snake_case for functions/variables, PascalCase for classes); internal helpers prefixed with underscore (e.g., `_build_supervisor_prompt`).
- **Module Structure:** Public APIs exposed via `__init__.py`; clear separation between framework (`src/macsdk`), examples (`examples/`), and tests (`tests/unit`, `tests/integration`).
- **Configuration:** Pydantic V2 `BaseModel` with `pydantic-settings` for env vars; YAML files loaded via `ChatbotConfig.from_yaml()` pattern.
- **Type Safety:** Strict mypy configuration (`disallow_untyped_defs=true`); extensive use of `typing.TYPE_CHECKING` blocks to avoid circular imports; `from __future__ import annotations` in all modules.
- **Async Patterns:** All I/O operations use `async`/`await`; agents implement `async def run()` for compatibility with LangGraph async execution.
- **Testing:** Unit tests mock LLM calls; integration tests use actual LangChain/LangGraph but with mocked external services (APIs, ChromaDB).
- **Templates:** Jinja2 templates in `src/macsdk/cli/templates/` generate complete project structures with proper imports and type hints.
- **Template Code Formatting:** Templates must generate code that passes ruff linting (88 char line limit). Long function calls should be split across multiple lines in the template itself.

### Logging Architecture

MACSDK uses a **two-channel output system**:

1. **User Channel** (stdout/WebSocket): Progress messages, chatbot responses
   - Use `log_progress()` from `macsdk.core.utils`
   - NEVER use `print()` or `logging.*` for user-facing output
   
2. **App Channel** (file/stderr): Technical logs, debug info
   - Use `logging.getLogger(__name__)`
   - CLI mode: logs to `./logs/*.log` (NEVER stdout)
   - Web mode: logs to stderr ONLY (no files in containers)

**Key Design Decisions:**
- `log_progress()` is for user feedback, NOT technical logging
- Debug prompts go to log file (not stdout) to preserve UX
- Default log directory is `./logs/` (CWD, not `~/.macsdk/`)
- Log level configurable via `config.yml`, ENV, or CLI flags (`-v`, `-vv`, `-q`, `--log-level`)
- `PromptDebugMiddleware` uses `logger.info()` (for user-requested visibility), never `print()`
- **Clean format for LLM logs**: `setup_logging(clean_llm_format=True)` configures the `macsdk.middleware.debug_prompts` logger with a clean formatter (`%(message)s`) and `propagate=False`
- **Agent context tracking**: Debug logs show which agent is making LLM calls (e.g., `[LLM [supervisor]]`, `[LLM [api-agent]]`)
- **Web mode disables file logging by default** (`log_to_file=False`) for 12-factor app compliance
- File logging in containers is discouraged; use stderr for log aggregation (K8s/OpenShift)

**Configuration:**
- `log_level`: Minimum level (DEBUG/INFO/WARNING/ERROR), default INFO
- `log_dir`: Directory for log files, default `./logs`
- `log_filename`: Custom filename (default auto-generated with date)
- `debug_prompt_max_length`: Max chars in debug prompts, default 10000
- `debug_show_response`: Show LLM responses in debug, default true

**CLI Options:**
- `-v`: DEBUG level
- `-vv`: DEBUG level + enable debug middleware (prompts to log)
- `-q`: WARNING level (quiet)
- `--debug`: Enable debug middleware
- `--log-level X`: Explicit level override
- `--log-file PATH`: Custom log file path

## Code Review Focus Areas

- **[Logging Channel Separation]** - Verify new code uses `log_progress()` for user feedback and `logging.*` for technical logs. NEVER use `print()` for either purpose. In CLI mode, check that stdout is reserved exclusively for user interaction (prompts and responses).

- **[Debug Middleware Output]** - In middleware that generates debugging information, ensure all output goes to `logger.debug()` or `logger.info()` - never to `print()` or `sys.stdout.write()`. Debug information should not pollute the user interface. The `PromptDebugMiddleware` uses `logger.info()` and relies on the logger configuration (set in `setup_logging`) for formatting. Never write directly to handler streams to avoid thread-safety issues.

- **[PromptDebugMiddleware - Development Only]** - The `PromptDebugMiddleware` logs **complete, unredacted content** including tool call arguments with sensitive data (API keys, tokens, passwords). This is intentional for debugging effectiveness. The middleware is **exclusively for local development** and should never be enabled in production, staging, or any environment with real credentials. Do NOT add sanitization logic - it adds complexity and false sense of security. If someone enables `--show-llm-calls` in production, that's a deployment/configuration error, not a code issue.

- **[CLI Startup Logging]** - Verify CLI commands call `setup_logging()` early in execution and display the log file path to the user (in CLI mode). The path should be shown in a subtle way (dimmed text) that doesn't disrupt the UI.

- **[Log Level Respect]** - Check that code respects `config.log_level` and doesn't hardcode log levels or bypass the configuration. CLI flags (`-v`, `-vv`, `-q`, `--log-level`) should properly override config values.

- **[SpecialistAgent Protocol Compliance]** - Verify all agent implementations correctly implement the `SpecialistAgent` protocol (name, capabilities, async run(), as_tool()). Check that `capabilities` descriptions are verbose and LLM-friendly for accurate routing.

- **[LangGraph State Management]** - In state transitions (`ChatbotState`), ensure `messages` list is appended (never replaced) and `workflow_step` is updated correctly. Verify the supervisor→tool→supervisor loop terminates properly without infinite routing.

- **[AgentRegistry Thread Safety]** - Review `src/macsdk/core/registry.py` for potential race conditions during agent registration in async contexts. The global singleton pattern may need protection if agents are registered after server startup.

- **[Supervisor Prompt Construction]** - In `src/macsdk/agents/supervisor/agent.py`, verify `get_all_capabilities()` returns deterministic, well-formatted agent descriptions. Middleware order is critical: DatetimeContext → ToolInstructions (if knowledge tools) → Summarization → Supervisor → DebugPrompts.

- **[Pydantic Field Descriptions]** - In `models.py` files, `Field(description=...)` strings are consumed by LLMs for tool/agent selection. Must be precise, actionable, and include examples where ambiguity exists.

- **[Async I/O Patterns]** - Check for blocking operations in async functions: file I/O in RAG indexing, synchronous HTTP calls in API tools, ChromaDB operations. All should use async equivalents or run in thread pools.

- **[API Tool Security]** - In `src/macsdk/tools/api.py`, review certificate validation logic (`verify` parameter), URL construction to prevent SSRF, and JSONPath extraction for injection risks. The `APIRegistry` should validate service configurations.

- **[URL Security & SSRF Protection]** - In `src/macsdk/core/url_security.py`, verify:
  - Domain allowlist uses strict suffix matching (not fnmatch - security risk)
  - IP allowlist accepts CIDR with `strict=False` (user-friendly)
  - Ambiguous IP formats are blocked (127.1, 0x7f000001, decimal notation)
  - Pydantic `AnyUrl` is used for robust URL parsing
  - `create_redirect_validator()` returns async callable for httpx event hooks
  - Localhost/private IP handling respects `allow_localhost` flag

- **[RAG Source Validation]** - In `src/macsdk/agents/rag/config.py`, verify path traversal protection for local markdown/file sources. URL validation for remote sources should prevent access to internal networks.

- **[SSL Certificate Management]** - In `src/macsdk/core/cert_manager.py`, ensure certificate downloads use proper validation (no blind SSL verification disabled). Check that `asyncio.run()` is only called from synchronous contexts (not from running event loops). Verify cache directory creation is thread-safe.

- **[HTTP Redirect Validation]** - In `src/macsdk/tools/remote.py` and `api.py`, verify:
  - `follow_redirects=True` is explicitly set on `httpx.AsyncClient`
  - `create_redirect_validator()` is used to validate redirect targets
  - Event hooks are properly attached (`event_hooks={"request": [validator]}`)
  - Redirects respect URL security policy (no redirect to blocked domains/IPs)

- **[Web Crawler Security]** - In `src/macsdk/agents/rag/recursive_loader.py`, verify domain validation prevents crawling external sites (strict netloc comparison). Check Content-Type filtering to prevent parsing binary files. Ensure recursion depth limits prevent infinite loops. Verify URL normalization prevents duplicate crawling.

- **[Template Generation Security]** - In `src/macsdk/cli/commands/new.py`, ensure Jinja2 templates don't allow arbitrary code execution. Validate project names to prevent directory traversal during scaffolding.

- **[WebSocket Error Handling]** - In `src/macsdk/interfaces/web/server.py`, verify proper cleanup of WebSocket connections on error, especially during streaming LLM responses. Check for memory leaks in long-running sessions.

## Library Documentation & Best Practices

### SpecialistAgent Protocol Pattern

The core architectural pattern is the **SpecialistAgent Protocol** defined in `src/macsdk/core/protocol.py`:

```python
@runtime_checkable
class SpecialistAgent(Protocol):
    name: str  # Unique identifier
    capabilities: str  # LLM-readable description for routing
    
    async def run(self, query: str, context: dict | None = None) -> dict:
        # Returns: {"response": str, "agent_name": str, "tools_used": list, ...}
        ...
    
    def as_tool(self) -> BaseTool:
        # Wraps agent as LangChain tool for supervisor
        ...
```

**Key Principles:**
1. **Protocol-based, not inheritance-based** - Agents don't need to inherit from a base class; they just need to implement the protocol methods.
2. **CAPABILITIES as Single Source of Truth** - The `CAPABILITIES` constant serves dual purpose: it's used by the supervisor for routing AND as the agent's base `SYSTEM_PROMPT`. This eliminates duplication and ensures alignment.
3. **Agents as Tools** - The `as_tool()` method wraps the agent for LangGraph tool invocation, enabling the supervisor to call agents like function tools.
4. **Context dict pattern** - Agents receive optional context (conversation history, config) via dict parameter rather than constructor injection.
5. **Extensibility via Skills/Facts** - Agents can be extended with domain knowledge through skills (step-by-step instructions) and facts (reference data) without modifying core code.

### LangGraph State Pattern

The framework uses **TypedDict-based state** for LangGraph workflows:

```python
class ChatbotState(TypedDict):
    messages: list[BaseMessage]  # Conversation history
    workflow_step: str  # Current step (supervisor/formatter/end)
    agent_results: str  # Raw results from supervisor before formatting
```

**Best Practices:**
- Always append to `messages`, never replace
- Use `workflow_step` to control flow (supervisor → formatter → end)
- `agent_results` stores raw output from supervisor for formatter processing
- Middleware wraps state transitions, not individual nodes

### Configuration Pattern

All configuration uses **Pydantic Settings with env var priority**:

```python
from macsdk.core import EnvPrioritySettingsMixin, MACSDKConfig

class MyConfig(EnvPrioritySettingsMixin, BaseSettings):
    # Or simply inherit from MACSDKConfig (already includes mixin)
    api_timeout: int = Field(default=30, gt=0)
```

**Key Points:**
- `EnvPrioritySettingsMixin`: Ensures env vars override config.yml (not vice versa)
- `MACSDKConfig`: Base class for chatbots/agents, includes the mixin
- `RAGConfig`: Separate config with `RAG_` prefix, also uses the mixin
- Use `Field()` validators for runtime validation

**Global Config vs RunnableConfig (Architecture Decision):**

The SDK uses **two distinct configuration mechanisms** for different purposes:

1. **Global Config Singleton** (`macsdk.core.config.config`)
   - **Purpose:** Application-wide settings (security, debug mode, model defaults)
   - **Scope:** Entire application lifetime, shared across all executions
   - **Access:** Direct import `from macsdk.core.config import config`
   - **Examples:** `url_security`, `debug`, `llm_model`, `api_registry`
   - **Lazy Loading:** Loads `config.yml` from CWD on first attribute access (prevents import-time errors)

2. **RunnableConfig** (LangChain/LangGraph)
   - **Purpose:** Execution-specific settings (callbacks, streaming, tracing)
   - **Scope:** Single agent/graph invocation
   - **Access:** Via `InjectedToolArg` or middleware
   - **Examples:** `callbacks`, `run_id`, `metadata`, LangSmith tracing

**Rationale (KISS Principle):**
- **Application config should be global** - No reason to pass security settings, model defaults, or debug flags through every function call
- **Execution config should be local** - Callbacks, streaming functions, and tracing are specific to each request
- **Simpler architecture** - Tools don't need `InjectedToolArg`, just import global config
- **Easier testing** - Mock the global config singleton, not propagation through RunnableConfig

**For reviewers:** Do NOT suggest passing application-level config (like `url_security`) via `RunnableConfig`. That's architectural complexity without benefit.

### Configuration Error Handling ("Fail Closed" Strategy)

The SDK implements a **"Fail Closed"** security strategy for configuration errors:

**Behavior:**
- **Invalid `config.yml` (syntax or validation errors):** Raises `ConfigurationError` with clean, user-friendly message (no Python traceback)
- **Missing `config.yml`:** Silently uses default values (safe fallback)
- **Import-time safety:** Global config uses lazy loading via `_ConfigProxy` to prevent crashes during module import

**Rationale:**
- **Security:** Invalid config could disable security features (e.g., typo in `url_security`). Crashing is safer than running with unknown state.
- **Fail Fast:** Applications should know immediately if configuration is broken, not fail later in production.
- **User Experience:** Clean error messages guide users to fix the problem without developer-level tracebacks.

**Implementation Details:**
```python
# src/macsdk/core/config.py
def _create_default_config() -> MACSDKConfig:
    """Create default config with fail-closed error handling."""
    try:
        config_path = Path.cwd() / "config.yml"
        if config_path.exists():
            return create_config()  # Raises ConfigurationError if invalid
        return MACSDKConfig()  # Safe defaults if no config file
    except ConfigurationError:
        raise  # Propagate clean error message
```

**Lazy Loading Pattern:**
```python
# Global config is lazy-loaded to prevent import-time errors
class _ConfigProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(_get_config(), name)

config = _ConfigProxy()  # Loads on first attribute access
```

**Interface Lazy Loading:**
```python
# src/macsdk/interfaces/__init__.py uses __getattr__ for lazy imports
def __getattr__(name: str) -> Any:
    if name == "run_cli_chatbot":
        from .cli import run_cli_chatbot
        return run_cli_chatbot
    # ... prevents config access during import
```

**Error Message Format:**
```
Configuration validation failed in config.yml:
  - url_security.enabled: Input should be a valid boolean
  - url_security.ennabled: Extra inputs are not permitted

Please fix the errors in config.yml and restart the application.
```

**For reviewers:** 
- Do NOT suggest "fail open" (silent fallback to defaults) for invalid config files
- Do NOT suggest showing Python tracebacks for config errors (user-facing issue)
- The lazy loading pattern prevents import-time crashes while maintaining fail-closed semantics

### Generated Project Configuration (Design Decisions)

Generated chatbots and agents include a `config.py` that extends `MACSDKConfig` using Pydantic Settings:

```python
from pydantic_settings import SettingsConfigDict
from macsdk.core import MACSDKConfig

class MyAgentConfig(MACSDKConfig):
    api_token: SecretStr | None = None  # Secrets
    api_base_url: HttpUrl | None = None  # Validated URLs
    api_timeout: int = 30  # Simple values
```

**Design Decisions (DO NOT flag these as issues):**

1. **`pydantic-settings` is a transitive dependency** - Generated projects do NOT need to explicitly add `pydantic-settings` to their `pyproject.toml`. It is a **direct dependency of `macsdk`** (see line 28 of root `pyproject.toml`), so it's always available.

2. **`env_file=".env"` only searches CWD** - Unlike `load_dotenv()` which searches parent directories, Pydantic Settings only reads `.env` from the current working directory. This is intentional and follows 12-factor app conventions. Users run CLIs from project root.

3. **Global instantiation `config = ...Config()`** - The config object is instantiated at module import time. This is "fail-fast" by design: if required fields are missing, the app fails immediately at startup rather than later in production. All example fields in templates use `| None = None` to avoid crashes in fresh environments.

4. **`extra="ignore"` in generated configs** - Generated project configs use `extra="ignore"` to prevent loading random environment variables. This overrides `MACSDKConfig`'s `extra="allow"` (which is for internal SDK extension) and is intentional.

5. **No `load_dotenv()` needed** - Pydantic Settings with `env_file=".env"` handles `.env` loading automatically. The `python-dotenv` dependency was removed intentionally.

**Security Best Practices (documented in templates):**
- Use `SecretStr` for tokens/credentials (prevents exposure in logs/repr)
- Use `HttpUrl` for URL validation
- Templates include commented examples of all patterns

### Middleware Pattern

Middleware wraps the supervisor invocation for cross-cutting concerns:

```python
class DatetimeContextMiddleware(AgentMiddleware):
    def before_invoke(self, state: ChatbotState) -> ChatbotState:
        # Inject current datetime into system message
        return state
    
    def after_invoke(self, state: ChatbotState, response: dict) -> dict:
        # Post-process response
        return response
```

**Middleware Execution Order:**
1. DatetimeContext - injects temporal context
2. ToolInstructions (if knowledge tools present) - injects usage instructions and knowledge inventory
3. Summarization - compresses old messages if context too large
4. Supervisor - main LLM routing
5. DebugPrompts - logs final prompt for debugging

**Note**: Order matters. Summarization MUST run before supervisor to prevent context window overflow. TodoListMiddleware is deprecated (no-op).

### Task Planning via Chain-of-Thought Prompts (v0.6.0+)

**TodoListMiddleware is DEPRECATED** - Task planning is now handled via specialized prompts integrated into system messages:

**Supervisor Planning:**
- Planning principles built into `SUPERVISOR_PROMPT`
- Emphasizes parallel tool calls, complete investigations
- No separate planning prompt needed

**Specialist Planning:**
```python
# In agent.py - CAPABILITIES serves as SYSTEM_PROMPT
from macsdk.agents.supervisor import SPECIALIST_PLANNING_PROMPT

CAPABILITIES = """Your agent description here..."""
SYSTEM_PROMPT = CAPABILITIES  # Single source of truth

# Planning prompt is appended by run_agent_with_tools() or manually
full_prompt = SYSTEM_PROMPT + "\n\n" + SPECIALIST_PLANNING_PROMPT
```

**Backward Compatibility:**
- `TodoListMiddleware` still exists but is a no-op with deprecation warning
- `TODO_PLANNING_SPECIALIST_PROMPT` is an alias for `SPECIALIST_PLANNING_PROMPT`
- Old code works but issues warnings

**Important for review:**
- Don't suggest using `TodoListMiddleware` - it's deprecated
- Planning is now via prompts, not middleware
- Agent creation functions return `Any` (agent only), not tuples
- System prompt passed to `create_agent(system_prompt=...)`, not `run_agent_with_tools()`
- **Specialist agents no longer have `prompts.py`** - `CAPABILITIES` in `agent.py` is the single source of truth

## Code Review Checklist

When reviewing changes to this project, verify:

### Type Safety & Code Quality
- [ ] All functions have complete type annotations (args + return type)
- [ ] `from __future__ import annotations` present in modified modules
- [ ] No mypy errors in strict mode (`disallow_untyped_defs=true`)
- [ ] Ruff linting passes (line length 100, imports sorted)
- [ ] No bare `except:` clauses; use specific exception types

**Pydantic Type Coercion Style:**
When using Pydantic types like `HttpUrl`, `SecretStr`, etc., prefer explicit instantiation
over relying on Pydantic's automatic coercion. This keeps mypy happy without `# type: ignore`.

```python
# ✅ Preferred: Explicit instantiation
config = APIServiceConfig(name="test", base_url=HttpUrl("https://api.example.com"))

# ❌ Avoid: Relying on coercion with type ignore
config = APIServiceConfig(name="test", base_url="https://...")  # type: ignore[arg-type]
```

This applies to both production code and tests. Explicit is better than implicit.

### Testing Requirements
- [ ] New features have unit tests (90%+ coverage target)
- [ ] Async functions tested with pytest-asyncio
- [ ] LLM calls are mocked (no real API calls in tests)
- [ ] External services (APIs, ChromaDB) are mocked in unit tests
- [ ] Integration tests added for multi-component changes

### Protocol & Architecture Compliance
- [ ] New agents implement `SpecialistAgent` protocol correctly
- [ ] Agent `capabilities` descriptions are LLM-friendly (verbose, actionable)
- [ ] State mutations append to `messages`, never replace
- [ ] Middleware respects execution order (Datetime→ToolInstructions(optional)→Summarization→Supervisor→Debug)
- [ ] Configuration uses Pydantic V2 `BaseModel` with validators
- [ ] Configuration errors raise `ConfigurationError` (not generic exceptions or sys.exit())

### Documentation & Style
- [ ] Docstrings use Google style (Args, Returns, Raises sections)
- [ ] Pydantic `Field(description=...)` strings are clear (consumed by LLMs)
- [ ] Module-level docstrings explain purpose
- [ ] Public APIs exposed via `__init__.py`
- [ ] Comments explain "why", not "what"

### Security Considerations
- [ ] No path traversal vulnerabilities in file operations
- [ ] URL security enabled and properly configured (allowlists for domains/IPs)
- [ ] Domain wildcards use strict suffix matching (not fnmatch)
- [ ] Ambiguous IP formats are blocked (decimal notation, hex, shorthands)
- [ ] HTTP redirects validated via httpx event hooks
- [ ] Certificate validation explicitly configured (not blindly disabled)
- [ ] Jinja2 templates don't allow arbitrary code execution
- [ ] User inputs validated before use in shell commands or file paths
- [ ] Configuration errors fail closed (raise ConfigurationError) not fail open (silent defaults)



---
<!-- MANUAL SECTIONS - DO NOT MODIFY THIS LINE -->
<!-- The sections below will be preserved during updates -->

## Common Review False Positives (Do NOT Flag These)

### TodoListMiddleware Deprecation (v0.6.0+)

**False Positive:** "Should use `TodoListMiddleware` for task planning"

**Reality:** `TodoListMiddleware` is **deprecated** as of v0.6.0. Task planning is now handled via Chain-of-Thought (CoT) prompts integrated directly into system messages.

**Current Approach:**
- **Supervisor:** Planning principles built into `SUPERVISOR_PROMPT` (no separate prompt)
- **Specialists:** Append `SPECIALIST_PLANNING_PROMPT` to system prompt
- **Backward compatibility:** `TODO_PLANNING_SPECIALIST_PROMPT` is an alias for `SPECIALIST_PLANNING_PROMPT`

**Why the Change:**
- LLMs (especially Gemini) often ignored explicit planning tags
- Internal CoT planning is more natural and efficient
- Better caching with static prompts vs dynamic state
- Simpler agent reasoning without tag management

**Evidence:** `src/macsdk/middleware/todo.py` (now a deprecated no-op), `src/macsdk/agents/supervisor/prompts.py`

---

### Middleware Request Modification (v0.6.0+)

**Pattern:**
```python
# In DatetimeContextMiddleware
def _inject_datetime_context(self, request: "ModelRequest") -> None:
    request.system_message = SystemMessage(content=new_content)
```

**False Positive:** "Modifying `request.system_message` might not work if it's immutable/frozen"

**Reality:** 
- Uses LangChain 1.0+ official API: `wrap_model_call(request, handler)` and `awrap_model_call(request, handler)`
- These hooks are specifically designed for request modification
- Verified working in production with 325+ passing tests
- Alternative (`before_model`) doesn't have access to configured system_message

**Evidence:** `src/macsdk/middleware/datetime_context.py`

---

### DateTime Context Caching Without Lock

**Pattern:**
```python
def _get_cached_context(self) -> str:
    # Race condition possible: _cached_context and _cache_time updated non-atomically
    if self._cached_context is None or (now - self._cache_time).total_seconds() > self._cache_ttl:
        self._cached_context = format_datetime_context(now)
        self._cache_time = now
    return self._cached_context
```

**False Positive:** "Should use `threading.Lock` to prevent race conditions"

**Reality:**
- **Intentional design** - Race condition is acknowledged and documented in code comments
- Operation is **idempotent** (same input = same output)
- `format_datetime_context()` is **cheap** (simple string formatting, ~1ms)
- Worst case: redundant string generation (not corruption)
- Adding lock would add complexity without measurable benefit

**When to add lock:** Only if `format_datetime_context()` becomes expensive (e.g., external API call)

**Evidence:** `src/macsdk/middleware/datetime_context.py` (documented rationale in code comments)

---

### Timestamp Refresh in Multi-Turn Conversations

**Pattern:**
```python
# In _inject_datetime_context and before_model
if DATETIME_CONTEXT_HEADER in content:
    # Strip old context and inject fresh
    content = content.split(DATETIME_CONTEXT_HEADER)[0].strip()
```

**False Positive:** "Datetime context is duplicated / should skip if already present"

**Reality:**
- **Intentional behavior change** (v0.6.0)
- Old behavior: Skip injection if header present → stale timestamps in long conversations
- New behavior: Remove old context, inject fresh → always current timestamp
- Critical for chatbots with persistent state (LangGraph multi-turn conversations)

**Evidence:** `src/macsdk/middleware/datetime_context.py`, test: `test_datetime_context.py::test_refreshes_stale_datetime_context`

---

### Internal vs Public APIs

**Pattern:**
```python
# src/macsdk/agents/supervisor/agent.py
def create_supervisor_agent(include_datetime=None, debug=None):
    # No enable_todo parameter
```

**False Positive:** "Removing `enable_todo` parameter is a breaking change"

**Reality:**
- `create_supervisor_agent()` is an **internal SDK function**
- Users don't call it directly - it's called by `create_graph()` internally
- Public API for users: `macsdk new chatbot` (CLI scaffolding)
- No external consumers exist

**Evidence:** 
- No usage in `examples/` directory
- Function not exported in public `__init__.py`
- Only called from `src/macsdk/core/graph.py` (internal)

---

### Deprecated Config Fields

**Pattern:**
```python
# src/macsdk/core/config.py
enable_todo: bool = Field(
    default=True,
    deprecated=True,
    description="DEPRECATED: TODO middleware is always enabled."
)
```

**False Positive:** "Removing `enable_todo` breaks backward compatibility"

**Reality:**
- Field is **NOT removed**, it's **deprecated** with `Field(deprecated=True)`
- Old YAML files with `enable_todo: true` still load without error
- Pydantic's `extra='allow'` ensures no crashes
- Migration guide (`docs/guides/migration-v0.6.md`) documents the change

**Evidence:** `src/macsdk/core/config.py`

---

### DatetimeContextMiddleware Content Stripping

**False Positive:** "Using `split(HEADER)[0]` loses content if middleware appends after datetime context"

**Reality:** Safe with current middleware. Uses HTML comment delimiters (`<!-- macsdk:datetime:start/end -->`) with regex for robust block detection.

**Evidence:** `src/macsdk/middleware/datetime_context.py`

---

### DatetimeContextMiddleware Modes

**False Positive:** "DatetimeContextMiddleware injects unnecessary temporal context into specialist agents"

**Reality:**
- Middleware has two modes: `minimal` (default, ~15 tokens) and `full` (~500 tokens)
- **Minimal mode**: Only current date - for specialist agents that need timestamp interpretation
- **Full mode**: Complete context with pre-calculated dates + routing instructions - for supervisors
- Full mode automatically includes instructions on passing concrete dates to specialists
- Default changed to minimal for 90%+ token reduction in typical workflows

**Pattern:**
```python
# Specialist agents (default) - minimal context
middleware.append(DatetimeContextMiddleware())

# Supervisor agents (explicit) - full context with instructions
middleware.append(DatetimeContextMiddleware(mode="full"))
```

**Evidence:** `src/macsdk/middleware/datetime_context.py`, `src/macsdk/agents/supervisor/agent.py`

**Do NOT suggest:** Using full mode for specialists, removing datetime context entirely, or manually adding temporal routing instructions to supervisor prompts.

---

### XML Tags in Prompts - Gemini Behavior

**False Positive:** "Should use XML tags like `<datetime>` for better structure"

**Reality:** XML tags cause Gemini to be more "planful" — adding extra `write_todos` calls and consulting more skills/facts before acting. This increases step count and can hit recursion limits.

HTML comments (`<!-- -->`) are ignored by LLMs, providing robust delimiters for code without affecting agent behavior.

**Evidence:** Empirical testing with same queries: XML=fail (50+ steps), HTML=pass (~10 steps)

---

### Tool Name Matching in ToolInstructionsMiddleware

**False Positive:** "Hardcoded tool names are tightly coupled. Use metadata/attributes instead."

**Reality:** Tool names (`read_skill`, `read_fact`) are public API contract. Name matching is intentional KISS design. The middleware pre-injects knowledge inventory into the system prompt. Do NOT suggest metadata approach.

**Evidence:** `src/macsdk/middleware/tool_instructions.py`

---

### Package Resources Without as_file()

**False Positive:** "Should use `importlib.resources.as_file()` for zip-safe compatibility"

**Reality:** Tools create closures needing persistent paths. `as_file()` context exits before tool use. Documented limitation. Do NOT suggest `as_file()`.

**Evidence:** `src/macsdk/tools/knowledge/__init__.py`

---

### Knowledge Bundle Dual Calls

**False Positive:** "Calling `get_knowledge_bundle()` twice is inefficient/duplicative"

**Reality:** Intentional. `get_knowledge_bundle(__package__)` called separately in `tools.py` (for tools) and `agent.py` (for middleware). Enables lazy initialization and CLI visibility. Lightweight operation (just creates instances). Do NOT suggest caching in global variable or wrapper functions.

---

### Knowledge Inventory Synchronous I/O

**False Positive:** "Synchronous file I/O in `ToolInstructionsMiddleware.__init__` blocks the event loop"

**Reality:** Middleware instantiated **once at agent creation** during startup, not per-request. File reading happens before application serves requests. Typical: 10-20 files, <10ms. Not in hot path.

**Evidence:** `src/macsdk/cli/templates/agent/agent.py.j2`, `src/macsdk/tools/knowledge/__init__.py`

---

### Knowledge Inventory Size Limits

**False Positive:** "Unbounded inventory injection will exhaust context window"

**Reality:** Typical usage 10-50 items (~50-100 tokens each), well within 128K+ context limits. Example project: 11 items. Future: could warn if >100 items, but not critical.

**Evidence:** `examples/agent-with-knowledge/`

---

### Knowledge Tools Breaking Change (v0.7.0)

**False Positive:** "`list_skills`/`list_facts` removal breaks backward compatibility"

**Reality:** Intentional optimization. Eliminates redundant LLM discovery calls by pre-injecting inventory into prompt. Reduces latency and tokens. All code/tests/docs updated.

**Evidence:** `PROPOSAL_KNOWLEDGE_INVENTORY.md`

---

### Progressive Disclosure for Skills/Facts

**False Positive:** "Skills/facts in subdirectories are not listed in the inventory"

**Reality:** Intentional design pattern. `_list_documents()` uses `glob("*.md")` (not `rglob`) to list only top-level documents. This implements progressive disclosure:

1. **Top-level documents** are listed in the inventory (injected into system prompt)
2. **Sub-documents** (in subdirectories) are accessed on-demand via `read_skill`/`read_fact`
3. **Top-level documents link to sub-documents** in their content

**Benefits:**
- Reduces initial prompt size (only high-level skills/facts shown)
- Agent reads generic skill first, then specific sub-skills if needed
- Better context management for complex knowledge hierarchies

**Pattern:**
```
skills/
├── deployment.md          # Listed in inventory, links to sub-skills
├── deployment/
│   ├── kubernetes.md      # Accessed via read_skill("deployment/kubernetes.md")
│   └── openshift.md       # Accessed via read_skill("deployment/openshift.md")
└── monitoring.md          # Listed in inventory
```

**Evidence:** `src/macsdk/tools/knowledge/helpers.py`, `docs/guides/using-knowledge-tools.md`

---

### Calculate Tool DoS Limits

**False Positive:** "Limits too restrictive (factorial max 100, pow max ±1000)"

**Reality:** Security boundaries. `factorial(100)` = 9.3e157 already. Legitimate use fits. Do NOT suggest increasing without justification.

**Evidence:** `src/macsdk/tools/calculate.py`

---

### Path Traversal with is_relative_to()

**False Positive:** "Use `str.startswith()` for path validation instead of `is_relative_to()`"

**Reality:** `is_relative_to()` prevents bypass attacks (e.g., symlinks). `str.startswith()` is vulnerable. Always use `Path.is_relative_to()`.

**Evidence:** `src/macsdk/tools/knowledge/helpers.py`

---

### Specialist Agents Architecture (Tools, Not Nodes)

**False Positive:** "`supervisor_timeout` only covers planning, not specialist execution. Specialists run in separate LangGraph tool nodes."

**Reality:**
- Specialist agents are **LangChain tools** (BaseTool), not LangGraph nodes
- Graph: `START → supervisor → formatter → END` (only 2 nodes)
- Specialists execute **inside** `supervisor.ainvoke()` as synchronous tool calls
- `supervisor_timeout` wraps the entire `ainvoke()`, including all tool/specialist executions

**Pattern:**
```python
async with asyncio.timeout(config.supervisor_timeout):
    result = await supervisor.ainvoke(...)  # Tools execute here, not after
```

**Not standard LangGraph** (supervisor_node → tool_node → supervisor_node). This project uses agents-as-tools pattern.

**Evidence:** `src/macsdk/core/graph.py` (2 nodes), `src/macsdk/agents/supervisor/agent.py:71,108` (tools=agent_tools)

**Do NOT suggest:** Moving timeout to graph.invoke() or renaming to `supervisor_planning_timeout`.

---

## Business Logic & Implementation Decisions

### Built-in Agents Architecture

Built-in agents (supervisor, formatter, RAG) are now organized under `src/macsdk/agents/` subdirectories:
- **Supervisor** (`agents/supervisor/`): Central orchestrator, routes queries to specialist agents
- **Formatter** (`agents/formatter/`): Response synthesizer, formats raw agent results into polished responses
- **RAG** (`agents/rag/`): Document Q&A with ChromaDB (optional dependencies)

**Key Design Decisions:**
- **Separation of Concerns**: Supervisor focuses on orchestration, Formatter on presentation
- **Composable Prompts**: Formatter prompt split into CORE/TONE/FORMAT/EXTRA for selective customization
- **Conversation History Strategy**: Only formatted responses (not raw `agent_results`) are appended to `messages`
  * Rationale: Avoids context bloat from duplicate information (raw + formatted)
  * Trade-off: If formatter omits specific details (IDs, numbers), they're not in message history
  * Mitigation: Supervisor can re-invoke agents in future turns if specific data is needed
  * This prioritizes conversation history readability and token efficiency over raw data persistence
- **Lazy Loading for RAG**: Uses `__getattr__` to avoid loading `langchain_community` and `chromadb` at import time
- **TYPE_CHECKING Block**: Ensures RAGAgent is visible to mypy/IDEs while maintaining runtime lazy behavior
- **`__dir__` Implementation**: Enables RAGAgent to appear in `dir()` and IDE autocompletion
- **Backward Compatibility**: Re-exports in `core/__init__.py` and `prompts.py` maintain existing import paths
- **Built-in Agent Prompts**: Supervisor and formatter have `prompts.py` for composable prompts
- **Specialist Agent Simplification**: Generated specialist agents use `CAPABILITIES = SYSTEM_PROMPT` pattern (no separate `prompts.py`)

**Graph Flow:**
```
START → supervisor_node → formatter_node → END
        (orchestration)    (presentation)
```

**Review Focus:**
- Verify imports use re-exports (`from macsdk.core import supervisor_agent_node`) or direct paths
- Check lazy loading doesn't break at runtime due to missing optional dependencies
- Ensure `TYPE_CHECKING` imports don't create circular dependencies
- Verify `agent_results` field is properly initialized in all state creation points

### Specialist Agent Architecture (CAPABILITIES = SYSTEM_PROMPT)

**For reviewers:** Specialist agents use `SYSTEM_PROMPT = CAPABILITIES` pattern. This is intentional:
- No separate `prompts.py` for specialists (only supervisor/formatter have one)
- `CAPABILITIES` serves dual purpose: supervisor routing + agent system prompt
- Domain knowledge added via skills/facts, not prompt files

**Do NOT suggest:** Creating `prompts.py` for specialist agents, separating CAPABILITIES from SYSTEM_PROMPT.

---

### Protocol-Based Architecture (not Inheritance)

The framework uses **Protocol** (`SpecialistAgent`) instead of base class inheritance. This decision:
- Allows agents to be developed independently without SDK coupling
- Enables structural subtyping (duck typing with type safety)
- Supports runtime protocol checking with `@runtime_checkable`
- Avoids diamond inheritance problems in multi-agent scenarios

### Agents as LangChain Tools

Specialist agents are exposed as LangChain `BaseTool` instances via the `as_tool()` method. This design:
- Leverages LangChain's native tool-calling mechanism
- Allows the LLM to decide when to invoke agents vs respond directly
- Enables tool use metadata (which agents were called, tool traces)
- Simplifies integration with LangGraph's tool-calling nodes

**Important:** The supervisor never calls agent methods directly; it always uses LangChain's tool invocation.

### Tool Docstrings Are Intentionally Generic

Agent tools use minimal docstrings ("Query this specialist agent..."). This is **correct by design**:
- Routing uses `CAPABILITIES` in the supervisor prompt, not tool docstrings
- Avoids duplication/desync between docstring and capabilities
- Validated empirically; LLMs route correctly

**Do not flag generic tool docstrings as issues.**

### Response Field Mapping

`BaseAgentResponse.response_text` → `result["response"]` mapping happens in `run_agent_with_tools()`. Tool wrappers correctly access `result["response"]`. **Do not flag as inconsistent.**

### Agent Code Never Instantiates Response Models

**Do not flag "missing AgentResponse field updates" in agent.py files.**

Agents do NOT manually instantiate `AgentResponse(field=value, ...)`. The flow is:
1. `create_agent(..., response_format=AgentResponse)` passes the class to LangChain
2. LangChain's structured output mechanism generates and validates the response
3. `run_agent_with_tools()` extracts fields from the model

Changing `models.py` fields requires NO changes to `agent.py` because the agent code never constructs the response object directly.

### Dynamic Prompt Construction

The supervisor's system prompt is built at runtime by querying the `AgentRegistry` for all registered agents' `capabilities` strings. This means:
- Agent registration order can affect LLM routing (though it shouldn't in theory)
- `capabilities` strings must be stable and deterministic
- Changes to registered agents require supervisor recreation (happens per request)

### State Append-Only Pattern

The `ChatbotState.messages` list follows an **append-only** pattern:
- Messages are ALWAYS appended, never replaced or removed (except by middleware)
- Middleware (e.g., `SummarizationMiddleware`) can compress old messages
- This ensures conversation history integrity for debugging and LLM context

**Anti-pattern to watch for:** Code that reassigns `state["messages"] = [new_msg]` instead of appending.

### Middleware Execution Order

Middleware wraps the supervisor invocation (formatter runs after supervisor in graph):
1. **DatetimeContext** - injects current datetime
2. **ToolInstructions** (if knowledge tools present) - injects usage instructions
3. **Summarization** - compresses old messages if too large
4. **Supervisor** - LLM invocation with tools
5. **DebugPrompts** (if enabled) - logs final prompt

**Critical:** 
- Summarization MUST run before supervisor to prevent context window overflow
- TodoListMiddleware is deprecated - task planning now via CoT prompts

### Task Planning Design Decisions (Chain-of-Thought - v0.6.0+)

**Chain-of-Thought (CoT) Planning:**
- Task planning now via specialized prompts in system messages
- TodoListMiddleware deprecated (no-op with warning)
- More efficient - LLMs naturally plan internally without explicit tags

**Supervisor Planning:**
- Planning principles integrated directly into `SUPERVISOR_PROMPT`
- Emphasizes parallel execution, complete investigations
- Uses imperative language ("MUST", "ALWAYS")
- No separate planning prompt needed

**Specialist Planning:**
- `SPECIALIST_PLANNING_PROMPT` appended to specialist system prompts
- Promotes efficient execution, minimal LLM calls
- Encourages parallelization and internal planning
- Backward compatible via `TODO_PLANNING_SPECIALIST_PROMPT` alias

**Why the Change:**
- LLMs (especially Gemini) often ignored explicit planning tags
- Internal planning is more natural and efficient
- Reduces complexity in agent reasoning
- Better caching (static prompts vs dynamic state)

**Function signatures (v0.6.0+):**
- Agent creation functions return `Any` (agent only)
- System prompt passed to `create_agent()`, not `run_agent_with_tools()`
- Backward compatibility: `run_agent_with_tools()` accepts deprecated `system_prompt` param with warning

### Lazy Model Initialization

The LLM model (`get_answer_model()`) is initialized lazily to avoid loading at import time. This design:
- Allows configuration to be loaded first (env vars, YAML)
- Supports testing without real API keys
- Enables different models per request (future feature)

**Review focus:** Check that model initialization happens after config is loaded.

### Custom Web Crawler (SimpleRecursiveLoader)

The RAG indexer uses a custom `httpx`-based web crawler for document ingestion. Key design features:
- **Connection Pooling**: Single `httpx.Client` instance per crawl for HTTP Keep-Alive and SSL session reuse, reducing overhead (N connections use 1 TCP/SSL handshake instead of N)
- **Progress Tracking**: Protocol-based callback system reports progress per crawled page for granular user feedback
- **Security**: Strict domain validation and Content-Type filtering

**Implementation Details:**
- Recursion depth: Default `max_depth=2` to prevent stack overflow and excessive crawling
- Domain validation: Strict `netloc` comparison prevents crawling external sites (e.g., `site.com` won't match `site.com.evil.com`)
- URL normalization: Removes trailing slashes and fragments to prevent duplicate crawling
- Content-Type filtering: Skips binary files (PDFs, images) before parsing with BeautifulSoup
- Thread-safe: Runs in `ThreadPoolExecutor` for parallel document loading

**Review focus:** Verify recursion limits are respected, domain validation is strict, and Content-Type filtering prevents binary content parsing.

### SSL Certificate Management

The `core.cert_manager` provides centralized SSL certificate handling for both API tools and RAG crawler:
- **Remote Certificates**: Downloads from URLs, validates PEM format, caches locally with per-URL locking to prevent race conditions
- **Local Certificates**: Validates file existence using non-blocking I/O (`asyncio.to_thread`)
- **Cache Management**: SHA256-based filenames in `~/.cache/macsdk/certs/`
- **httpx Integration**: Direct certificate path support without modifying global SSL context

**Review focus:** Ensure `asyncio.run()` in `_resolve_cert_path()` is only called from `ThreadPoolExecutor` contexts (not from running event loops). Verify certificate downloads validate PEM format before caching.

## Domain-Specific Context

### Terminology

- **Supervisor**: The central orchestrator agent that routes queries to specialist agents. Uses LangChain's `create_agent()` with tools.
- **Specialist Agent**: An agent that implements the `SpecialistAgent` protocol. Handles a specific domain (e.g., API monitoring, documentation Q&A).
- **Capabilities**: Human-readable description of what an agent can do. This string is injected into the supervisor's prompt and is critical for LLM routing decisions.
- **Agent-as-Tool**: Pattern where agents are wrapped as LangChain `BaseTool` instances and invoked by the supervisor via tool calls.
- **Workflow Step**: State tracking field (`"supervisor"`, `"complete"`, `"error"`) used to manage LangGraph execution flow.
- **RAG Agent**: Built-in specialist agent for documentation Q&A using ChromaDB vector store and retrieval-augmented generation.

### Key State Fields

```python
ChatbotState:
    messages: list[BaseMessage]  # Conversation history (append-only)
    user_query: str              # Current user input
    chatbot_response: str        # Final response to user
    workflow_step: str           # Current execution phase
```

**Important:** `messages` contains the full conversation history including both user and AI messages. The `user_query` is the current query being processed.

### Runtime Requirements

- **Google Gemini API**: Requires `GOOGLE_API_KEY` environment variable
- **ChromaDB**: Optional for RAG features; uses local filesystem persistence (no external service required)

### Configuration Sources

Configuration is loaded from multiple sources (priority order):
1. Environment variables (highest priority)
2. `.env` file
3. `config.yml` (via `create_config()` or `load_rag_config()`)
4. Pydantic field defaults (lowest priority)

This order is enforced by `EnvPrioritySettingsMixin`, which both `MACSDKConfig` and `RAGConfig` inherit. Env vars can always override config files, enabling easy deployment customization.

**Pydantic Settings V2 Priority Order (for reviewers):**
In `settings_customise_sources`, the **first element has highest priority** (not the last).
This is documented in Pydantic: "Sources returned first take the most precedence."
Our implementation is correct:
```python
return (env_settings, dotenv_settings, init_settings, ...)  # env wins
```
**Do not flag this as inverted logic.**

## Special Cases & Edge Handling

### Structured vs String Message Content

LLM responses can have two content formats:
```python
# String format (most common)
content = "Hello, how can I help?"

# Structured format (some models)
content = [
    {"type": "text", "text": "Hello"},
    {"type": "text", "text": "how can I help?"}
]
```

The `_extract_text_content()` helper in `agents/supervisor/agent.py` handles both formats.

**Review focus:** Ensure new code that processes `message.content` uses this helper or handles both formats.

### Recursion Limit Errors

The supervisor can recursively call tools (agents), which can themselves use tools. To prevent infinite loops:
- Default recursion limit: configured via `config.recursion_limit` (typical: 50)
- LangGraph raises `RecursionError` when limit exceeded
- Supervisor catches and returns user-friendly error: "The request required too many steps..."

**Isolated Counters (v0.6.0+):**
Specialist agents have independent recursion limits. In `run_agent_with_tools()`:
- `recursion_limit` is reset to `config.recursion_limit` (not inherited from supervisor)
- `metadata.langgraph_step` is cleared (counter starts at 0)

Without this, specialist steps would count against the supervisor's limit, causing premature errors.

**Review focus:** Changes that add tool-calling logic should consider recursion depth.

### Context Window Management

When conversation history grows too large:
- `SummarizationMiddleware` triggers at `config.summarization_trigger_tokens` (e.g., 20,000 tokens)
- Keeps last N messages (`config.summarization_keep_messages`) and summarizes older ones
- Summary is injected as a system message

**Edge case:** Very long single messages can still exceed context window. Currently not handled.

### Empty or Malformed Agent Registry

If no agents are registered when the supervisor runs:
- The supervisor still functions but has no tools
- LLM responds directly to all queries (no specialist routing)
- `get_all_capabilities()` returns empty dict
- Prompt includes empty agent capabilities section

**Review focus:** Ensure new agent registration code handles initialization order correctly.

### Rate Limiting and API Errors

The supervisor catches common API errors and provides specific messages:
- `"rate"` or `"quota"` in error → "API rate limit reached..."
- `"timeout"` or `"deadline"` → "Request took too long..."
- `"recursion"` or `"maximum"` → "Too many steps..."

**Review focus:** New API integration code should raise descriptive exceptions that these handlers can categorize.

### WebSocket Connection Cleanup

The web interface (`server.py`) streams responses via WebSocket. Edge cases:
- Client disconnects during streaming → connection error caught, cleanup happens
- Supervisor error during streaming → error message sent before close
- Multiple concurrent clients → each has isolated state and LangGraph execution

**Review focus:** Async cleanup in exception handlers, especially for long-running LLM streams.

### Jinja2 Template Security

Project scaffolding uses Jinja2 templates. Security considerations:
- Templates do NOT have access to arbitrary Python functions
- Project names are validated (alphanumeric + hyphens/underscores only)
- No user-provided template content is evaluated

**Review focus:** New template code should never use `eval()`, `exec()`, or allow arbitrary user input in template context.

## Additional Context

### Security Model

**Threat Boundaries:**
- **Trusted:** Code in `src/macsdk` and user's chatbot project
- **Untrusted:** User queries, RAG source URLs, API responses, external agent responses
- **Semi-trusted:** Configuration files (YAML), environment variables

**Key Security Considerations:**

1. **Path Traversal (RAG Sources)**
   - Local file sources must validate paths don't escape intended directories
   - Use `Path.resolve()` to normalize paths before file operations

2. **SSRF (API Tools & Remote File Tools)**
   - **URL Security Module** (`url_security.py`) provides configurable allowlist-based filtering
   - **Domain Allowlist:** Supports exact matches and wildcard subdomains (*.example.com)
   - **IP Allowlist:** Supports individual IPs and CIDR ranges (192.168.1.0/24)
   - **Ambiguous IP Protection:** Blocks decimal notation (2130706433), hex (0x7f000001), and IP shorthands (127.1)
   - **Redirect Validation:** HTTP redirects are validated via httpx event hooks
   - **Deny-all Policy:** When `enabled=True` with empty allowlists, blocks all requests
   - **Localhost Control:** Configurable via `allow_localhost` flag
   - Tools affected: `api_get`, `api_post`, `api_put`, `api_delete`, `api_patch`, `fetch_file`, `fetch_and_save`, `fetch_json`
   - **Configuration:** Via `url_security` section in `config.yml` (global singleton pattern)

3. **Certificate Validation**
   - Custom SSL certs supported via `CertificateManager`
   - Default behavior: verify=True (system trust store)
   - Custom certs: explicitly provided paths, not disabled verification

4. **LLM Prompt Injection**
   - User queries are passed directly to LLM (by design)
   - System prompts are constructed from `capabilities` strings (trusted)
   - Agent responses are trusted (assumed to be controlled by developer)

5. **Formatter Agent - Simple Text Separators**
   - The formatter agent uses simple text separators (Markdown headers) to structure prompts
   - User input and agent results are injected directly without escaping/sanitization
   - This is intentional because the formatter has:
     * No tools (cannot execute actions)
     * No access to sensitive data
     * No external system access
     * Only formats text for display
   - Worst case "injection": Poorly formatted response (cosmetic issue only)
   - Text separators are clear and don't require escaping external content
   - XML tags are useful in templates but not when injecting untrusted content
   - Sanitizing would be security theater - no actual risk to mitigate
   - **For reviewers:** Do NOT suggest escaping/sanitizing formatter inputs unless you can demonstrate actual harm beyond "user sees weird formatting"

### Performance Considerations

**Blocking Operations:**
- ChromaDB operations are synchronous (not async) - run in thread pool when needed
- RAG document indexing runs in `ThreadPoolExecutor` for parallel source loading
- `SimpleRecursiveLoader` uses synchronous `httpx.Client` with connection pooling for efficient HTTP reuse
- Certificate downloads use `asyncio.to_thread` to avoid blocking event loop

**Memory Usage:**
- Conversation history grows unbounded until summarization triggers
- ChromaDB index stored on disk (can be large for many documents)
- Each WebSocket connection has isolated state (memory multiplied by concurrent users)
- `SimpleRecursiveLoader` uses URL deduplication (visited set) to prevent memory exhaustion on cyclic links

**Performance Optimizations:**
- RAG web crawler: Connection pooling eliminates N-1 TCP/SSL handshakes (e.g., 100 pages = 1 handshake instead of 100)
- Certificate downloads: Per-URL locking prevents duplicate concurrent downloads
- URL normalization: Prevents duplicate crawling of same page with different URL formats

### Testing Philosophy

**Unit Tests:**
- Mock all external services (LLM, APIs, ChromaDB)
- Use `pytest-asyncio` for async test functions
- Focus on protocol compliance and state transitions
- **Important:** Tests that create supervisor/agents must mock `get_answer_model()` to avoid requiring API keys
- Use `# type: ignore[call-arg]` for Pydantic models with `extra="allow"` and dynamic fields

**Integration Tests:**
- Use real LangChain/LangGraph (complex to mock correctly)
- Mock only the LLM responses (use fixtures)
- Test end-to-end workflows (user query → supervisor → agent → response)

**Coverage Targets:**
- Core modules (`src/macsdk/core`): 90%+ required
- Agents, middleware, tools: 80%+ target
- CLI commands, interfaces: 70%+ acceptable
- Example projects: no coverage requirement

### Workspace Structure (uv)

The project uses `uv` workspace feature:
- Root: `macsdk` SDK package
- Members: example projects in `examples/multirepo/` and `examples/monorepo/`
- Workspace members reference `macsdk` via `{ workspace = true }`

**Review focus:** Changes to `pyproject.toml` should maintain workspace member references.

### Dynamic Agent Configuration (Pydantic `extra="allow"`)

The `MACSDKConfig` class uses Pydantic's `extra="allow"` setting to support agent-specific configuration:

```python
model_config = SettingsConfigDict(
    extra="allow",  # Allow custom config fields
)
```

**Purpose:**
- Enables passing arbitrary agent configurations: `api_agent={"enable_todo": True}`
- Agents can read their specific config via: `getattr(config, "agent_name", {})`
- Supports hierarchical configuration: global settings + agent-specific overrides

**For Review:**
- Dynamic fields like `api_agent={}` in config will show mypy errors: `Unexpected keyword argument`
- This is EXPECTED behavior; use `# type: ignore[call-arg]` on these lines
- The configuration works at runtime due to Pydantic's `extra="allow"`
- Tests in `tests/unit/core/test_agent_specific_config.py` verify this pattern

**Pattern:**
```python
# In agent code:
agent_config = getattr(config, "my_agent", {})
enable_todo = agent_config.get("enable_todo", False)  # Agent-specific default
```

**Agent naming guarantee:**
- All `agent_slug` values are guaranteed to be valid Python identifiers
- Generated via `slugify()` in `src/macsdk/cli/utils.py` (converts hyphens/spaces to underscores, lowercase, removes invalid chars)
- This ensures `getattr(config, "agent_slug")` works correctly for dynamic agent configuration
- Templates use `{{ agent_slug }}` which is always a valid identifier

### Deprecation Handling

LangChain/LangGraph are rapidly evolving:
- `pytest.ini` suppresses known deprecation warnings from LangChain
- `mypy` ignores missing stubs for LangChain modules
- Code should target latest stable versions (1.0+) of LangChain ecosystem

**IMPORTANT - LangChain 1.0+ Breaking Changes (October 2025):**
- LangChain moved from 0.3.x to 1.0.0 with significant API changes
- New middleware system: `langchain.agents.middleware` module introduced in 1.0.0
- Built-in middleware: human-in-the-loop, summarization, PII redaction, and support for custom middleware
- MACSDK previously used `TodoListMiddleware` but migrated to CoT prompts in v0.6.0+
- Agent creation with `create_agent()` now supports middleware parameter natively

**IMPORTANT - LangChain Version Context:**
- Current version in use: **1.1.2** (stable, Oct-Nov 2025)
- **NEW in 1.0+:** Native middleware system for agent enhancements
- **NEW in 1.1+:** Model profiles (`.profile` attribute), `ModelRetryMiddleware`, smarter summarization
- `langchain-google-genai`: Currently `>=2.0.0` (v4.0.0 available with breaking changes)

**Review focus:**
- New LangChain usage should follow 1.0+ patterns, not 0.3.x patterns
- Middleware patterns are fundamentally different between 0.3.x and 1.0+
- If reviewing against older LangChain docs (pre-1.0), be aware of breaking changes