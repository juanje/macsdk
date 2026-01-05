# Migration Guide: v0.5.x to v0.6.0

This guide helps you migrate projects created with MACSDK v0.5.x to v0.6.0.

## Table of Contents

1. [Overview](#overview)
2. [Breaking Changes](#breaking-changes)
3. [Backwards Compatibility](#backwards-compatibility)
4. [Migration Steps](#migration-steps)
   - [1. Update Agent Creation](#1-update-agent-creation)
   - [2. Update Agent Run Function](#2-update-agent-run-function)
   - [3. Update Agent Class](#3-update-agent-class)
   - [4. Update Configuration](#4-update-configuration)
   - [5. Removed Prompts](#5-removed-prompts)
5. [Quick Checklist](#quick-checklist)
6. [Benefits](#benefits)
7. [Need Help?](#need-help)

---

## Overview

Version 0.6.0 improves prompt caching, system message handling, and simplifies TODO middleware. **Projects created with v0.5.x will continue to work** with deprecation warnings.

## Breaking Changes

1. **System Prompt**: Pass to `create_agent(system_prompt=...)` instead of `run_agent_with_tools()`
2. **TODO Middleware**: Always enabled (no longer configurable)
3. **Datetime Context**: Injected at end of system messages for better caching
4. **Function Signatures**: Simplified (no `enable_todo`, no tuple returns)

## Backwards Compatibility

**Old code still works** but with deprecation warnings:

```
DeprecationWarning: Passing 'system_prompt' to run_agent_with_tools() is deprecated.
This parameter will be removed in v1.0.0.
```

### Old Pattern (v0.5.x) - Still works, but inefficient:
- ❌ System prompts sent as `HumanMessage` (not cached by Gemini)
- ❌ Datetime context injected before system prompt
- ❌ Reduced performance

### New Pattern (v0.6.0) - Recommended:
- ✅ System prompts sent as `SystemMessage` (cached by Gemini)
- ✅ Datetime context at end for optimal caching
- ✅ Better performance and token usage

---

## Migration Steps

### 1. Update Agent Creation

**Key changes:**
- Remove `enable_todo` parameter
- Change return from `tuple[Any, str]` to `Any`
- Pass `system_prompt` to `create_agent()`
- Always include `TodoListMiddleware()`

```python
# Before (v0.5.x)
def create_my_agent(debug: bool | None = None, enable_todo: bool | None = None) -> tuple[Any, str]:
    system_prompt = SYSTEM_PROMPT
    if enable_todo:
        system_prompt += "\n\n" + TODO_PLANNING_SPECIALIST_PROMPT
        middleware.append(TodoListMiddleware(enabled=True))
    
    agent = create_agent(model=..., tools=..., middleware=...)
    return agent, system_prompt  # Tuple

# After (v0.6.0)
def create_my_agent(debug: bool | None = None) -> Any:
    system_prompt = SYSTEM_PROMPT + "\n\n" + TODO_PLANNING_SPECIALIST_PROMPT
    
    middleware.append(TodoListMiddleware(enabled=True))  # Always
    
    agent = create_agent(
        model=..., 
        tools=..., 
        middleware=...,
        system_prompt=system_prompt,  # ✅ Pass here
    )
    return agent  # No tuple
```

### 2. Update Agent Run Function

**Key changes:**
- Remove tuple unpacking
- Remove `system_prompt` parameter from `run_agent_with_tools()`
- Remove `enable_todo` parameter

```python
# Before (v0.5.x)
async def run_my_agent(query: str, enable_todo: bool | None = None, ...) -> dict:
    agent, system_prompt = create_my_agent(enable_todo=enable_todo)  # Tuple unpacking
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        system_prompt=system_prompt,  # ❌ Deprecated
        agent_name="my_agent",
    )

# After (v0.6.0)
async def run_my_agent(query: str, ...) -> dict:
    agent = create_my_agent()  # No unpacking
    return await run_agent_with_tools(
        agent=agent,
        query=query,
        agent_name="my_agent",
        # ✅ No system_prompt
    )
```

### 3. Update Agent Class

Remove `enable_todo` parameter from the `run()` method:

```python
# Before (v0.5.x)
async def run(self, query: str, enable_todo: bool | None = None, ...) -> dict:
    return await run_my_agent(query, enable_todo=enable_todo, ...)

# After (v0.6.0)
async def run(self, query: str, ...) -> dict:
    return await run_my_agent(query, ...)
```

### 4. Update Configuration

Remove `enable_todo` from `config.yml`:

```yaml
# Before (v0.5.x)
enable_todo: true
my_agent:
  enable_todo: true

# After (v0.6.0)
# No enable_todo needed - always enabled
```

### 5. Removed Prompts

The following prompt constants were removed from `macsdk.prompts`:

| Prompt | Status | Action |
|--------|--------|--------|
| `TODO_PLANNING_COMMON` | ❌ Removed | Remove imports (integrated into middleware) |
| `TODO_PLANNING_SUPERVISOR_PROMPT` | ❌ Removed | Remove imports (integrated into `SUPERVISOR_PROMPT`) |
| `TODO_PLANNING_SPECIALIST_PROMPT` | ✅ Available | Import from `macsdk.agents.supervisor.prompts` |

**Usage:**
```python
from macsdk.agents.supervisor.prompts import TODO_PLANNING_SPECIALIST_PROMPT

system_prompt = BASE_PROMPT + "\n\n" + TODO_PLANNING_SPECIALIST_PROMPT
```

---

## Quick Checklist

For each specialist agent:

- [ ] Remove `enable_todo` parameter from `create_<agent>()` 
- [ ] Change return type from `tuple[Any, str]` to `Any`
- [ ] Pass `system_prompt=...` to `create_agent()`
- [ ] Always add `TodoListMiddleware()` to middleware
- [ ] Remove tuple unpacking in `run_<agent>()`
- [ ] Remove `system_prompt` from `run_agent_with_tools()` call
- [ ] Remove `enable_todo` from agent's `run()` method
- [ ] Remove `enable_todo` from `config.yml`

---

## Benefits

After migration:

1. **Better LLM Caching** - System prompts properly cached by Gemini
2. **Simpler Configuration** - No `enable_todo` management
3. **Cleaner Code** - Simplified signatures
4. **Improved Performance** - Datetime caching, better prompt structure
5. **Future-Proof** - Ready for v1.0.0

---

## Need Help?

- [Examples](../../examples/) - Reference implementations
- [API Documentation](../reference/) - Full API reference
- [GitHub Issues](https://github.com/juanje/macsdk/issues) - Report problems

---

## Deprecation Timeline

- **v0.6.0** (Current): Deprecated parameters work with warnings
- **v1.0.0** (Future): Deprecated parameters removed

**Migrate now for a smooth transition.**
