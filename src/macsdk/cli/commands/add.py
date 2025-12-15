"""Command for adding agents to chatbots.

This module provides functions for adding agents to existing chatbot projects.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from rich.console import Console

from ..utils import derive_class_name

console = Console()


# =============================================================================
# PUBLIC API - Called by CLI
# =============================================================================


def add_agent_to_chatbot(
    chatbot_name: str,
    package: str | None,
    git: str | None,
    path: str | None,
) -> None:
    """Add an agent to an existing chatbot project.

    Args:
        chatbot_name: Path to the chatbot project directory.
        package: Pip package name (e.g., "weather-agent").
        git: Git repository URL.
        path: Local filesystem path.
    """
    if not any([package, git, path]):
        console.print("[red]Error:[/red] Must specify --package, --git, or --path")
        raise SystemExit(1)

    chatbot_path = Path(chatbot_name).resolve()

    if not chatbot_path.exists():
        console.print(f"[red]Error:[/red] Directory '{chatbot_name}' not found")
        raise SystemExit(1)

    # Find required files
    pyproject = _find_pyproject(chatbot_path)
    if not pyproject:
        console.print("[red]Error:[/red] No pyproject.toml found")
        raise SystemExit(1)

    agents_file = _find_agents_file(chatbot_path)
    if not agents_file:
        console.print("[red]Error:[/red] No agents.py found in src/*/")
        raise SystemExit(1)

    # Determine agent info and source configuration
    uv_source: str | None = None  # For [tool.uv.sources] section

    if package:
        agent_package = package.replace("-", "_")
        agent_class = derive_class_name(package)
        dependency = package
    elif git:
        # Extract package name from git URL
        match = re.search(r"/([^/]+?)(?:\.git)?$", git)
        if not match:
            console.print("[red]Error:[/red] Could not parse git URL")
            raise SystemExit(1)
        agent_name = match.group(1)
        agent_package = agent_name.replace("-", "_")
        agent_class = derive_class_name(agent_name)
        dependency = agent_name
        uv_source = f'{agent_name} = {{ git = "{git}" }}'
    elif path:
        agent_path = Path(path).resolve()
        if not agent_path.exists():
            console.print(f"[red]Error:[/red] Path '{path}' not found")
            raise SystemExit(1)
        agent_name = agent_path.name
        agent_package = agent_name.replace("-", "_")
        agent_class = derive_class_name(agent_name)
        dependency = agent_name
        # Add source with relative path for local development
        relative_path = _get_relative_path(chatbot_path, agent_path)
        uv_source = f'{agent_name} = {{ path = "{relative_path}", editable = true }}'

    console.print(f"Adding agent [bold]{agent_package}[/bold] to {chatbot_name}...")

    # Update pyproject.toml
    dep_added = _add_dependency_to_pyproject(pyproject, dependency)
    if dep_added:
        console.print("  [green]✓[/green] Added dependency to pyproject.toml")
    else:
        console.print("  [yellow]→[/yellow] Dependency already in pyproject.toml")

    # Add uv source if needed (for git or path)
    if uv_source:
        if _add_uv_source_to_pyproject(pyproject, uv_source):
            console.print("  [green]✓[/green] Added source to [tool.uv.sources]")
        else:
            console.print("  [yellow]→[/yellow] Source already configured")

    # Update agents.py
    if _add_agent_to_agents_file(agents_file, agent_package, agent_class):
        console.print("  [green]✓[/green] Added import and registration to agents.py")
    else:
        console.print("  [yellow]→[/yellow] Agent already in agents.py")

    # Run uv sync
    console.print("  [dim]Running uv sync...[/dim]")
    try:
        subprocess.run(
            ["uv", "sync"],
            cwd=chatbot_path,
            capture_output=True,
            check=True,
        )
        console.print("  [green]✓[/green] Dependencies installed")
    except subprocess.CalledProcessError as e:
        console.print(f"  [yellow]Warning:[/yellow] uv sync failed: {e}")
        console.print(f"  [dim]Run 'cd {chatbot_name} && uv sync' manually[/dim]")
    except FileNotFoundError:
        console.print("  [yellow]Warning:[/yellow] uv not found")
        console.print(f"  [dim]Run 'cd {chatbot_name} && uv sync' manually[/dim]")

    console.print("\n[green]✓[/green] Agent added successfully!")


# =============================================================================
# INTERNAL HELPERS
# =============================================================================


def _find_agents_file(chatbot_path: Path) -> Path | None:
    """Find the agents.py file in a chatbot project."""
    # Look for src/*/agents.py pattern
    for agents_file in chatbot_path.glob("src/*/agents.py"):
        return agents_file
    return None


def _find_pyproject(chatbot_path: Path) -> Path | None:
    """Find pyproject.toml in chatbot project."""
    pyproject = chatbot_path / "pyproject.toml"
    return pyproject if pyproject.exists() else None


def _get_relative_path(from_path: Path, to_path: Path) -> str:
    """Calculate relative path from one directory to another.

    Args:
        from_path: Source directory (e.g., chatbot directory).
        to_path: Target directory (e.g., agent directory).

    Returns:
        Relative path string (e.g., "../infra-agent").
    """
    try:
        return os.path.relpath(to_path, from_path)
    except ValueError:
        # On Windows, paths on different drives can't be relative
        return str(to_path)


def _add_dependency_to_pyproject(pyproject_path: Path, dependency: str) -> bool:
    """Add a dependency to pyproject.toml."""
    content = pyproject_path.read_text()

    # Check if already present (just the package name, not the full spec)
    dep_name = dependency.split("@")[0].split("[")[0].strip()
    if f'"{dep_name}"' in content or f"'{dep_name}'" in content:
        return False

    # Find dependencies section and add
    # This is a simple implementation - a proper TOML parser would be better
    if "dependencies = [" in content:
        content = content.replace(
            "dependencies = [",
            f'dependencies = [\n    "{dependency}",',
        )
        pyproject_path.write_text(content)
        return True

    return False


def _add_uv_source_to_pyproject(pyproject_path: Path, source_line: str) -> bool:
    """Add a source to [tool.uv.sources] in pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml.
        source_line: The source configuration line to add.

    Returns:
        True if added, False if already present.
    """
    content = pyproject_path.read_text()

    # Extract package name from source line
    match = re.match(r"^(\S+)\s*=", source_line)
    if not match:
        return False
    pkg_name = match.group(1)

    # Check if already present
    if f"{pkg_name} =" in content or f"{pkg_name}=" in content:
        return False

    # Check if [tool.uv.sources] section exists
    if "[tool.uv.sources]" in content:
        # Add after the section header
        content = content.replace(
            "[tool.uv.sources]",
            f"[tool.uv.sources]\n{source_line}",
        )
    else:
        # Add new section at the end
        content = content.rstrip() + f"\n\n[tool.uv.sources]\n{source_line}\n"

    pyproject_path.write_text(content)
    return True


def _add_agent_to_agents_file(
    agents_file: Path,
    agent_package: str,
    agent_class: str,
) -> bool:
    """Add agent import and registration to agents.py."""
    content = agents_file.read_text()

    # Check if already imported
    if f"from {agent_package}" in content:
        console.print(f"[yellow]Agent {agent_package} already imported[/yellow]")
        return False

    agent_name = agent_package.replace("-", "_")

    # Ensure register_agent is imported
    if "from macsdk.core import register_agent" not in content:
        # Check if there's a commented import we can uncomment
        if "# from macsdk.core import register_agent" in content:
            content = content.replace(
                "# from macsdk.core import register_agent",
                "from macsdk.core import register_agent",
            )
        elif "from macsdk.core import get_registry" in content:
            # Add register_agent to the existing import
            content = content.replace(
                "from macsdk.core import get_registry",
                "from macsdk.core import get_registry, register_agent",
            )
        else:
            # Add new import line
            lines = content.split("\n")
            import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("from ") or line.startswith("import "):
                    import_idx = i + 1
            lines.insert(import_idx, "from macsdk.core import register_agent")
            content = "\n".join(lines)

    # Find import section marker or create one
    import_marker = "# --- BEGIN AGENT IMPORTS ---"
    register_marker = "# --- BEGIN AGENT REGISTRATION ---"

    if import_marker in content:
        # Add after marker
        content = content.replace(
            import_marker,
            f"{import_marker}\nfrom {agent_package} import {agent_class}",
        )
    else:
        # Add import at top of file after existing imports
        lines = content.split("\n")
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                import_idx = i + 1
        lines.insert(import_idx, f"from {agent_package} import {agent_class}")
        content = "\n".join(lines)

    # Build registration code
    reg_code = f'    if not registry.is_registered("{agent_name}"):\n        register_agent({agent_class}())\n'

    if register_marker in content:
        # Add after marker
        content = content.replace(
            register_marker,
            f"{register_marker}\n{reg_code}",
        )
    else:
        # Find register_all_agents function and add registration inside it
        # Look for the placeholder comment or the _ = registry line
        if "_ = registry  # Avoid unused variable warning" in content:
            # Replace the placeholder with actual registration
            content = content.replace(
                "    _ = registry  # Avoid unused variable warning",
                reg_code.rstrip(),
            )
        elif "def register_all_agents" in content:
            # Find the end of register_all_agents by looking for the next function
            lines = content.split("\n")
            in_register_func = False
            insert_idx = -1

            for i, line in enumerate(lines):
                if "def register_all_agents" in line:
                    in_register_func = True
                elif in_register_func:
                    # Look for next function definition or end of indented block
                    if line.startswith("def ") or line.startswith("class "):
                        # Insert before this line
                        insert_idx = i
                        break
                    # Track last non-empty line in function
                    if line.strip() and not line.startswith("#"):
                        insert_idx = i + 1

            if insert_idx > 0:
                # Insert the registration code
                lines.insert(insert_idx, reg_code)
                content = "\n".join(lines)

    agents_file.write_text(content)
    return True
