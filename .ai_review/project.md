# Project Context for AI Code Review

## Project Overview

**Purpose:** Python SDK for building and orchestrating multi-agent chatbot systems with RAG support, web interfaces, and reusable API tools.
**Type:** Python library / SDK (v0.11.2)
**Domain:** AI, Multi-Agent Systems, LLM Orchestration
**Key Dependencies:** LangChain 1.0+ (orchestration), LangGraph (workflow), FastAPI (web), ChromaDB (optional RAG)

## Technology Stack & Versions (as of 2026-04-23)

- **Python** 3.12+ | **Build:** hatchling | **Package manager:** uv (workspace)
- **langchain>=1.0.1** / **langgraph>=1.0.0** — LangChain 1.0.0 released Oct 2025 (from 0.3.x). Current: **1.1.2**. Do NOT suggest 0.3.x patterns or pre-1.0 `create_agent()` signatures.
- **langchain-google-genai>=2.0.0** — Default LLM: `gemini-3-flash-preview` | Default embedding: `gemini-embedding-001`
- **pydantic>=2.0.0** / **pydantic-settings>=2.0.0** — V2 syntax only
- **fastapi>=0.115.0** — WebSocket streaming | **httpx>=0.27.0** — All HTTP (sync + async)
- **chromadb>=0.4.0** — Optional (`macsdk[rag]`) | **beautifulsoup4>=4.12.0** — RAG web crawler
- **click>=8.0.0** / **jinja2>=3.0.0** — CLI scaffolding | **simpleeval>=1.0.0** — Safe math
- **Linting:** ruff >=0.14.1 (line-length **88**) | **Types:** mypy >=1.18.2 strict
- `from __future__ import annotations` required in all modules

## Architecture & Code Organization

```
src/macsdk/
├── core/           # Protocol, registry, config (global singleton), state, graph, url_security
├── agents/         # supervisor/ (orchestrator + prompts.py), formatter/ (+ prompts.py), rag/ (optional)
├── interfaces/     # cli.py (Rich), web/server.py (FastAPI/WebSocket)
├── middleware/      # datetime_context, summarization, tool_instructions, debug_prompts
├── tools/          # api, remote, calculate, knowledge (skills/facts)
└── cli/            # Scaffolding: `macsdk new chatbot/agent` with Jinja2 templates
```

### Key Patterns

- **SpecialistAgent Protocol** (`core/protocol.py`): Protocol-based, not inheritance. Agents implement `name`, `capabilities`, `async run()`, `as_tool()`.
- **Agents as Tools**: Specialists wrapped as LangChain `BaseTool` via `as_tool()`. Supervisor invokes via tool-calling, never directly.
- **2-Node Graph**: `START → supervisor_node → formatter_node → END`. Specialists execute INSIDE supervisor as tool calls, not as separate nodes.
- **CAPABILITIES = SYSTEM_PROMPT**: For specialists, `CAPABILITIES` is single source of truth for routing AND system prompt. No separate `prompts.py` (only supervisor/formatter have one).
- **Global Config Singleton** (`core/config.py`): Lazy-loaded proxy. Do NOT suggest `RunnableConfig` for app-level settings.
- **Two-Channel Output**: `log_progress()` for user feedback, `logging.*` for technical logs. Never `print()`.
- **Middleware Order**: DatetimeContext → ToolInstructions (if knowledge tools) → Summarization → Supervisor → DebugPrompts. Summarization MUST run before supervisor.
- **State Append-Only**: `ChatbotState.messages` must be appended to, never replaced.

## Review Guidance

### What Reviewers Must Know

- **LangChain 1.0+ only**: Do NOT suggest 0.3.x patterns or old middleware. Current: 1.1.2.
- **TodoListMiddleware is deprecated (v0.6.0+)**: Task planning now via CoT prompts in system messages. Don't suggest using it.
- **Config errors fail closed**: Invalid `config.yml` raises `ConfigurationError`. Do NOT suggest fail-open or Python tracebacks.
- **Pydantic explicit instantiation**: Prefer `HttpUrl("https://...")` over relying on coercion with `# type: ignore`.
- **`supervisor_timeout` covers everything**: Wraps entire `ainvoke()` including all tool/specialist executions. Not just planning.
- **URL security uses strict suffix matching**: Not fnmatch. Ambiguous IP formats (decimal, hex, shorthands) blocked. Redirects validated via httpx event hooks.
- **WebSocket uses `safe_send_json()`**: Checks `WebSocketState.CONNECTED` before sending. Streams explicitly closed via `aclose()` on all error paths. `/health` exposes `active_connections`.
- **`PromptDebugMiddleware` logs unredacted content**: Intentional for local dev. Do NOT add sanitization.
- **Pydantic Settings priority**: In `settings_customise_sources`, first element = highest priority. `(env_settings, dotenv_settings, init_settings, ...)` is correct — env wins. Not inverted.
- **`extra="allow"` on `MACSDKConfig`**: Supports dynamic agent-specific config. `# type: ignore[call-arg]` on dynamic fields is expected.
- **`extra="ignore"` on generated configs**: Overrides SDK's `extra="allow"` intentionally.
- **`pydantic-settings` is transitive dep**: Generated projects don't need it in their `pyproject.toml`.
- **No `load_dotenv()` needed**: Pydantic Settings handles `.env` loading. `env_file=".env"` only searches CWD (intentional, 12-factor).
- **`_extract_text_content()` helper**: LLM responses can be string or structured `[{"type": "text", ...}]`. New code processing `message.content` must handle both.

---
<!-- MANUAL SECTIONS - DO NOT MODIFY THIS LINE -->

## Do NOT Flag (Known False Positives)

### Middleware Request Modification
Modifying `request.system_message` in `DatetimeContextMiddleware` uses LangChain 1.0+ official `wrap_model_call`/`awrap_model_call` API. Not immutable. Verified in 325+ tests.

### DateTime Cache Without Lock
Race condition in `_get_cached_context()` is intentional. Idempotent operation, ~1ms cost. Worst case: redundant string generation.

### Timestamp Refresh in Multi-Turn
Old datetime context is stripped and re-injected fresh each turn. Intentional (v0.6.0) — prevents stale timestamps in long conversations.

### DatetimeContextMiddleware Modes
Two modes: `minimal` (default, ~15 tokens) for specialists; `full` (~500 tokens) for supervisor. Don't suggest full mode for specialists or removing datetime context.

### DatetimeContextMiddleware Content Stripping
`split(HEADER)[0]` is safe. Uses HTML comment delimiters with regex for robust block detection.

### XML Tags in Prompts — Gemini
XML tags cause Gemini to be overly "planful" (50+ steps vs ~10). HTML comments (`<!-- -->`) used as delimiters instead.

### Internal vs Public APIs
`create_supervisor_agent()` is internal (not exported, only called from `core/graph.py`). Removing parameters is not a breaking change.

### Deprecated Config Fields
`enable_todo` uses `Field(deprecated=True)`, not removed. Old YAML files still load without error.

### Tool Name Matching in ToolInstructionsMiddleware
Hardcoded tool names (`read_skill`, `read_fact`) are public API contract. KISS design, not tight coupling.

### Package Resources Without as_file()
Tools create closures needing persistent paths. `as_file()` context exits before tool use. Do NOT suggest `as_file()`.

### SDK Tools Auto-Detection
`get_sdk_tools(__package__)` auto-includes `calculate` (always) and `read_skill`/`read_fact` (if `.md` files exist in `skills/`/`facts/`). Don't suggest manual imports.

### SDK Tools Double get_knowledge_bundle
Called twice (tools + middleware) at startup only. <10ms. Not worth caching.

### Knowledge Inventory Synchronous I/O
Middleware instantiated once at startup, not per-request. 10-20 files, <10ms. Not blocking event loop.

### Knowledge Inventory Size
Typical 10-50 items. Well within 128K+ context limits. Not unbounded risk.

### Knowledge Tools Breaking Change (v0.7.0)
`list_skills`/`list_facts` removal was intentional. Pre-injects inventory into prompt instead.

### Progressive Disclosure for Skills/Facts
`_list_documents()` uses `glob("*.md")` not `rglob`. Top-level docs in inventory, sub-docs accessed on-demand via `read_skill`/`read_fact`. Intentional.

### Knowledge Tools Flag Removed (v0.7.0+)
No `--with-knowledge` flag. All agents include `skills/`/`facts/` dirs with `.gitkeep`. Auto-detected.

### Example Markdown Files in skills/facts
No example `.md` files in generated dirs. Would auto-trigger knowledge tools with placeholder content.

### Calculate Tool DoS Limits
`factorial(100)` = 9.3e157. Limits are security boundaries. Don't increase without justification.

### Path Traversal Protection
Uses `Path.is_relative_to()`, not `str.startswith()`. Prevents symlink bypass. Don't suggest `startswith()`.

### API Service Registration
Lazy registration via `_ensure_api_registered()` with global flag in `get_tools()`. No import-time side effects.

### Specialist Agents Are Tools, Not Nodes
Graph: `START → supervisor → formatter → END` (2 nodes only). Specialists execute inside `supervisor.ainvoke()`. `supervisor_timeout` wraps entire invocation. Don't suggest moving timeout to `graph.invoke()`.

### Tool Docstrings Are Generic
Routing uses `CAPABILITIES` in supervisor prompt, not tool docstrings. Validated empirically. Don't flag generic docstrings.

### Response Field Mapping
`BaseAgentResponse.response_text` → `result["response"]` mapping in `run_agent_with_tools()`. Not inconsistent.

### Agent Code Never Instantiates Response Models
LangChain structured output generates responses. Changing `models.py` fields requires NO changes to `agent.py`.

### Formatter Input Sanitization
Formatter has no tools, no data access, no external access. Worst case: weird formatting. Don't suggest escaping/sanitization.

## Architecture & Design Decisions

### CAPABILITIES Pattern
`CAPABILITIES` serves dual purpose: supervisor routing AND agent system prompt. Optional `EXTENDED_INSTRUCTIONS` for critical per-request instructions NOT sent to supervisor (keeps routing prompt concise). Use for domain rules, API handling. NOT for reference docs (use Facts) or procedures (use Skills).

### Config Architecture
- **Global singleton**: App settings (security, debug, models). Import directly from `macsdk.core.config`.
- **RunnableConfig**: Execution-specific only (callbacks, streaming, tracing).
- **Fail-closed**: Invalid YAML raises `ConfigurationError` with user-friendly message. Missing YAML uses safe defaults.
- **Lazy loading**: `_ConfigProxy` prevents import-time crashes. Loads on first attribute access.

### Conversation History
Only formatted responses (not raw `agent_results`) appended to `messages`. Avoids context bloat. Trade-off: formatter-omitted details not in history.

### Isolated Recursion Counters (v0.6.0+)
Specialist agents get independent recursion limits in `run_agent_with_tools()`. Without this, specialist steps count against supervisor's limit.

### Task Planning (CoT, v0.6.0+)
Via prompts in system messages. `TodoListMiddleware` is deprecated no-op. `SPECIALIST_PLANNING_PROMPT` appended to specialist prompts. `TODO_PLANNING_SPECIALIST_PROMPT` is alias. Agent creation returns `Any` (agent only). System prompt passed to `create_agent()`, not `run_agent_with_tools()`.

## Domain-Specific Context

### Terminology
- **Supervisor**: Central orchestrator routing queries to specialists via tool calls
- **Specialist Agent**: Implements `SpecialistAgent` protocol for a specific domain
- **Capabilities**: LLM-readable description for routing, injected into supervisor prompt
- **Agent-as-Tool**: Agents wrapped as LangChain `BaseTool` via `as_tool()`

### Key State Fields
```python
ChatbotState:
    messages: list[BaseMessage]  # Append-only conversation history
    user_query: str              # Current user input
    chatbot_response: str        # Final response
    workflow_step: str           # Current execution phase
    agent_results: str           # Raw supervisor output for formatter
```

### URL Security (`core/url_security.py`)
- Domain allowlist: strict suffix matching (not fnmatch — security risk)
- IP allowlist: CIDR with `strict=False`; ambiguous formats blocked (decimal, hex, shorthands)
- Redirect validation: `create_redirect_validator()` returns async callable for httpx event hooks
- Deny-all when `enabled=True` with empty allowlists
- Affects: `api_get`, `api_post`, `api_put`, `api_delete`, `api_patch`, `fetch_file`, `fetch_and_save`, `fetch_json`

### SSL Certificates (`core/cert_manager.py`)
Remote certs downloaded, PEM-validated, cached in `~/.cache/macsdk/certs/` with per-URL locking. `asyncio.run()` in `_resolve_cert_path()` only from `ThreadPoolExecutor` contexts.

### RAG Web Crawler (`agents/rag/recursive_loader.py`)
Custom `httpx.Client` with connection pooling. Strict `netloc` domain validation. Content-Type filtering skips binary. `glob("*.md")` not `rglob` for progressive disclosure.
