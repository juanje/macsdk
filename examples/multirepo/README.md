# Multirepo Examples

This directory demonstrates the **multi-repository approach** where chatbots and agents are separate projects.

## Structure

```
multirepo/
├── devops-chatbot/      # Chatbot that imports external agents
│   ├── pyproject.toml   # Has api-agent as dependency
│   └── src/devops_chatbot/
│       └── agents.py    # from api_agent import ApiAgent
│
└── api-agent/           # Standalone agent project
    ├── pyproject.toml   # Independent package
    └── src/api_agent/
        └── ...
```

## How It Works

1. **Agent as Package**: The `api-agent` is a complete Python package with its own `pyproject.toml`
2. **Dependency**: The chatbot declares `api-agent` as a dependency
3. **Source Configuration**: Uses `[tool.uv.sources]` to reference the local path during development
4. **Import**: Uses standard Python imports: `from api_agent import ApiAgent`

## Running the Examples

```bash
# From this directory
cd devops-chatbot
uv sync
uv run devops-chatbot
```

## Adding the Agent to a New Chatbot

```bash
# Option 1: Local path (development)
macsdk add-agent ./my-chatbot --path ./api-agent

# Option 2: Git repository
macsdk add-agent ./my-chatbot --git https://github.com/user/api-agent

# Option 3: Published package (when available)
macsdk add-agent ./my-chatbot --package api-agent
```

## When to Use This Approach

- **Reusable agents**: Share agents across multiple chatbots
- **Independent versioning**: Version and release agents separately
- **Team separation**: Different teams work on different components
- **Publishing**: Distribute agents as pip packages

