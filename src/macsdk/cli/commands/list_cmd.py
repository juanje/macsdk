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

SDK_TOOLS = [
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


# =============================================================================
# PUBLIC API - Called by CLI
# =============================================================================


def list_sdk_tools() -> None:
    """List tools provided by the MACSDK."""
    table = Table(title="🔧 MACSDK Tools")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Parameters", style="dim")

    for tool_info in SDK_TOOLS:
        table.add_row(
            tool_info["name"],
            tool_info["category"],
            tool_info["description"],
            tool_info["params"],
        )

    console.print(table)
    console.print()

    # Usage example
    usage_text = """\
[bold]Usage in your agent:[/bold]

[cyan]from macsdk.tools import api_get, fetch_file[/cyan]
[cyan]from macsdk.core.api_registry import register_api_service[/cyan]

[dim]# Register your API service[/dim]
[cyan]register_api_service("myapi", "https://api.example.com")[/cyan]

[dim]# Use in a tool[/dim]
[cyan]@tool[/cyan]
[cyan]async def get_users():[/cyan]
[cyan]    return await api_get.ainvoke({[/cyan]
[cyan]        "service": "myapi",[/cyan]
[cyan]        "endpoint": "/users",[/cyan]
[cyan]        "extract": "$[*].name",  # JSONPath[/cyan]
[cyan]    })[/cyan]
"""

    console.print(Panel(usage_text, title="Example", border_style="green"))
