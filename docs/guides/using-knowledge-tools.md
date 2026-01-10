# Using Knowledge Tools

Knowledge tools enable agents to access task instructions (skills) and contextual information (facts) that are packaged with the agent. This guide explains how to use the knowledge system effectively.

## Philosophy: Extension Without Code Changes

The knowledge system follows MACSDK's core principle: **extend agent capabilities without modifying code**.

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT + KNOWLEDGE                        │
│                                                             │
│   CAPABILITIES (agent.py)                                   │
│   └── "What I can do" (base system prompt)                  │
│                                                             │
│   + Skills (skills/*.md)                                    │
│   └── "How to do complex tasks" (step-by-step)              │
│                                                             │
│   + Facts (facts/*.md)                                      │
│   └── "Domain context" (reference data, configs)            │
│                                                             │
│   = Complete agent prompt (assembled by middleware)         │
└─────────────────────────────────────────────────────────────┘
```

## Overview

The knowledge system consists of:

- **Skills**: Step-by-step instructions for performing specific tasks
- **Facts**: Contextual information like service names, configurations, and policies
- **Tools**: `read_skill`, `read_fact`
- **Middleware**: Automatically injects usage instructions and inventory into the system prompt

## Quick Start

### 1. Create Agent

Create a new agent (knowledge tools are auto-detected):

```bash
macsdk new agent devops-specialist
```

This generates:

```
devops-specialist/
└── src/
    └── devops_specialist/
        ├── agent.py         # Uses get_sdk_tools and get_sdk_middleware
        ├── tools.py         # Configured for auto-detection
        ├── skills/          # Empty, ready for use
        └── facts/           # Empty, ready for use
```

### 2. Agent Code (Auto-Generated)

The generated code uses SDK internal tools with auto-detection:

**`tools.py`** - Uses `get_sdk_tools` for automatic inclusion:

```python
from macsdk.tools import api_get, fetch_file, get_sdk_tools

def get_tools() -> list:
    """Get all tools for this agent."""
    _ensure_api_registered()
    
    return [
        *get_sdk_tools(__package__),  # calculate + auto-detect knowledge
        api_get,
        fetch_file,
    ]
```

**`agent.py`** - Uses `get_sdk_middleware` for auto-detection:

```python
from macsdk.tools import get_sdk_middleware
from .tools import get_tools

def create_agent_name():
    tools = get_tools()  # Already includes SDK tools
    
    middleware = [
        DatetimeContextMiddleware(),
        *get_sdk_middleware(__package__),  # Auto-detect knowledge
    ]
    
    return create_agent(
        tools=tools,
        middleware=middleware,
        system_prompt=SYSTEM_PROMPT,
    )
```

**Key benefits:**
- ✅ `calculate` always included (LLMs need it)
- ✅ Knowledge tools auto-detected when you add .md files
- ✅ Zero configuration - just add files
- ✅ Simple and maintainable

### 3. Add Your Skills and Facts

Replace the example files with your own content:

**`src/your_agent/skills/deploy-service.md`**:
```markdown
---
name: deploy-service
description: How to deploy a service safely
---

# Deploy Service

## Steps

1. Check service health
2. Review alerts
3. Deploy using API
4. Monitor deployment
...
```

**`src/your_agent/facts/service-info.md`**:
```markdown
---
name: service-catalog
description: Information about available services
---

# Service Catalog

## Production Services

- API Gateway (ID: 1)
- Auth Service (ID: 2)
...
```

## How It Works

### Automatic Path Resolution

The `get_knowledge_bundle(__package__)` function uses `importlib.resources` to locate skills and facts:

- **Development mode**: Reads from `src/your_agent/skills/` and `src/your_agent/facts/`
- **Installed package**: Reads from the installed package location
- **No configuration needed**: Paths are resolved automatically

### Automatic Instruction Injection

The `ToolInstructionsMiddleware` detects which knowledge tools are present and automatically adds usage instructions and the inventory of available skills/facts to the system prompt:

**Skills only**:
```
## Skills System
You have access to step-by-step task instructions (skills).

**Skills**: Task instructions showing how to perform specific operations.
Use `read_skill(path)` to get detailed steps for a specific task.

The available skills are listed below...

## Available Skills
Use `read_skill(path)` to get detailed content.

- **deploy-service** (`deploy-service.md`): How to deploy a service safely
- **check-health** (`check-health.md`): Service health monitoring
```

**Skills + Facts** (combined):
```
## Knowledge System
You have access to skills (how-to instructions) and facts (contextual information).

**Skills**: Step-by-step task instructions. Use `read_skill(path)` to get the content.

**Facts**: Contextual data and reference information. Use `read_fact(path)` to get details.

The available skills and facts are listed below...

## Available Skills
...

## Available Facts
...
```

## Usage Patterns

### Pattern 1: Task Guidance

Agent flow when user asks to perform a complex task:

1. **Check system prompt** for available skills (pre-injected inventory)

2. **Read the relevant skill**:
   ```
   Agent: read_skill("deploy-service.md")
   → Full deployment instructions
   ```

3. **Follow the steps** systematically

4. **Complete the task** using tools (API calls, file fetching, etc.)

### Pattern 2: Contextual Information

Agent flow when user asks about specific services:

1. **Check system prompt** for available facts (pre-injected inventory)

2. **Read relevant facts**:
   ```
   Agent: read_fact("service-catalog.md")
   → Service names, IDs, configurations
   ```

3. **Use accurate information** in subsequent operations

### Pattern 3: Progressive Disclosure (Hierarchical Knowledge)

For complex domains, organize knowledge hierarchically using **progressive disclosure**:
the agent sees only top-level skills/facts in the inventory, and discovers more specific
documents by reading the general ones first.

#### Directory Structure

```
skills/
├── check-service-health.md       # ← Listed in inventory (top-level)
├── check-service-health/         # ← NOT listed, but accessible
│   ├── api-gateway.md
│   ├── auth-service.md
│   └── postgres-primary.md
├── deploy-service.md             # ← Listed in inventory
└── deploy-service/               # ← NOT listed
    ├── deploy-frontend.md
    └── deploy-backend.md
```

#### How It Works

1. **Inventory shows only top-level files**: The agent's system prompt lists only
   `check-service-health.md` and `deploy-service.md`

2. **Top-level skills link to specific ones**: The general skill explains the topic
   and references specific sub-skills:

   ```markdown
   # Check Service Health

   ## General Workflow
   1. Start with /services to get overview
   2. For deeper investigation, use service-specific skills (see below)

   ## Service-Specific Skills
   - **check-service-health/api-gateway.md**: API Gateway troubleshooting
   - **check-service-health/auth-service.md**: Auth service monitoring
   ```

3. **Agent navigates hierarchically**: When the agent needs details, it reads
   the specific sub-skill using the full path:

   ```
   Agent: read_skill("check-service-health/api-gateway.md")
   → Detailed API Gateway troubleshooting steps
   ```

#### Benefits

| Benefit | Description |
|---------|-------------|
| **Reduced prompt size** | Only top-level skills in inventory |
| **Better context** | Agent reads general guidance before specifics |
| **Scalability** | Works well with many specific skills |
| **Intentionality** | Agent understands WHY it needs the specific skill |

#### Writing Top-Level Skills

A good top-level skill should:

1. **Provide overview**: Explain the general approach
2. **List sub-skills**: Document what specific skills exist and when to use them
3. **Include paths**: Use exact paths so the agent can read them

**Example** (`check-service-health.md`):

```markdown
---
name: check-service-health
description: How to check service health (general guidance)
---

# Check Service Health

## Quick Overview
Use `api_get` with service="devops", endpoint="/services"

## When to Use Service-Specific Skills

For detailed troubleshooting, use these specialized skills:
- **check-service-health/api-gateway.md**: Latency issues, timeouts
- **check-service-health/auth-service.md**: Token problems, dependencies
- **check-service-health/postgres-primary.md**: Connection pools, queries

Use this general skill for **overview and initial assessment**.
Use service-specific skills when you need **detailed troubleshooting**.
```

#### Agent Workflow Example

**User**: "Why is the API Gateway having issues?"

**Agent**:
1. Sees `check-service-health.md` in inventory
2. Reads it → gets overview + learns about specific skills
3. Reads `check-service-health/api-gateway.md` for detailed steps
4. Follows the specific troubleshooting procedure

This pattern ensures the agent has context before diving into specifics.

## Frontmatter Format

All knowledge files must have YAML frontmatter:

```markdown
---
name: unique-identifier
description: Human-readable description
---

# Content Title

Your content here...
```

**Fields**:
- `name` (required): Unique identifier for the document
- `description` (required): Brief description shown in listings
- Additional custom fields are allowed but not used by the system

## Package Distribution

### Including Files in Package

Skills and facts are automatically included when using Hatch (the default build backend):

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/my_agent"]
# All files inside src/my_agent/ are included automatically
```

### Verification

To verify files are included:

```bash
# Build the package
uv build

# Check contents
tar -tzf dist/my_agent-*.tar.gz | grep -E '\.(md)$'
```

You should see your skills and facts markdown files.

## Manual Integration

If you're adding knowledge tools to an existing agent manually:

### 1. Install dependencies

No additional dependencies needed - knowledge tools are part of core MACSDK.

### 2. Create directory structure

```bash
mkdir -p src/your_agent/skills src/your_agent/facts
```

### 3. Update `tools.py`

Use `get_sdk_tools` for automatic inclusion:

```python
from macsdk.tools import api_get, fetch_file, get_sdk_tools

def get_tools() -> list:
    """Get all tools for this agent."""
    _ensure_api_registered()
    
    return [
        *get_sdk_tools(__package__),  # calculate + auto-detect knowledge
        api_get,
        fetch_file,
    ]
```

### 4. Update `agent.py`

Use `get_sdk_middleware` for auto-detection:

```python
from macsdk.tools import get_sdk_middleware

def create_your_agent():
    tools = get_tools()  # Already includes SDK tools
    
    middleware = [
        DatetimeContextMiddleware(),
        *get_sdk_middleware(__package__),  # Auto-detect knowledge
    ]
    
    return create_agent(
        tools=tools,
        middleware=middleware,
        system_prompt=SYSTEM_PROMPT,
    )
```

### 5. Add .md files

Add skills or facts as .md files with frontmatter. They'll be auto-detected on next run.

## Advanced Usage

### Partial Knowledge (Skills OR Facts)

Include only skills or only facts:

```python
# Skills only
tools, middleware = get_knowledge_bundle(
    __package__,
    include_skills=True,
    include_facts=False,
)

# Facts only
tools, middleware = get_knowledge_bundle(
    __package__,
    include_skills=False,
    include_facts=True,
)
```

### Custom Subdirectories

Use different directory names:

```python
tools, middleware = get_knowledge_bundle(
    __package__,
    skills_subdir="procedures",
    facts_subdir="reference",
)
```

Then place files in:
- `src/your_agent/procedures/`
- `src/your_agent/reference/`

### Multiple Knowledge Sources

Combine knowledge from multiple packages:

```python
from macsdk.tools.knowledge import get_knowledge_bundle

# Get knowledge from main agent
agent_tools, agent_mw = get_knowledge_bundle(__package__)

# Get knowledge from shared library
shared_tools, shared_mw = get_knowledge_bundle("my_company.shared_knowledge")

tools = [
    *base_tools,
    *agent_tools,
    *shared_tools,
]

middleware = [
    *base_middleware,
    *agent_mw,
    *shared_mw,
]
```

## Best Practices

### 1. Skill Design

- **One task per skill**: Each skill should focus on a single task
- **Clear steps**: Use numbered lists for procedures
- **Prerequisites**: List what's needed before starting
- **Common issues**: Include troubleshooting tips
- **Related content**: Link to relevant facts or other skills
- **Progressive disclosure**: For complex topics, create a general skill that links to specific sub-skills in a subdirectory

### 2. Fact Design

- **Accurate data**: Facts should be the source of truth
- **Regular updates**: Keep facts current with infrastructure changes
- **Clear organization**: Use headings and sections
- **Concise**: Include only essential information
- **Actionable**: Provide data the agent can use in operations

### 3. Naming Conventions

- Use kebab-case for file names: `deploy-service.md`
- Use descriptive names that indicate purpose
- Avoid spaces or special characters
- Keep names relatively short

### 4. Content Structure

```markdown
---
name: task-name
description: Brief description
---

# Task Name

## Purpose
What this skill/fact is for

## Content
Main content here

## Related
Links to related skills/facts
```

### 5. Testing

Always test your knowledge tools:

```python
# In your test file
def test_skills_available():
    tools, _ = get_knowledge_bundle(__package__)
    read_skill = next(t for t in tools if t.name == "read_skill")
    content = read_skill.invoke({"path": "deploy-service.md"})
    assert "Deploy" in content
```

## Examples

See the complete example in [`examples/agent-with-knowledge/`](../../examples/agent-with-knowledge/).

## Troubleshooting

### Skills/Facts Not Found

**Problem**: Agent can't find skills/facts directories.

**Solution**: Ensure directories are inside the Python package:
- ✅ `src/my_agent/skills/`
- ❌ `skills/` (at project root)

### Files Not Included in Package

**Problem**: Skills/facts missing after installing package.

**Solution**: 
1. Verify files are in `src/package_name/`
2. Check `pyproject.toml` has correct `packages` configuration
3. Rebuild package: `uv build`

### Middleware Not Injecting Instructions

**Problem**: System prompt doesn't include knowledge tool instructions.

**Solution**:
1. Verify middleware is in the middleware list
2. Check that tools are in the tools list
3. Ensure middleware comes after base middleware (DatetimeContext, etc.)

### Path Traversal Errors

**Problem**: Error messages about invalid paths.

**Solution**: Use relative paths only, never `../` or absolute paths.

## See Also

- [Tools Reference](../reference/tools.md) - Complete tool API documentation
- [Middleware Reference](../reference/middleware.md) - Middleware configuration
- [Creating Agents](./creating-agents.md) - General agent development guide

