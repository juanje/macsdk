# Monorepo Examples

This directory demonstrates the **mono-repository approach** where agents live inside the chatbot project.

## Structure

```
monorepo/
└── devops-chatbot/
    ├── pyproject.toml           # Single config for everything
    └── src/devops_chatbot/
        ├── local_agents/        # Local agents directory
        │   ├── __init__.py
        │   └── api/             # API agent as local module
        │       ├── __init__.py
        │       ├── agent.py
        │       ├── tools.py
        │       └── ...
        ├── agents.py            # Uses relative imports
        └── ...
```

## How It Works

1. **Local Modules**: Agents are Python modules inside `src/{chatbot}/local_agents/`
2. **No Extra Dependencies**: No need to configure external packages
3. **Relative Imports**: Uses `from .local_agents.api import ApiAgent`
4. **Single pyproject.toml**: One configuration file for the entire project

## Running the Example

```bash
cd devops-chatbot
uv sync
uv run devops-chatbot
```

## Creating Local Agents

```bash
# From inside the chatbot directory
cd my-chatbot
macsdk add-agent . --new weather --description "Weather forecasts"

# This creates:
# src/my_chatbot/local_agents/weather/
#   ├── __init__.py
#   ├── agent.py
#   ├── config.py
#   ├── models.py
#   ├── prompts.py
#   └── tools.py
```

## When to Use This Approach

- **Project-specific agents**: Agents that won't be reused elsewhere
- **Simpler setup**: No dependency configuration needed
- **Unified codebase**: Everything in one place
- **Rapid prototyping**: Quick iteration without package management

