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
    # Tools table
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

    # Service configuration options
    config_table = Table(title="⚙️  API Service Options")
    config_table.add_column("Option", style="cyan", no_wrap=True)
    config_table.add_column("Description", style="white")

    for opt_name, opt_desc in SERVICE_CONFIG_OPTIONS:
        config_table.add_row(opt_name, opt_desc)

    console.print(config_table)
    console.print()

    # Usage example
    usage_text = """\
[bold]Register a service:[/bold]

[cyan]from macsdk.core.api_registry import register_api_service[/cyan]

[dim]# Basic service with token[/dim]
[cyan]register_api_service([/cyan]
[cyan]    "github",[/cyan]
[cyan]    "https://api.github.com",[/cyan]
[cyan]    token=os.environ["GITHUB_TOKEN"],[/cyan]
[cyan])[/cyan]

[dim]# Internal service with custom SSL cert[/dim]
[cyan]register_api_service([/cyan]
[cyan]    "internal",[/cyan]
[cyan]    "https://api.internal.company.com",[/cyan]
[cyan]    token=os.environ["INTERNAL_TOKEN"],[/cyan]
[cyan]    ssl_cert="/path/to/company-ca.pem",[/cyan]
[cyan])[/cyan]

[dim]# Test server (no SSL verification)[/dim]
[cyan]register_api_service([/cyan]
[cyan]    "test",[/cyan]
[cyan]    "https://localhost:8443",[/cyan]
[cyan]    ssl_verify=False,  [red]# Insecure![/red][/cyan]
[cyan])[/cyan]

[bold]Use in your tools:[/bold]

[cyan]@tool[/cyan]
[cyan]async def get_users():[/cyan]
[cyan]    return await api_get.ainvoke({[/cyan]
[cyan]        "service": "github",[/cyan]
[cyan]        "endpoint": "/users",[/cyan]
[cyan]        "extract": "$[*].login",  # JSONPath[/cyan]
[cyan]    })[/cyan]
"""

    console.print(Panel(usage_text, title="Examples", border_style="green"))
