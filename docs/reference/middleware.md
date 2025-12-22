# Middleware Reference

MACSDK includes middleware components that enhance agent capabilities automatically.

## Available Middleware

| Middleware | Purpose | Default |
|------------|---------|---------|
| `DatetimeContextMiddleware` | Injects current date/time and pre-calculated date references | Enabled |
| `TodoListMiddleware` | Enables task planning for complex multi-step queries | Enabled |
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

### Benefits

- **No prompt boilerplate**: Agents don't need to explain date calculations
- **Consistent format**: All dates in ISO 8601, ready for API queries
- **Accurate context**: Current time is refreshed on each LLM call
- **Pre-calculated ranges**: Common date ranges ready to use

### Example Use Case

When a user asks "Show me failed pipelines from last week", the agent can immediately use the pre-calculated `Last 7 days` date in its API call without needing custom date logic in the prompt.

## TodoListMiddleware

Equips agents with an internal to-do list for tracking complex multi-step investigations.

### Configuration

**For Supervisor (enabled by default):**

```yaml
# config.yml
enable_todo: true  # Default: true (supervisor only)
```

**For Specialist Agents (disabled by default):**

Specialist agents don't inherit the global setting. Enable explicitly when needed:

```yaml
# Supervisor uses global setting
enable_todo: true

# Enable for specific agents that need task planning
diagnostic_agent:
  enable_todo: true   # Explicitly enable for complex agents
```

### What It Provides

When enabled, agents can:
- Break down complex queries into manageable tasks
- Track progress on multi-step investigations
- Mark tasks as complete
- Review remaining work before responding

### How It Works

The middleware automatically provides:
1. An internal to-do list managed by the agent
2. Context-specific system prompts for task planning guidance:
   - `TODO_PLANNING_SUPERVISOR_PROMPT`: For supervisors coordinating specialist agents
   - `TODO_PLANNING_SPECIALIST_PROMPT`: For specialist agents using tools
3. Natural language task tracking (no explicit tool calls needed)

The agent naturally plans and tracks tasks in its reasoning:

```
Agent internal reasoning:
"Let me break this down:
1. Check deployment status
2. Get pipeline details
3. Fetch error logs
4. Analyze root cause

Starting with step 1..."
```

### When to Use

Enable for agents that handle:
- **Complex diagnostics**: "Why did the deployment fail?"
- **Multi-step investigations**: Queries requiring multiple dependent tool calls
- **Comprehensive analysis**: Tasks needing information from multiple sources

Disable for agents that:
- Handle simple lookups
- Use single tool calls
- Don't require planning

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

The SDK provides two specialized prompts that are automatically injected when `enable_todo=True`:

#### For Supervisor Agents

The supervisor uses `TODO_PLANNING_SUPERVISOR_PROMPT`, which includes examples of coordinating specialist agents:

```python
from macsdk.prompts import TODO_PLANNING_SUPERVISOR_PROMPT

# Examples use agent calls:
# 1. Call deployment_agent("recent deployments")
# 2. Call pipeline_agent("pipeline #3 failed jobs")
# ...
```

#### For Specialist Agents

Specialist agents use `TODO_PLANNING_SPECIALIST_PROMPT`, which includes examples of using tools:

```python
from macsdk.prompts import TODO_PLANNING_SPECIALIST_PROMPT

# Examples use tool calls:
# 1. Call get_recent_deployments()
# 2. Call get_deployment_details(deployment_id=7)
# ...
```

#### Customizing Prompts

You can override the default prompts in your agent's `prompts.py`:

```python
from macsdk.prompts import TODO_PLANNING_COMMON

# Define your own specialized version
TODO_PLANNING_SPECIALIST_PROMPT = (
    TODO_PLANNING_COMMON + """
**Custom Investigation Flow:**
... your specific examples ...
"""
)
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

Displays the actual prompts sent to the LLM, useful for debugging agent behavior and prompt engineering.

### Configuration

```yaml
# config.yml
debug: true  # default: false
```

Or via CLI flag:

```bash
# Chatbots
my-chatbot chat --debug
my-chatbot web --debug

# Agents
my-agent chat --debug
```

### Output Example

When enabled, you'll see output like:

```
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

The middleware supports additional options when used programmatically:

```python
from macsdk.middleware import PromptDebugMiddleware

middleware = PromptDebugMiddleware(
    enabled=True,
    show_system=True,     # Show system prompts
    show_user=True,       # Show user messages
    show_response=True,   # Show model responses
    max_length=2000,      # Truncate long content
    use_logger=False,     # Use print (False) or logger (True)
)
```

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

