# Middleware Reference

MACSDK includes middleware components that enhance agent capabilities automatically.

## Available Middleware

| Middleware | Purpose | Default |
|------------|---------|---------|
| `DatetimeContextMiddleware` | Injects current date/time and pre-calculated date references | Enabled |
| `TodoListMiddleware` | **DEPRECATED** - Task planning now via CoT prompts | N/A |
| `ToolInstructionsMiddleware` | Auto-injects usage instructions for knowledge tools | Optional |
| `SummarizationMiddleware` | Summarizes long conversations to stay within token limits | Disabled |
| `PromptDebugMiddleware` | Displays prompts sent to the LLM for debugging | Disabled |

## DatetimeContextMiddleware

Injects temporal context into prompts, helping agents interpret timestamps, logs, and relative date expressions.

The middleware supports two modes optimized for different agent types:

| Mode | Token Cost | Best For | Contains |
|------|------------|----------|----------|
| `minimal` | ~15 tokens | **Specialist agents** (default) | Current date only |
| `full` | ~500 tokens | **Supervisor agents** | Current date + pre-calculated ranges |

### Configuration

```yaml
# config.yml
include_datetime: true  # default: true
```

### What It Provides

**Minimal mode** (default for specialists):

```
**Current date**: Friday, January 09, 2026 (2026-01-09T19:55:00Z)
```

**Full mode** (for supervisors):

When enabled with `mode="full"`, agents receive this complete context:

```
## Current DateTime Context

**Now:**
- Current UTC time: 2025-12-14 19:32:59 UTC
- Current date: Sunday, December 14, 2025
- ISO format: 2025-12-14T19:32:59+00:00

**Pre-calculated dates for API queries (ISO 8601 format):**
| Reference | Date | Use for |
|-----------|------|---------|
| Yesterday | 2025-12-13T00:00:00Z | "yesterday" queries |
| Last 24 hours | 2025-12-13T19:32:59Z | "last 24 hours", "today" |
| Last 7 days | 2025-12-07T00:00:00Z | "last week", "past 7 days" |
| Last 30 days | 2025-11-14T00:00:00Z | "last month", "past 30 days" |
| Start of this week | 2025-12-08T00:00:00Z | "this week" (Monday) |
| Start of this month | 2025-12-01T00:00:00Z | "this month" |
| Start of last month | 2025-11-01T00:00:00Z | "last month" (calendar) |

**Phrase interpretation:**
- "last 7 days" / "past week" → use 2025-12-07T00:00:00Z
- "this week" → use 2025-12-08T00:00:00Z
- "last month" (relative) → use 2025-11-14T00:00:00Z
- "last month" (calendar) → use 2025-11-01T00:00:00Z
```

### How It Works

The datetime context is injected **at the end** of the system prompt before each LLM call. This placement:
- Enables optimal LLM caching (Gemini caches system message prefixes)
- Refreshes timestamps automatically in multi-turn conversations
- Ensures agents always have current time information

### Benefits

- **No prompt boilerplate**: Agents don't need to explain date calculations
- **Consistent format**: All dates in ISO 8601, ready for API queries
- **Accurate context**: Current time is refreshed on each LLM call
- **Pre-calculated ranges**: Common date ranges ready to use
- **Optimized for caching**: Placement maximizes LLM provider caching efficiency

### Mode Selection

**When to use `minimal` (default):**
- Specialist agents that receive pre-processed queries from supervisor
- Agents that need timestamp interpretation but not temporal query translation
- Token efficiency is important (99% of agents)

**When to use `full`:**
- Supervisor agents that interpret user queries with temporal references
- Agents that need to translate "last week" → concrete ISO dates
- First point of contact for user queries

### Usage Examples

**Specialist agent (minimal mode - default):**
```python
from macsdk.middleware import DatetimeContextMiddleware

middleware = [
    DatetimeContextMiddleware()  # Uses minimal mode by default
]
```

**Supervisor agent (full mode):**
```python
from macsdk.middleware import DatetimeContextMiddleware

middleware = [
    DatetimeContextMiddleware(mode="full")  # Includes pre-calculated dates
]
```

**Programmatic usage:**
```python
from macsdk.middleware import (
    format_minimal_datetime_context,
    format_datetime_context,
)

# Get minimal context string
minimal = format_minimal_datetime_context()

# Get full context string  
full = format_datetime_context()
```

### Architecture Pattern

In supervisor/specialist architectures:

1. **Supervisor** uses `mode="full"` to interpret user queries like "failed pipelines from last week"
2. **Supervisor** translates temporal references to concrete dates: "since 2026-01-02T00:00:00Z"
3. **Specialists** use `mode="minimal"` to interpret timestamps in logs/API responses
4. **Result**: 90%+ reduction in datetime context tokens across the system

### Example Use Case

**User query**: "Show me failed pipelines from last week"

**Supervisor** (with full mode):
- Sees pre-calculated `Last 7 days: 2026-01-02T00:00:00Z`
- Routes to specialist: `"failed pipelines since 2026-01-02T00:00:00Z"`

**Specialist** (with minimal mode):
- Receives concrete date from supervisor
- Uses minimal context to interpret log timestamps
- No need for date range calculations

## TodoListMiddleware (DEPRECATED)

**⚠️ DEPRECATED in v0.6.0+**: This middleware is now a no-op and issues a deprecation warning. Task planning is now handled via Chain-of-Thought (CoT) prompts integrated directly into agent system messages.

### Migration

**Old approach (deprecated):**
```python
from macsdk.middleware import TodoListMiddleware

middleware = [TodoListMiddleware(enabled=True)]  # Now deprecated
```

**New approach (recommended):**

Task planning is now automatic via specialized prompts:

**For Supervisor Agents:**
- Planning principles are integrated into `SUPERVISOR_PROMPT`
- No separate planning prompt needed
- Focuses on tool routing and parallel execution

**For Specialist Agents:**
```python
from macsdk.agents.supervisor import SPECIALIST_PLANNING_PROMPT

system_prompt = BASE_PROMPT + "\n\n" + SPECIALIST_PLANNING_PROMPT
```

### Why the Change?

The tag-based middleware approach had several issues:
- Added complexity to the agent's reasoning
- LLMs (especially Gemini) often ignored the explicit tags
- Extra overhead for planning that could be done naturally
- Internal planning is more efficient than visible tag-based planning

### Chain-of-Thought Planning

Agents now use internal Chain-of-Thought planning guided by prompt instructions:

**Supervisor** (`SUPERVISOR_PROMPT`):
- Emphasizes parallel tool calls
- Guides multi-step workflows
- Ensures complete investigations
- Uses direct, imperative language

**Specialists** (`SPECIALIST_PLANNING_PROMPT`):
- Promotes efficient task execution
- Minimizes LLM calls
- Encourages parallelization
- Guides complex task breakdown

### Example Behavior

Agents now plan internally without explicit tags:

```
User: "Why did deployment #5 fail and what services are affected?"

Agent's internal reasoning (not visible):
- Need deployment details
- Need pipeline logs
- Need affected services info
→ Call all three in parallel

Agent's visible response:
[Makes 3 tool calls in parallel]
[Synthesizes results]
"Deployment #5 failed due to..."
```

### Backward Compatibility

The `TodoListMiddleware` class still exists but does nothing:
```python
middleware = [TodoListMiddleware()]  # Issues DeprecationWarning, then passes through
```

**Recommendation**: Remove `TodoListMiddleware` from your middleware lists. It has no effect and only adds a deprecation warning to your logs.

### Planning Prompts Reference

| Prompt Constant | Status | Usage |
|-----------------|--------|-------|
| `SUPERVISOR_PROMPT` | ✅ Active | Includes planning principles for supervisor |
| `SPECIALIST_PLANNING_PROMPT` | ✅ Active | Append to specialist system prompts |
| `TODO_PLANNING_SPECIALIST_PROMPT` | ⚠️ Alias | Backward compatibility alias for `SPECIALIST_PLANNING_PROMPT` |

**Import:**
```python
from macsdk.agents.supervisor import SPECIALIST_PLANNING_PROMPT
# or for backward compatibility:
from macsdk.prompts import TODO_PLANNING_SPECIALIST_PROMPT
```

## SummarizationMiddleware

Automatically summarizes conversation history when it exceeds a token threshold, preventing context window overflow.

### Configuration

```yaml
# config.yml
summarization_enabled: false         # default: false
summarization_trigger_tokens: 100000 # tokens before summarizing
summarization_keep_messages: 6       # recent messages to preserve
```

### How It Works

1. Monitors conversation token count
2. When threshold is exceeded, summarizes older messages
3. Keeps the most recent N messages intact
4. Replaces old messages with a summary

### When to Enable

- Long-running chat sessions
- Conversations with many tool calls (high token usage)
- When you see "context length exceeded" errors

## PromptDebugMiddleware

Logs prompts sent to the LLM to the application log file (not stdout), useful for debugging agent behavior and prompt engineering.

**Important:** Debug prompts are written to the log file, NOT to stdout. This keeps the user interface clean while still providing full debugging information.

**⚠️ Security Warning - Development Only:** This middleware logs **complete, unredacted content** including:
- User inputs and conversation history (may contain PII)
- Complete system prompts (may expose business logic)
- Model responses
- **Tool call arguments with ALL sensitive data (API keys, tokens, passwords, credentials)**

**This middleware is EXCLUSIVELY for local development debugging. NEVER enable in production, staging, or any environment with real user data or real credentials.**

### Configuration

```yaml
# config.yml
debug: true  # default: false

# Optional: Configure debug output
debug_prompt_max_length: 10000  # Max chars per prompt (default: 10000)
debug_show_response: true       # Show model responses (default: true)
```

Or via CLI flag:

```bash
# Chatbots
my-chatbot chat --debug              # Enables debug mode
my-chatbot chat -vv                  # Same as --debug
my-chatbot chat --log-level DEBUG    # Sets log level to DEBUG

# Agents
my-agent chat --debug
my-agent chat -vv
```

### Where Debug Output Goes

**CLI Chat Mode:**
- Debug prompts written to `./logs/{app}-{date}.log`
- stdout remains clean for user interaction
- Log file path shown at startup: `📋 Logs: ./logs/chatbot-2026-01-04.log`

**Web Mode:**
- Debug prompts written to stderr
- Optionally also to file if `--log-file` is specified

### Log File Example

When enabled, your log file will contain:

```
2026-01-04 10:30:16 - macsdk.middleware.debug_prompts - DEBUG - 
================================================================================
🔍 [PROMPT DEBUG] Before Model Call
================================================================================

📋 SYSTEM PROMPT:
----------------------------------------
You are a DevOps monitoring assistant...
----------------------------------------

👤 USER MESSAGE (message 1):
----------------------------------------
[HumanMessage]
Show me failed pipelines from last week
----------------------------------------

📊 Total messages: 1
================================================================================
```

### Options

The middleware supports these options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `True` | Whether middleware is active |
| `show_system` | bool | `True` | Show system prompts |
| `show_user` | bool | `True` | Show user messages |
| `show_response` | bool | `True` | Show model responses |
| `max_length` | int | from config | Max chars per message (reads `debug_prompt_max_length` from config) |

**Breaking Change:** The `use_logger` parameter has been removed. Debug output now always goes to the logger (never to print/stdout).

**Output Format:** When `--show-llm-calls` is enabled, the logging system automatically configures a clean format without logger prefixes. The output includes agent context (e.g., `[LLM [supervisor]]`, `[LLM [toolbox]]`) to help track which agent is making each LLM call. This is controlled by the logging configuration, not by middleware parameters.

### Programmatic Usage

```python
from macsdk.middleware import PromptDebugMiddleware

middleware = PromptDebugMiddleware(
    enabled=True,
    show_system=True,     # Show system prompts
    show_user=True,       # Show user messages
    show_response=True,   # Show model responses
    max_length=10000,     # Override config value
)
```

### Configuration in config.yml

```yaml
# Enable debug mode globally
debug: true

# Configure debug output detail
debug_prompt_max_length: 10000   # Increase if prompts are cut off
debug_show_response: true        # Include model responses in debug
```

## ToolInstructionsMiddleware

Automatically injects usage instructions for knowledge tools (skills/facts) into the system prompt.

### Purpose

When agents have access to knowledge tools (`list_skills`, `read_skill`, `list_facts`, `read_fact`), this middleware detects them and adds usage instructions so the agent knows how to use them effectively.

### How It Works

The middleware:
1. Inspects the agent's tools on initialization
2. Detects knowledge tool patterns (skills, facts, or both)
3. Generates appropriate usage instructions
4. Injects instructions into the system prompt before each model call
5. Caches instructions for efficiency

### Automatic Usage

When you use `get_knowledge_bundle()`, the middleware is automatically included:

**`tools.py`** - Tools with lazy initialization:
```python
from macsdk.tools import api_get, calculate, fetch_file

def get_tools() -> list:
    from macsdk.tools.knowledge import get_knowledge_bundle
    
    _ensure_api_registered()
    knowledge_tools, _ = get_knowledge_bundle(__package__)
    
    return [api_get, fetch_file, calculate, *knowledge_tools]
```

**`agent.py`** - Middleware setup:
```python
from macsdk.tools.knowledge import get_knowledge_bundle

def create_agent_name():
    tools = get_tools()
    
    middleware = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]
    
    _, knowledge_middleware = get_knowledge_bundle(__package__)
    middleware.extend(knowledge_middleware)  # ToolInstructionsMiddleware is here
    
    return create_agent(tools=tools, middleware=middleware)
```

### Manual Usage

You can also create the middleware manually:

```python
from macsdk.middleware import ToolInstructionsMiddleware
from macsdk.tools.knowledge import create_skills_tools, create_facts_tools

# Create tools
skills_tools = create_skills_tools(skills_path)
facts_tools = create_facts_tools(facts_path)
all_tools = [*my_tools, *skills_tools, *facts_tools]

# Create middleware
middleware = [
    DatetimeContextMiddleware(),
    ToolInstructionsMiddleware(tools=all_tools),
]

agent = create_agent(
    tools=all_tools,
    middleware=middleware,
)
```

### What Gets Injected

**Skills only**:
```markdown
## Skills System
Use skills to discover how to perform tasks correctly:
- list_skills(): Get available task instructions
- read_skill(name): Get detailed steps for a specific task
```

**Facts only**:
```markdown
## Facts System
Use facts to get accurate contextual information:
- list_facts(): Get available information categories
- read_fact(name): Get specific details
```

**Both skills and facts**:
```markdown
## Knowledge System
You have access to skills (how-to instructions) and facts (contextual information):

**Skills** - Task instructions:
- list_skills() → read_skill(name) to learn how to do something

**Facts** - Contextual data:
- list_facts() → read_fact(name) to get accurate information
```

### Detection Logic

The middleware uses pattern matching to detect tools:

```python
TOOL_PATTERNS = {
    frozenset({"list_skills", "read_skill"}): SKILLS_INSTRUCTIONS,
    frozenset({"list_facts", "read_fact"}): FACTS_INSTRUCTIONS,
}

COMBINED_PATTERNS = {
    frozenset({"list_skills", "read_skill", "list_facts", "read_fact"}):
        KNOWLEDGE_SYSTEM_INSTRUCTIONS,
}
```

Combined patterns (both skills and facts) take priority over individual patterns for more concise instructions.

### Performance

- **Caching**: Instructions are generated once and cached
- **Efficient**: Only inspects tools on initialization
- **Minimal overhead**: Pattern matching is O(1) with frozensets

### Disabling

To temporarily disable (for testing or debugging):

```python
middleware = ToolInstructionsMiddleware(tools=tools, enabled=False)
```

### Complete Guide

See [Using Knowledge Tools Guide](../guides/using-knowledge-tools.md) for:
- Complete workflow examples
- Best practices
- Troubleshooting

## Using Middleware in Custom Agents

When creating agents, middleware is configured in `agent.py`:

```python
from langchain.agents import create_agent
from macsdk.middleware import DatetimeContextMiddleware, PromptDebugMiddleware

def create_my_agent(debug: bool = False):
    middleware = []
    
    if debug:
        middleware.append(PromptDebugMiddleware(enabled=True))
    
    middleware.append(DatetimeContextMiddleware())
    
    return create_agent(
        model=get_answer_model(),
        tools=get_tools(),
        middleware=middleware,
    )
```

## Middleware Execution Order

Middleware runs in the order it's added to the list:

1. First middleware processes the request first
2. Response flows back in reverse order

For debugging, add `PromptDebugMiddleware` first to see the final prompt after all other middleware has modified it.

