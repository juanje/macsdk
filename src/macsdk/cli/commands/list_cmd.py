"""Command for listing SDK tools.

This module provides functions for listing tools available in MACSDK.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# =============================================================================
# SDK Tools Information
# =============================================================================

# Internal tools (auto-included via get_sdk_tools)
INTERNAL_TOOLS = [
    {
        "name": "calculate",
        "category": "Math",
        "description": "Safe math evaluation (LLMs are unreliable at arithmetic)",
        "params": "expression",
        "condition": "always",
    },
    {
        "name": "read_skill",
        "category": "Knowledge",
        "description": "Read a skill document (step-by-step instructions)",
        "params": "path",
        "condition": "if skills/ has .md",
    },
    {
        "name": "read_fact",
        "category": "Knowledge",
        "description": "Read a fact document (contextual information)",
        "params": "path",
        "condition": "if facts/ has .md",
    },
]

# Manual tools (add explicitly to get_tools)
MANUAL_TOOLS = [
    # API tools
    {
        "name": "api_get",
        "category": "API",
        "description": "GET request to a registered API service",
        "params": "service, endpoint, params?, extract?",
    },
    {
        "name": "api_post",
        "category": "API",
        "description": "POST request with JSON body",
        "params": "service, endpoint, body, params?, extract?",
    },
    {
        "name": "api_put",
        "category": "API",
        "description": "PUT request with JSON body",
        "params": "service, endpoint, body, params?, extract?",
    },
    {
        "name": "api_delete",
        "category": "API",
        "description": "DELETE request to an endpoint",
        "params": "service, endpoint, params?",
    },
    {
        "name": "api_patch",
        "category": "API",
        "description": "PATCH request with JSON body",
        "params": "service, endpoint, body, params?, extract?",
    },
    # Remote file tools
    {
        "name": "fetch_file",
        "category": "Remote",
        "description": "Fetch file from URL with grep/head/tail filtering",
        "params": "url, grep_pattern?, tail_lines?, head_lines?",
    },
    {
        "name": "fetch_and_save",
        "category": "Remote",
        "description": "Download and save a file locally",
        "params": "url, save_path, timeout?",
    },
    {
        "name": "fetch_json",
        "category": "Remote",
        "description": "Fetch JSON with optional JSONPath extraction",
        "params": "url, extract?, timeout?",
    },
]

# Service configuration options
SERVICE_CONFIG_OPTIONS = [
    ("token", "Bearer token for authentication"),
    ("headers", "Custom HTTP headers"),
    ("timeout", "Request timeout (default: 30s)"),
    ("max_retries", "Retry attempts (default: 3)"),
    ("rate_limit", "Requests per hour limit"),
    ("ssl_cert", "Path to SSL certificate file"),
    ("ssl_verify", "Verify SSL (default: true, set false for test servers)"),
]


# =============================================================================
# PUBLIC API - Called by CLI
# =============================================================================


def list_sdk_tools() -> None:
    """List tools provided by the MACSDK."""
    # Internal tools table (auto-included)
    internal_table = Table(
        title="🔧 Internal Tools (auto-included via get_sdk_tools)",
        title_style="bold cyan",
    )
    internal_table.add_column("Tool", style="cyan", no_wrap=True)
    internal_table.add_column("Category", style="yellow")
    internal_table.add_column("Description", style="white")
    internal_table.add_column("Parameters", style="dim")
    internal_table.add_column("Condition", style="magenta")

    for tool_info in INTERNAL_TOOLS:
        internal_table.add_row(
            tool_info["name"],
            tool_info["category"],
            tool_info["description"],
            tool_info["params"],
            tool_info["condition"],
        )

    console.print(internal_table)
    console.print()

    # Manual tools table
    manual_table = Table(
        title="🛠️  Manual Tools (add explicitly to get_tools)",
        title_style="bold green",
    )
    manual_table.add_column("Tool", style="cyan", no_wrap=True)
    manual_table.add_column("Category", style="yellow")
    manual_table.add_column("Description", style="white")
    manual_table.add_column("Parameters", style="dim")

    for tool_info in MANUAL_TOOLS:
        manual_table.add_row(
            tool_info["name"],
            tool_info["category"],
            tool_info["description"],
            tool_info["params"],
        )

    console.print(manual_table)
    console.print()

    # Service configuration options
    config_table = Table(title="⚙️  API Service Options")
    config_table.add_column("Option", style="cyan", no_wrap=True)
    config_table.add_column("Description", style="white")

    for opt_name, opt_desc in SERVICE_CONFIG_OPTIONS:
        config_table.add_row(opt_name, opt_desc)

    console.print(config_table)
    console.print()

    # Usage examples
    usage_text = """\
[bold]Using get_sdk_tools (recommended):[/bold]

[cyan]from macsdk.tools import api_get, fetch_file, get_sdk_tools[/cyan]

[cyan]def get_tools():[/cyan]
[cyan]    return [[/cyan]
[cyan]        *get_sdk_tools(__package__),  [dim]# calculate + auto-detect knowledge[/dim][/cyan]
[cyan]        api_get,[/cyan]
[cyan]        fetch_file,[/cyan]
[cyan]    ][/cyan]

[bold]Enabling knowledge tools:[/bold]

[dim]# Create directories with .md files[/dim]
[cyan]mkdir -p src/my_agent/skills src/my_agent/facts[/cyan]
[cyan]echo "---\\nname: example\\n---\\n# Example" > src/my_agent/skills/example.md[/cyan]

[dim]# read_skill and read_fact will be auto-detected on next run[/dim]

[bold]Registering API services:[/bold]

[cyan]from macsdk.core.api_registry import register_api_service[/cyan]

[cyan]register_api_service([/cyan]
[cyan]    "github",[/cyan]
[cyan]    "https://api.github.com",[/cyan]
[cyan]    token=os.environ["GITHUB_TOKEN"],[/cyan]
[cyan])[/cyan]
"""

    console.print(Panel(usage_text, title="Examples", border_style="green"))
