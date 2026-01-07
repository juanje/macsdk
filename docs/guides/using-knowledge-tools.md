# Using Knowledge Tools

Knowledge tools enable agents to access task instructions (skills) and contextual information (facts) that are packaged with the agent. This guide explains how to use the knowledge system effectively.

## Overview

The knowledge system consists of:

- **Skills**: Step-by-step instructions for performing specific tasks
- **Facts**: Contextual information like service names, configurations, and policies
- **Tools**: `list_skills`, `read_skill`, `list_facts`, `read_fact`
- **Middleware**: Automatically injects usage instructions into the system prompt

## Quick Start

### 1. Create Agent with Knowledge Tools

When creating a new agent, use the `--with-knowledge` flag:

```bash
macsdk new agent devops-specialist --with-knowledge
```

This generates:

```
devops-specialist/
└── src/
    └── devops_specialist/
        ├── agent.py         # Pre-configured with knowledge bundle
        ├── skills/          # Task instructions directory
        │   └── example-skill.md
        └── facts/           # Contextual info directory
            └── example-fact.md
```

### 2. Agent Code (Auto-Generated)

The generated code uses a clean, zero-duplication architecture:

**`tools.py`** - Single source of truth for all tools:

```python
from macsdk.tools import api_get, calculate, fetch_file

def get_tools() -> list:
    """Get all tools for this agent."""
    from macsdk.tools.knowledge import get_knowledge_bundle
    
    _ensure_api_registered()
    
    # Lazy initialization - get knowledge tools when needed
    knowledge_tools, _ = get_knowledge_bundle(__package__)
    
    return [
        api_get,
        fetch_file,
        calculate,
        *knowledge_tools,  # Adds: list_skills, read_skill, list_facts, read_fact
    ]
```

**`agent.py`** - Direct middleware setup:

```python
from macsdk.tools.knowledge import get_knowledge_bundle
from .tools import get_tools

def create_agent_name():
    # Get all tools in one call (includes knowledge tools)
    tools = get_tools()
    
    middleware = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]
    
    # Add knowledge middleware directly
    _, knowledge_middleware = get_knowledge_bundle(__package__)
    middleware.extend(knowledge_middleware)
    
    return create_agent(
        tools=tools,
        middleware=middleware,
        system_prompt=SYSTEM_PROMPT,
    )
```

**Key benefits:**
- ✅ Tools appear in `my-agent tools` command
- ✅ Zero duplication - tools defined once
- ✅ No risk of middleware/tools mismatch
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

The `ToolInstructionsMiddleware` detects which knowledge tools are present and automatically adds usage instructions to the system prompt:

**Skills only**:
```
## Skills System
Use skills to discover how to perform tasks correctly:
- list_skills(): Get available task instructions
- read_skill(name): Get detailed steps for a specific task
```

**Skills + Facts** (combined):
```
## Knowledge System
You have access to skills (how-to instructions) and facts (contextual information):

**Skills** - Task instructions:
- list_skills() → read_skill(name) to learn how to do something

**Facts** - Contextual data:
- list_facts() → read_fact(name) to get accurate information
```

## Usage Patterns

### Pattern 1: Task Guidance

Agent flow when user asks to perform a complex task:

1. **Check for relevant skill**:
   ```
   Agent: list_skills()
   → ["deploy-service", "troubleshoot-alerts", ...]
   ```

2. **Read the skill**:
   ```
   Agent: read_skill("deploy-service.md")
   → Full deployment instructions
   ```

3. **Follow the steps** systematically

4. **Complete the task** using tools (API calls, file fetching, etc.)

### Pattern 2: Contextual Information

Agent flow when user asks about specific services:

1. **Check available facts**:
   ```
   Agent: list_facts()
   → ["service-catalog", "deployment-windows", ...]
   ```

2. **Read relevant facts**:
   ```
   Agent: read_fact("service-catalog.md")
   → Service names, IDs, configurations
   ```

3. **Use accurate information** in subsequent operations

### Pattern 3: Hierarchical Knowledge

Organize knowledge hierarchically:

```
skills/
├── deploy/
│   ├── deploy-frontend.md
│   ├── deploy-backend.md
│   └── deploy-database.md
└── troubleshoot/
    ├── troubleshoot-alerts.md
    └── troubleshoot-logs.md
```

The agent can navigate this structure:
- List all skills to see categories
- Read specific skills as needed

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

Add knowledge tools to your `get_tools()` function:

```python
from macsdk.tools import api_get, calculate, fetch_file

def get_tools() -> list:
    """Get all tools for this agent."""
    from macsdk.tools.knowledge import get_knowledge_bundle
    
    # Your existing initialization
    _ensure_api_registered()
    
    # Get knowledge tools (lazy initialization)
    knowledge_tools, _ = get_knowledge_bundle(__package__)
    
    return [
        api_get,
        fetch_file,
        calculate,
        *knowledge_tools,  # list_skills, read_skill, list_facts, read_fact
    ]
```

### 4. Update `agent.py`

Add knowledge middleware to your agent:

```python
from macsdk.tools.knowledge import get_knowledge_bundle

def create_your_agent():
    tools = get_tools()  # Already includes knowledge tools
    
    middleware = [
        DatetimeContextMiddleware(),
        TodoListMiddleware(enabled=True),
    ]
    
    # Add knowledge middleware
    _, knowledge_middleware = get_knowledge_bundle(__package__)
    middleware.extend(knowledge_middleware)
    
    return create_agent(
        tools=tools,
        middleware=middleware,
        system_prompt=SYSTEM_PROMPT,
    )
```

### 5. Add example files

Create at least one skill and one fact to test the system.

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
    list_skills = next(t for t in tools if t.name == "list_skills")
    skills = list_skills.invoke({})
    assert len(skills) > 0
    assert any(s["name"] == "deploy-service" for s in skills)
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

