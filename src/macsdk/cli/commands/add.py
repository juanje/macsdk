"""Command for adding agents to chatbots.

This module provides functions for adding agents to existing chatbot projects.
Supports both remote agents (external packages) and local agents (mono-repo).
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404
import tomllib
from pathlib import Path

from rich.console import Console

from ..templates import render_template
from ..utils import derive_class_name, slugify

console = Console()


def _find_import_insert_position(lines: list[str]) -> int:
    """Find the correct position to insert a new import statement.

    Respects:
    - Module docstrings (single or triple quotes)
    - from __future__ imports (must be first)
    - Existing import blocks

    Args:
        lines: List of file lines.

    Returns:
        Line index where new import should be inserted.
    """
    import_idx = 0
    in_docstring = False
    docstring_char = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track docstrings (triple quotes, including raw strings r""")
        if not in_docstring:
            # Handle regular and raw string docstrings
            if stripped.startswith(('"""', "'''")):
                docstring_char = stripped[:3]
            elif stripped.startswith(('r"""', "r'''")):
                docstring_char = stripped[1:4]  # Skip 'r' prefix
            else:
                docstring_char = None

            if docstring_char:
                # Check if docstring ends on same line
                if stripped.count(docstring_char) >= 2:
                    import_idx = i + 1
                else:
                    in_docstring = True
                continue
        else:
            if docstring_char and docstring_char in stripped:
                in_docstring = False
                import_idx = i + 1
            continue

        # Skip empty lines and comments at the start
        if not stripped or stripped.startswith("#"):
            if import_idx == 0:
                import_idx = i + 1
            continue

        # __future__ imports must come first, always skip past them
        if stripped.startswith("from __future__"):
            import_idx = i + 1
            continue

        # Found a top-level import, track position after it
        # Only consider unindented lines to avoid local imports inside functions
        is_top_level = not line.startswith((" ", "\t"))
        is_import = stripped.startswith("from ") or stripped.startswith("import ")
        if is_import and is_top_level:
            import_idx = i + 1

    return import_idx


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
        subprocess.run(  # nosec B603, B607
            ["uv", "sync"],  # Controlled command, no user input
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


def add_local_agent_to_chatbot(
    chatbot_name: str,
    agent_name: str,
    description: str | None = None,
) -> None:
    """Create and add a local agent to a chatbot project (mono-repo).

    This creates the agent files inside the chatbot's source directory
    under local_agents/, then updates agents.py with relative imports.

    Args:
        chatbot_name: Path to the chatbot project directory.
        agent_name: Name for the new agent (e.g., "weather").
        description: Optional description for the agent.
    """
    chatbot_path = Path(chatbot_name).resolve()

    if not chatbot_path.exists():
        console.print(f"[red]Error:[/red] Directory '{chatbot_name}' not found")
        raise SystemExit(1)

    # Find chatbot slug
    chatbot_slug = _find_chatbot_slug(chatbot_path)
    if not chatbot_slug:
        console.print("[red]Error:[/red] Could not find chatbot package in src/")
        raise SystemExit(1)

    agents_file = _find_agents_file(chatbot_path)
    if not agents_file:
        console.print("[red]Error:[/red] No agents.py found in src/*/")
        raise SystemExit(1)

    agent_slug = slugify(agent_name)
    agent_class = derive_class_name(agent_name)

    console.print(
        f"Creating local agent [bold]{agent_slug}[/bold] in {chatbot_name}..."
    )

    # Create local agent directory and files
    agent_dir = _create_local_agent(
        chatbot_path, chatbot_slug, agent_slug, agent_class, description
    )
    console.print(
        f"  [green]✓[/green] Created agent in {agent_dir.relative_to(chatbot_path)}"
    )

    # Update agents.py with relative import
    if _add_agent_to_agents_file(agents_file, agent_slug, agent_class, is_local=True):
        console.print("  [green]✓[/green] Added import and registration to agents.py")
    else:
        console.print("  [yellow]→[/yellow] Agent already in agents.py")

    console.print("\n[green]✓[/green] Local agent created successfully!")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  1. Implement your tools in local_agents/{agent_slug}/tools.py")
    console.print(f"  2. Customize the prompt in local_agents/{agent_slug}/prompts.py")
    console.print(f"  3. Run: uv run {chatbot_slug.replace('_', '-')}")


# =============================================================================
# INTERNAL HELPERS
# =============================================================================


def _find_chatbot_slug(chatbot_path: Path) -> str | None:
    """Find the chatbot package slug from src/ directory.

    First tries to derive the slug from pyproject.toml project name,
    then falls back to scanning src/ directory.

    Args:
        chatbot_path: Path to the chatbot project.

    Returns:
        The chatbot package slug (e.g., "my_chatbot") or None.
    """
    src_dir = chatbot_path / "src"
    if not src_dir.exists():
        return None

    # Try to get project name from pyproject.toml first (most reliable)
    pyproject = chatbot_path / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text())
            project_name = data.get("project", {}).get("name")
            if project_name:
                expected_slug = slugify(project_name)
                # Verify this package exists in src/
                expected_pkg = src_dir / expected_slug
                if expected_pkg.is_dir() and (expected_pkg / "__init__.py").exists():
                    return expected_slug
        except tomllib.TOMLDecodeError:
            pass  # Fall back to directory scan

    # Fallback: scan src/ for packages
    # Prioritize package matching the project directory name (most common convention)
    project_dir_slug = slugify(chatbot_path.name)
    packages = [
        item.name
        for item in src_dir.iterdir()
        if item.is_dir() and (item / "__init__.py").exists()
    ]

    if not packages:
        return None

    # Return matching package first, otherwise first found
    if project_dir_slug in packages:
        return project_dir_slug

    return packages[0]


def _create_local_agent(
    chatbot_path: Path,
    chatbot_slug: str,
    agent_slug: str,
    agent_class: str,
    description: str | None,
) -> Path:
    """Create local agent files inside the chatbot project.

    Args:
        chatbot_path: Path to the chatbot project.
        chatbot_slug: The chatbot package slug.
        agent_slug: The agent slug (e.g., "weather").
        agent_class: The agent class name (e.g., "WeatherAgent").
        description: Optional agent description.

    Returns:
        Path to the created agent directory.

    Raises:
        SystemExit: If agent already exists or slug is invalid.
    """
    # Validate agent_slug is a valid Python identifier
    if not agent_slug.isidentifier():
        console.print(
            f"[red]Error:[/red] '{agent_slug}' is not a valid Python identifier. "
            "Use only letters, numbers, and underscores (cannot start with a number)."
        )
        raise SystemExit(1)

    # Create local_agents directory if needed
    local_agents_dir = chatbot_path / "src" / chatbot_slug / "local_agents"
    local_agents_dir.mkdir(exist_ok=True)

    # Create __init__.py for local_agents package if needed
    local_agents_init = local_agents_dir / "__init__.py"
    if not local_agents_init.exists():
        local_agents_init.write_text(
            '"""Local agents for this chatbot (mono-repo approach)."""\n'
        )

    # Create agent directory
    agent_dir = local_agents_dir / agent_slug
    if agent_dir.exists():
        console.print(f"[red]Error:[/red] Agent '{agent_slug}' already exists")
        raise SystemExit(1)

    agent_dir.mkdir()

    # Prepare template context
    description = (
        description or f"A specialist agent for {agent_slug.replace('_', ' ')}"
    )
    context = {
        "name": agent_slug.replace("_", "-"),
        "agent_slug": agent_slug,
        "agent_class": agent_class,
        "description": description,
        "description_lower": description.lower(),
        "script_name": agent_slug.replace("_", "-"),
        "with_rag": False,
    }

    # Render and write agent templates (subset - no pyproject, README, etc.)
    templates = [
        ("agent/__init__.py.j2", agent_dir / "__init__.py"),
        ("agent/config.py.j2", agent_dir / "config.py"),
        ("agent/models.py.j2", agent_dir / "models.py"),
        ("agent/agent.py.j2", agent_dir / "agent.py"),
        ("agent/tools.py.j2", agent_dir / "tools.py"),
        ("agent/prompts.py.j2", agent_dir / "prompts.py"),
    ]

    for template_name, output_file in templates:
        content = render_template(template_name, context)
        output_file.write_text(content)

    return agent_dir


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
    is_local: bool = False,
) -> bool:
    """Add agent import and registration to agents.py.

    Args:
        agents_file: Path to the agents.py file.
        agent_package: Package/module name for the agent.
        agent_class: Class name for the agent.
        is_local: If True, use relative imports for local agents.

    Returns:
        True if added, False if already present.
    """
    content = agents_file.read_text()

    # Determine import statement based on local vs remote
    if is_local:
        import_stmt = f"from .local_agents.{agent_package} import {agent_class}"
    else:
        import_stmt = f"from {agent_package} import {agent_class}"

    # Check if already imported (use word boundaries to avoid partial matches)
    # e.g., "api" should not match "api_utils"
    remote_pattern = rf"from\s+{re.escape(agent_package)}\b"
    local_pattern = rf"\.local_agents\.{re.escape(agent_package)}\b"
    if re.search(remote_pattern, content) or re.search(local_pattern, content):
        console.print(f"[yellow]Agent {agent_package} already imported[/yellow]")
        return False

    agent_name = agent_package.replace("-", "_")

    # Ensure register_agent is imported (use regex to avoid false positives from comments)
    # Matches: "from x import register_agent" or "from x import a, register_agent"
    has_register_agent_import = (
        re.search(
            r"^\s*from\s+\S+\s+import\s+.*\bregister_agent\b", content, re.MULTILINE
        )
        is not None
    )
    if not has_register_agent_import:
        # Prefer adding to existing get_registry import (more robust)
        if "from macsdk.core import get_registry" in content:
            content = content.replace(
                "from macsdk.core import get_registry",
                "from macsdk.core import get_registry, register_agent",
            )
        else:
            # Add new import line at correct position
            lines = content.split("\n")
            import_idx = _find_import_insert_position(lines)
            lines.insert(import_idx, "from macsdk.core import register_agent")
            content = "\n".join(lines)

    # Find import section marker or create one
    import_marker = "# --- BEGIN AGENT IMPORTS ---"
    register_marker = "# --- BEGIN AGENT REGISTRATION ---"

    if import_marker in content:
        # Add after marker
        content = content.replace(
            import_marker,
            f"{import_marker}\n{import_stmt}",
        )
    else:
        # Add import at correct position (after docstrings, __future__, existing imports)
        lines = content.split("\n")
        import_idx = _find_import_insert_position(lines)
        lines.insert(import_idx, import_stmt)
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
