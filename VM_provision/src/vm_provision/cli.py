"""CLI for Vm Provision.

This provides commands for running and inspecting the chatbot.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    """Vm Provision - A multi-agent chatbot built with MACSDK"""
    if version:
        console.print("[bold cyan]Vm Provision[/] [dim]v0.1.0[/]")
        return

    # Show help if no subcommand
    if ctx.invoked_subcommand is None:
        _show_welcome()


def _show_welcome() -> None:
    """Show a welcome panel with available commands."""
    title = Text("Vm Provision", style="bold cyan")
    subtitle = Text("A multi-agent chatbot built with MACSDK", style="dim")

    commands_table = Table(show_header=False, box=None, padding=(0, 2))
    commands_table.add_column("Command", style="green")
    commands_table.add_column("Description", style="dim")

    commands_table.add_row("chat", "Start interactive CLI chat")
    commands_table.add_row("web", "Start web interface")
    commands_table.add_row("agents", "List registered agents")
    commands_table.add_row("tools", "List tools for agents")
    commands_table.add_row("info", "Show configuration")

    panel = Panel(
        commands_table,
        title=title,
        subtitle=subtitle,
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)

    console.print("\n[dim]Examples:[/]")
    console.print("  [green]vm-provision chat[/]   Start CLI chat")
    console.print("  [green]vm-provision web[/]    Start web at localhost:8000")
    console.print("  [green]vm-provision --help[/] Show all options\n")


@cli.command(name="tools")
@click.argument("agent_name", required=False)
@click.option("--all", "-a", "show_all", is_flag=True, help="Show tools for all agents")
@click.pass_context
def tools_command(ctx: click.Context, agent_name: str | None, show_all: bool) -> None:
    """List tools for a specific agent or all agents.

    \b
    Examples:
      vm-provision tools              # Show available agents
      vm-provision tools api_agent    # Show tools for api_agent
      vm-provision tools --all        # Show tools for all agents
    """
    # Lazy import to avoid loading heavy dependencies
    from macsdk.core import get_registry

    from . import agents

    agents.register_all_agents()
    registry = get_registry()
    registered = agents.get_registered_agents()

    console.print()

    # Case 1: Show all agents with their tools
    if show_all:
        if not registered:
            console.print(
                Panel(
                    "[dim]No agents registered yet.\n\n"
                    "Add agents in [white]src/vm_provision/agents.py[/][/]",
                    title="[bold]🤖 Agents & Tools[/]",
                    border_style="yellow",
                )
            )
            return

        for agent_info in registered:
            name = agent_info.get("name", "Unknown")
            agent = registry.get(name)
            agent_tools = getattr(agent, "tools", [])

            console.print(f"[bold cyan]{name}[/] [dim]({len(agent_tools)} tools)[/]")

            if not agent_tools:
                console.print("  [dim]No tools available[/]\n")
                continue

            table = Table(
                show_header=True,
                header_style="bold magenta",
                border_style="dim",
                box=None,
                padding=(0, 2),
            )
            table.add_column("Tool", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")

            for t in agent_tools:
                tool_name = t.name
                description = t.description or "No description"
                first_line = description.split("\n")[0].strip()
                table.add_row(tool_name, first_line)

            console.print(table)
            console.print()

        return

    # Case 2: Show tools for specific agent
    if agent_name is not None:
        if not registry.is_registered(agent_name):
            console.print(f"[red]✗ Error:[/] Agent '{agent_name}' not found")
            console.print(
                "[dim]Use[/] [green]vm-provision agents[/] "
                "[dim]to see registered agents.[/]\n"
            )
            return

        agent = registry.get(agent_name)
        agent_tools = getattr(agent, "tools", [])

        if not agent_tools:
            console.print(f"[yellow]Agent '{agent_name}' has no tools[/]\n")
            return

        table = Table(
            title=f"[bold]🔧 Tools for {agent_name}[/]",
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
            title_justify="left",
        )
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for t in agent_tools:
            tool_name = t.name
            description = t.description or "No description"
            first_line = description.split("\n")[0].strip()
            table.add_row(tool_name, first_line)

        console.print(table)
        console.print(f"\n[dim]Total: {len(agent_tools)} tools[/]\n")
        return

    # Case 3: No argument - show agents with hint about tools command
    console.print(
        "[yellow]💡 Tip:[/] Chatbots use [cyan]agents[/], not tools directly.\n"
        "   Each agent has its own tools. Showing agents instead:\n"
    )
    ctx.invoke(list_agents)
    console.print(
        "[dim]To see tools for a specific agent:[/]\n"
        "  [green]vm-provision tools <agent_name>[/]\n"
        "\n[dim]To see all tools for all agents:[/]\n"
        "  [green]vm-provision tools --all[/]\n"
    )


@cli.command(name="agents")
def list_agents() -> None:
    """List all registered agents and their capabilities."""
    # Lazy import to avoid loading heavy dependencies
    from . import agents

    registered = agents.get_registered_agents()

    console.print()
    if not registered:
        console.print(
            Panel(
                "[dim]No agents registered yet.\n\n"
                "Add agents in [white]src/vm_provision/agents.py[/][/]",
                title="[bold]🤖 Agents[/]",
                border_style="yellow",
            )
        )
        return

    table = Table(
        title="[bold]🤖 Registered Agents[/]",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        title_justify="left",
    )
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Tools", style="green", justify="center")

    for agent_info in registered:
        name = agent_info.get("name", "Unknown")
        description = agent_info.get("description", "No description")
        tools_count = agent_info.get("tools_count", 0)
        table.add_row(name, description, str(tools_count))

    console.print(table)
    console.print(f"\n[dim]Total: {len(registered)} agents registered[/]\n")


@cli.command()
def info() -> None:
    """Show chatbot information and configuration."""
    # Lazy import
    from macsdk.core import ConfigurationError, create_config

    from . import agents

    console.print()

    # Build info content
    info_text = Text()
    info_text.append("A multi-agent chatbot built with MACSDK\n\n", style="dim")

    # Show config status
    try:
        config = create_config(search_path=Path.cwd())

        # Supervisor configuration
        info_text.append("Supervisor Model: ", style="dim")
        info_text.append(f"{config.llm_model}\n", style="cyan")
        info_text.append("Temperature: ", style="dim")
        info_text.append(f"{config.llm_temperature}\n", style="cyan")

        # Registered agents
        registered = agents.get_registered_agents()
        agent_names = [a.get("name", "?") for a in registered]
        info_text.append("Agents: ", style="dim")
        info_text.append(f"{', '.join(agent_names) or 'None'}\n", style="cyan")


        info_text.append("\n")
        info_text.append("✓ Configuration loaded successfully", style="green")

    except ConfigurationError as e:
        info_text.append(f"⚠ Configuration error: {e}", style="red")

    panel = Panel(
        info_text,
        title="[bold cyan]Vm Provision[/]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    console.print(
        "\n[dim]Use[/] [green]vm-provision agents[/] "
        "[dim]to see agent details.[/]\n"
    )


@cli.command()
@click.option(
    "--show-llm-calls",
    is_flag=True,
    help="Show LLM prompts and responses in logs",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (-v=INFO, -vv=DEBUG)",
)
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (ERROR level)")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Set log level explicitly",
)
@click.option("--log-file", type=click.Path(), help="Custom log file path")
def chat(
    show_llm_calls: bool,
    verbose: int,
    quiet: bool,
    log_level: str | None,
    log_file: str | None,
) -> None:
    """Start interactive chat with the chatbot."""
    # Lazy import heavy dependencies
    from macsdk.core import (
        ConfigurationError,
        configure_cli_logging,
        create_chatbot_graph,
        create_config,
    )
    from macsdk.interfaces import run_cli_chatbot

    from . import agents

    try:
        # Load config from project root
        _config = create_config(search_path=Path.cwd())
        _config.validate_api_key()

        # Setup logging (encapsulated helper)
        try:
            actual_log, debug_enabled = configure_cli_logging(
                show_llm_calls=show_llm_calls,
                verbose=verbose,
                quiet=quiet,
                log_level=log_level,
                log_file=log_file,
                config=_config,
                app_name="vm_provision",
                log_to_stderr=False,
            )
            if actual_log:
                console.print(f"[dim]📋 Logs: {actual_log}[/]\n")
        except OSError as e:
            error_console.print(f"[red]✗ Failed to setup logging:[/] {e}")
            sys.exit(1)

        # Update global config singleton so nested agents also see debug flag
        if debug_enabled:
            from macsdk.core import config as global_config
            global_config.debug = True
            console.print("[yellow]🔍 LLM calls will be logged[/]\n")

        graph = create_chatbot_graph(agents.register_all_agents, debug=debug_enabled)
        run_cli_chatbot(
            graph=graph,
            title="Vm Provision",
        )
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration Error:[/] {e}")
        sys.exit(1)


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=8000, help="Port to bind to")
@click.option(
    "--show-llm-calls",
    is_flag=True,
    help="Show LLM prompts and responses in logs",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (-v=INFO, -vv=DEBUG)",
)
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (ERROR level)")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Set log level explicitly",
)
@click.option("--log-file", type=click.Path(), help="Custom log file path")
def web(
    host: str,
    port: int,
    show_llm_calls: bool,
    verbose: int,
    quiet: bool,
    log_level: str | None,
    log_file: str | None,
) -> None:
    """Start the web interface.

    Launches a FastAPI server with WebSocket support for real-time chat.
    Open your browser at http://localhost:PORT after starting.
    """
    # Lazy import heavy dependencies
    from macsdk.core import (
        ConfigurationError,
        configure_cli_logging,
        create_chatbot_graph,
        create_config,
    )
    from macsdk.interfaces import run_web_server

    from . import agents

    try:
        _config = create_config(search_path=Path.cwd())
        _config.validate_api_key()

        # Setup logging (encapsulated helper)
        try:
            actual_log, debug_enabled = configure_cli_logging(
                show_llm_calls=show_llm_calls,
                verbose=verbose,
                quiet=quiet,
                log_level=log_level,
                log_file=log_file,
                config=_config,
                app_name="vm_provision",
                log_to_stderr=True,  # Web mode logs to stderr
            )
        except OSError as e:
            error_console.print(f"[red]✗ Failed to setup logging:[/] {e}")
            sys.exit(1)

        # Update global config singleton so nested agents also see debug flag
        if debug_enabled:
            from macsdk.core import config as global_config
            global_config.debug = True

        # Look for static files in project root
        static_path = Path.cwd() / "static"
        static_dir: Path | None = static_path if static_path.exists() else None

        console.print()
        debug_msg = " [yellow](LLM calls logging)[/]" if debug_enabled else ""
        console.print(
            Panel(
                f"[dim]Starting server at[/] [cyan]http://{host}:{port}[/]{debug_msg}\n"
                "[dim]Press[/] [white]Ctrl+C[/] [dim]to stop[/]",
                title="[bold cyan]🌐 Web Interface[/]",
                border_style="cyan",
            )
        )
        console.print()

        graph = create_chatbot_graph(agents.register_all_agents, debug=debug_enabled)
        run_web_server(
            graph=graph,
            title="Vm Provision",
            static_dir=static_dir,
            host=host,
            port=port,
        )
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration Error:[/] {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
