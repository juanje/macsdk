"""CLI for api-agent.

This provides commands for testing and inspecting the agent.
"""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
error_console = Console(stderr=True)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", "-v", is_flag=True, help="Show version and exit")
def cli(ctx: click.Context, version: bool) -> None:
    """api-agent - REST API interactions using JSONPlaceholder."""
    if version:
        console.print("[bold cyan]api-agent[/] [dim]v0.1.0[/]")
        return

    # Show help if no subcommand
    if ctx.invoked_subcommand is None:
        _show_welcome()


def _show_welcome() -> None:
    """Show a welcome panel with available commands."""
    title = Text("api-agent", style="bold cyan")
    subtitle = Text("REST API interactions using JSONPlaceholder", style="dim")

    commands_table = Table(show_header=False, box=None, padding=(0, 2))
    commands_table.add_column("Command", style="green")
    commands_table.add_column("Description", style="dim")

    commands_table.add_row("chat", "Start interactive chat")
    commands_table.add_row("tools", "List available tools")
    commands_table.add_row("info", "Show agent information")

    panel = Panel(
        commands_table,
        title=title,
        subtitle=subtitle,
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)

    console.print("\n[dim]Examples:[/]")
    console.print("  [green]api-agent chat[/]   Start interactive chat")
    console.print("  [green]api-agent tools[/]  List available tools")
    console.print("  [green]api-agent --help[/] Show all options\n")


@cli.command()
def tools() -> None:
    """List available tools and their descriptions."""
    # Lazy import to avoid loading heavy dependencies
    from .tools import TOOLS

    console.print()
    table = Table(
        title="[bold]🔧 Available Tools[/]",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        title_justify="left",
    )
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    for tool in TOOLS:
        name = tool.name
        description = tool.description or "No description"
        # Get first line of description
        first_line = description.split("\n")[0].strip()
        table.add_row(name, first_line)

    console.print(table)
    console.print(f"\n[dim]Total: {len(TOOLS)} tools available[/]\n")


@cli.command()
def info() -> None:
    """Show agent information and capabilities."""
    # Lazy import
    from .agent import CAPABILITIES
    from .tools import TOOLS

    console.print()
    panel = Panel(
        f"[white]{CAPABILITIES}[/]",
        title="[bold cyan]api-agent[/]",
        subtitle=f"[dim]{len(TOOLS)} tools available[/]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    console.print(
        "\n[dim]Use[/] [green]api-agent tools[/] [dim]to see tool details.[/]\n"
    )


@cli.command()
def chat() -> None:
    """Start interactive chat with the agent."""
    # Lazy import heavy dependencies
    import asyncio
    from pathlib import Path

    from macsdk.core import ConfigurationError, create_config

    from .agent import run_api_agent

    console.print()
    console.print(
        Panel(
            "[dim]Type [white]exit[/] or press [white]Ctrl+C[/] to quit[/]",
            title="[bold cyan]api-agent Chat[/]",
            border_style="cyan",
        )
    )
    console.print()

    # Load config from current directory (standalone mode)
    try:
        _config = create_config(search_path=Path.cwd())
        _config.validate_api_key()
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration Error:[/] {e}")
        sys.exit(1)

    async def run() -> None:
        while True:
            try:
                query = console.input("[bold green]>> [/]")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Goodbye![/]")
                break

            if query.strip().lower() in ("exit", "quit"):
                console.print("[dim]Goodbye![/]")
                break
            if not query.strip():
                continue

            try:
                with console.status("[cyan]Processing...[/]", spinner="dots"):
                    result = await run_api_agent(query)
                console.print()
                console.print(
                    Panel(
                        result["response"],
                        title="[bold blue]Response[/]",
                        border_style="blue",
                        padding=(1, 2),
                    )
                )
                console.print()
            except ConfigurationError as e:
                error_console.print(f"\n[red]✗ Configuration Error:[/] {e}")
                sys.exit(1)
            except Exception as e:
                error_console.print(f"\n[red]✗ Error:[/] {e}")

    asyncio.run(run())


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
