# Middleware Reference

MACSDK includes middleware components that enhance agent capabilities automatically.

## Available Middleware

| Middleware | Purpose | Default |
|------------|---------|---------|
| `DatetimeContextMiddleware` | Injects current date/time and pre-calculated date references | Enabled |
| `TodoListMiddleware` | Enables task planning for complex multi-step queries | Enabled |
| `ToolInstructionsMiddleware` | Auto-injects usage instructions for knowledge tools | Optional |
| `SummarizationMiddleware` | Summarizes long conversations to stay within token limits | Disabled |
| `PromptDebugMiddleware` | Displays prompts sent to the LLM for debugging | Disabled |

## DatetimeContextMiddleware

Injects temporal context into prompts, helping agents interpret timestamps, logs, and relative date expressions.

### Configuration

```yaml
# config.yml
include_datetime: true  # default: true
```

### What It Provides

When enabled, agents receive this context automatically:

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

### Example Use Case

When a user asks "Show me failed pipelines from last week", the agent can immediately use the pre-calculated `Last 7 days` date in its API call without needing custom date logic in the prompt.

## TodoListMiddleware

Equips agents with task planning capabilities for complex multi-step investigations without requiring explicit tool calls.

### Configuration

**Always Enabled:**

The TodoListMiddleware is always enabled for all agents (both supervisor and specialists) as of v0.6.0. This ensures consistent task planning capabilities across the system without requiring configuration.

### What It Provides

Agents can:
- Break down complex queries into manageable tasks
- Track progress on multi-step investigations
- Mark tasks as complete
- Review remaining work before responding
- All without explicit tool calls (no write_todos/read_todos)

### How It Works

The middleware manages task planning internally by:

1. **Plan Creation**: Agent uses `<plan>Task 1\nTask 2\nTask 3</plan>` tags in its response
2. **State Tracking**: Middleware parses tags and reconstructs plan from conversation history (stateless design)
3. **Prompt Injection**: Current plan with status indicators (✓/→/○) injected into system prompt
4. **Task Completion**: Agent uses `<task_complete>Task name</task_complete>` to mark tasks done

**Example Agent Response:**

```
Let me break this down into steps:

<plan>Check deployment status
Get pipeline details
Fetch error logs
Analyze root cause</plan>

I'll start by checking the deployment status...
[performs action]
<task_complete>Check deployment status</task_complete>

Now getting pipeline details...
```

**What the Agent Sees (Next Call):**

```
## Current Task Plan

✓ Check deployment status
→ Get pipeline details
○ Fetch error logs
○ Analyze root cause

**To update:** <task_complete>task name</task_complete>
**To create plan:** <plan>Task 1\nTask 2\nTask 3</plan>
```

**Key Architecture:**
- **Stateless**: Plan reconstructed from message history on each call
- **No tool calls**: Eliminates 4-5 extra LLM calls per complex query
- **Compatible**: Works with LangGraph persistence and multi-turn conversations

### When It Helps Most

The middleware is particularly valuable for:
- **Complex diagnostics**: "Why did the deployment fail?"
- **Multi-step investigations**: Queries requiring multiple dependent tool calls
- **Comprehensive analysis**: Tasks needing information from multiple sources

For simple queries, the middleware adds minimal overhead and the agent naturally skips planning when not needed.

### Benefits

- **Ensures completeness**: Agents follow through on all investigation paths
- **Better coordination**: Tracks dependencies between steps
- **Improved reliability**: Reduces premature responses with incomplete information

### Middleware Ordering

When using multiple middleware, order matters. TodoListMiddleware should be placed **before** SummarizationMiddleware:

```python
middleware = []
middleware.append(DatetimeContextMiddleware())
middleware.append(TodoListMiddleware())      # ✓ Before Summarization
middleware.append(SummarizationMiddleware()) # ✗ After TodoList
```

**Rationale**: The task planner needs access to full conversation context to make informed planning decisions. If summarization runs first, the planner sees compressed context and may miss important details.

### Example Use Case

**User query**: "Why did deployment #5 fail and what services are affected?"

**With TodoListMiddleware enabled**:
1. Agent creates internal plan: Check deployment → Get pipeline → Find failed jobs → Get logs → Check affected services
2. Tracks progress through each step
3. Ensures all questions are answered before responding
4. Returns complete answer with root cause and impact

**Without middleware**:
- May stop after first finding ("Deployment #5 failed")
- Might miss investigating affected services
- Less systematic investigation

### Task Planning Prompts

The SDK provides specialized prompts that are automatically integrated into agent system prompts:

#### For Supervisor Agents

The supervisor uses `TODO_PLANNING_SUPERVISOR_PROMPT`, which includes examples of coordinating specialist agents:

```python
from macsdk.agents.supervisor import TODO_PLANNING_SUPERVISOR_PROMPT

# Examples use agent calls:
# 1. Call deployment_agent("recent deployments")
# 2. Call pipeline_agent("pipeline #3 failed jobs")
# ...
```

#### For Specialist Agents

Specialist agents use `TODO_PLANNING_SPECIALIST_PROMPT`, which includes examples of using tools:

```python
from macsdk.agents.supervisor import TODO_PLANNING_SPECIALIST_PROMPT

# Examples use tool calls:
# 1. Call get_recent_deployments()
# 2. Call get_deployment_details(deployment_id=7)
# ...
```

#### Customizing Prompts

You can override the default prompts in your agent's `prompts.py`:

```python
from macsdk.agents.supervisor import TODO_PLANNING_COMMON

# Define your own specialized version
TODO_PLANNING_SPECIALIST_PROMPT = (
    TODO_PLANNING_COMMON + """
**Custom Investigation Flow:**
... your specific examples ...
"""
)
```

**Note:** You can also import from `macsdk.prompts` for backward compatibility:
```python
from macsdk.prompts import TODO_PLANNING_SUPERVISOR_PROMPT  # Still works
```

The SDK automatically injects the appropriate prompt based on the agent type.

### Programmatic Usage

```python
from langchain.agents import create_agent
from macsdk.middleware import TodoListMiddleware

middleware = [TodoListMiddleware(enabled=True)]

agent = create_agent(
    model=get_answer_model(),
    tools=get_tools(),
    middleware=middleware,
)
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

