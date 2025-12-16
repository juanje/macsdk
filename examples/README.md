# MACSDK Examples

This directory contains example projects demonstrating different approaches to building chatbots with MACSDK.

## Project Organization Approaches

MACSDK supports two main approaches for organizing your chatbot and agents:

### [Monorepo](monorepo/) - Single Repository

All code lives in one repository. Agents are internal modules within the chatbot project.

**Best for:**
- Project-specific agents that won't be reused
- Simpler dependency management
- Teams preferring unified codebases
- Rapid prototyping

```
my-chatbot/
├── src/my_chatbot/
│   ├── local_agents/    # Local agents (vs remote packages)
│   │   └── weather/
│   └── ...
└── pyproject.toml       # Single config
```

### [Multirepo](multirepo/) - Multiple Repositories

Chatbot and agents are separate projects with their own repositories/packages.

**Best for:**
- Reusable agents across multiple chatbots
- Independent versioning and releases
- Teams working on different components
- Publishing agents as packages

```
workspace/
├── my-chatbot/          # Chatbot project
│   └── pyproject.toml   # Depends on agents
├── weather-agent/       # Separate agent
│   └── pyproject.toml
└── gitlab-agent/        # Another agent
    └── pyproject.toml
```

## Quick Start

### Monorepo Approach

```bash
# Create chatbot with internal agent
macsdk new chatbot my-chatbot
cd my-chatbot
macsdk add-agent . --new weather --description "Weather forecasts"
```

### Multirepo Approach

```bash
# Create separate projects
macsdk new chatbot my-chatbot
macsdk new agent weather-agent

# Link them
macsdk add-agent ./my-chatbot --path ./weather-agent
```

## Examples in This Directory

| Directory | Description |
|-----------|-------------|
| [`monorepo/devops-chatbot`](monorepo/devops-chatbot/) | DevOps chatbot with internal API agent |
| [`multirepo/devops-chatbot`](multirepo/devops-chatbot/) | DevOps chatbot importing external agent |
| [`multirepo/api-agent`](multirepo/api-agent/) | Standalone API agent for JSONPlaceholder |

