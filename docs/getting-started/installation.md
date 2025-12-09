# Installation

## Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Install from PyPI

```bash
# Using pip
pip install macsdk

# Using uv
uv add macsdk
```

### With RAG Support

To use the built-in RAG agent for documentation Q&A:

```bash
# Using pip
pip install macsdk[rag]

# Using uv
uv add macsdk[rag]
```

## Install from Source

```bash
git clone https://github.com/juanje/macsdk
cd macsdk
uv sync
```

## Verify Installation

```bash
macsdk --version
```

## Dependencies

### Core Dependencies

- **LangChain** >= 1.0.0 - Agent framework
- **LangGraph** >= 1.0.0 - Graph-based workflows
- **langchain-google-genai** >= 2.0.0 - Google AI integration
- **Pydantic** >= 2.0.0 - Data validation
- **Click** >= 8.0.0 - CLI framework
- **FastAPI** >= 0.115.0 - Web framework
- **Rich** >= 13.0.0 - Terminal formatting
- **Jinja2** >= 3.0.0 - Template engine
- **aiohttp** >= 3.0.0 - Async HTTP client
- **jsonpath-ng** >= 1.5.0 - JSONPath support

### RAG Dependencies (optional)

Installed with `macsdk[rag]`:

- **ChromaDB** >= 1.0.0 - Vector database
- **langchain-chroma** >= 1.0.0 - ChromaDB integration
- **BeautifulSoup4** >= 4.0.0 - HTML parsing
- **tiktoken** >= 0.5.0 - Token counting
- **tqdm** >= 4.0.0 - Progress bars

## Configuration

Create a `.env` file with your API keys:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

Get an API key from: https://aistudio.google.com/apikey

See [Configuration Reference](../reference/configuration.md) for all available options.

## Quick Verification

Create and run a simple chatbot:

```bash
# Create project
macsdk new chatbot test-bot
cd test-bot

# Configure
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Install and run
uv sync
uv run test-bot
```

You should see the command menu:

```
╭────────────────────── test-bot ──────────────────────╮
│                                                      │
│    chat      Start interactive CLI chat              │
│    web       Start web interface                     │
│    agents    List registered agents                  │
│    info      Show configuration                      │
│                                                      │
╰──────────────────────────────────────────────────────╯
```
