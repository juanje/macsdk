"""Command for listing registered agents.

This module provides functions for listing agents in chatbot projects.
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


# =============================================================================
# PUBLIC API - Called by CLI
# =============================================================================


def list_agents_in_chatbot(chatbot_dir: str) -> None:
    """List registered agents in a chatbot project.

    Args:
        chatbot_dir: Path to the chatbot project directory.
    """
    chatbot_path = Path(chatbot_dir).absolute()

    if not chatbot_path.exists():
        console.print(f"[red]Error:[/red] Directory '{chatbot_dir}' not found")
        raise SystemExit(1)

    # Find the agents.py file
    agents_file = None
    for f in chatbot_path.glob("src/*/agents.py"):
        agents_file = f
        break

    if not agents_file:
        console.print("[red]Error:[/red] No agents.py found in src/*/")
        console.print(
            "\n[dim]Make sure you're in a MACSDK chatbot project directory.[/dim]"
        )
        raise SystemExit(1)

    # Try to import and run the chatbot's agents module
    # This will register the agents with the global registry
    src_dir = agents_file.parent.parent
    module_name = agents_file.parent.name

    # Add src to path temporarily
    sys.path.insert(0, str(src_dir))

    try:
        # Import the agents module
        import importlib

        agents_module = importlib.import_module(f"{module_name}.agents")

        # Call register_all_agents if it exists
        if hasattr(agents_module, "register_all_agents"):
            agents_module.register_all_agents()

        # Now import the registry and list agents
        # This import is done here to avoid loading heavy deps on --help
        from macsdk.core import get_registry

        registry = get_registry()
        all_agents = registry.get_all()

        if not all_agents:
            console.print("[yellow]No agents registered.[/yellow]")
            console.print(
                "\n[dim]Add agents to src/{}/agents.py or use:[/dim]".format(
                    module_name
                )
            )
            console.print("  macsdk add-agent . --package your-agent")
            return

        table = Table(title="Registered Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Capabilities", style="green")

        for name, agent in all_agents.items():
            # Truncate capabilities for display
            caps = agent.capabilities
            if len(caps) > 60:
                caps = caps[:57] + "..."
            table.add_row(name, caps)

        console.print(table)

    except ImportError as e:
        console.print(f"[red]Error:[/red] Could not import agents module: {e}")
        console.print("\n[dim]Make sure dependencies are installed: uv sync[/dim]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
    finally:
        # Clean up sys.path
        if str(src_dir) in sys.path:
            sys.path.remove(str(src_dir))
