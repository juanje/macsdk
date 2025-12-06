# api-agent

An example agent demonstrating how to use **MACSDK's API tools**.

This agent shows the recommended pattern for building API integrations:
1. Register services with `ApiServiceRegistry`
2. Create domain-specific tools using `api_get`/`api_post`
3. Use **JSONPath** to extract specific fields

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Agent                              │
├─────────────────────────────────────────────────────────────┤
│  Domain Tools (get_user, get_posts_by_user, etc.)           │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         MACSDK API Tools (api_get, api_post)        │    │
│  │  • Automatic retries with exponential backoff        │    │
│  │  • Authentication handling (Bearer tokens)           │    │
│  │  • JSONPath extraction for specific fields           │    │
│  │  • Timeout and error handling                        │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         ApiServiceRegistry                           │    │
│  │  • Service configuration (base_url, tokens)          │    │
│  │  • Rate limiting                                     │    │
│  │  • Headers management                                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. Service Registration

Register your API service once at startup:

```python
from macsdk.core.api_registry import register_api_service

register_api_service(
    name="jsonplaceholder",
    base_url="https://jsonplaceholder.typicode.com",
    timeout=10,
    max_retries=2,
)
```

### 2. Using API Tools

Create domain-specific tools using MACSDK's `api_get`/`api_post`:

```python
from macsdk.tools import api_get

@tool
async def get_user(user_id: int) -> str:
    """Get information about a user."""
    return await api_get.ainvoke({
        "service": "jsonplaceholder",
        "endpoint": f"/users/{user_id}",
    })
```

### 3. JSONPath Extraction

Extract specific fields from responses:

```python
@tool
async def get_user_names() -> str:
    """Get just the names of all users."""
    return await api_get.ainvoke({
        "service": "jsonplaceholder",
        "endpoint": "/users",
        "extract": "$[*].name",  # JSONPath expression
    })
```

### 4. Query Parameters

Pass query parameters for filtering:

```python
@tool
async def get_completed_todos_by_user(user_id: int) -> str:
    """Get completed TODOs for a user."""
    return await api_get.ainvoke({
        "service": "jsonplaceholder",
        "endpoint": "/todos",
        "params": {"userId": user_id, "completed": "true"},
    })
```

## Installation

```bash
uv sync
```

## Configuration

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Usage

### Show Commands

```bash
uv run api-agent
```

### Interactive Chat

```bash
uv run api-agent chat
```

### List Tools

```bash
uv run api-agent tools
```

### Show Agent Info

```bash
uv run api-agent info
```

### Example Queries

```
>> Get info about user 1
>> List all user names
>> Show posts by user 3
>> Get just the titles of posts by user 2
>> Show pending TODOs for user 1
>> Create a post titled "Hello" for user 1
```

## Available Tools

| Tool | Description | Uses JSONPath |
|------|-------------|---------------|
| `get_user` | Get user details by ID | No |
| `list_users` | List all users | No |
| `get_user_names` | Get just user names | Yes |
| `get_user_emails` | Get just user emails | Yes |
| `get_posts_by_user` | Get posts by user | No |
| `get_post` | Get specific post | No |
| `get_post_titles_by_user` | Get post titles | Yes |
| `create_post` | Create new post | No |
| `get_comments_on_post` | Get comments | No |
| `get_comment_emails_on_post` | Get commenter emails | Yes |
| `get_todos_by_user` | Get user TODOs | No |
| `get_completed_todos_by_user` | Get completed TODOs | No |
| `get_pending_todo_titles_by_user` | Get pending TODO titles | Yes |

## JSONPath Examples

| Expression | Description |
|------------|-------------|
| `$[*].name` | All names from array |
| `$[*].email` | All emails from array |
| `$[*].title` | All titles from array |
| `$.company.name` | Nested field |
| `$[?(@.completed==true)]` | Filter by condition |

## Using with Chatbots

Register the agent in your chatbot:

```python
from api_agent import ApiAgentAgent
from macsdk.core import register_agent

register_agent(ApiAgentAgent())
```

## Development

```bash
# Run linting
uv run ruff check src/

# Format code
uv run ruff format src/
```

## 🤖 AI Tools Disclaimer

This project was developed with the assistance of artificial intelligence tools:

**Tools used:**
- **Cursor**: Code editor with AI capabilities
- **Claude-4-Sonnet**: Anthropic's language model

**Division of responsibilities:**

**AI (Cursor + Claude-4-Sonnet)**:
- 🔧 Initial code prototyping
- 📝 Generation of examples and test cases
- 🐛 Assistance in debugging and error resolution
- 📚 Documentation and comments writing
- 💡 Technical implementation suggestions

**Human (Juanje Ojeda)**:
- 🎯 Specification of objectives and requirements
- 🔍 Critical review of code and documentation
- 💬 Iterative feedback and solution refinement
- 📋 Definition of project's educational structure
- ✅ Final validation of concepts and approaches

**Collaboration philosophy**: AI tools served as a highly capable technical assistant, while all design decisions, educational objectives, and project directions were defined and validated by the human.
