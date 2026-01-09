"""Command for creating new chatbots and agents.

This module provides functions for generating project scaffolding
using Jinja2 templates for clean separation of concerns.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..templates import TEMPLATES_DIR, render_template
from ..utils import derive_class_name, slugify

console = Console()


def _generate_uv_sources(macsdk_source: dict[str, str] | None) -> str:
    """Generate uv.sources section for pyproject.toml.

    Args:
        macsdk_source: Optional dict with 'type' and 'value'.

    Returns:
        UV sources section string or empty string.
    """
    if macsdk_source is None:
        return ""

    source_type = macsdk_source["type"]
    value = macsdk_source["value"]

    if source_type == "git":
        return f'\n[tool.uv.sources]\nmacsdk = {{ git = "{value}" }}\n'
    elif source_type == "path":
        return (
            f'\n[tool.uv.sources]\nmacsdk = {{ path = "{value}", editable = true }}\n'
        )

    return ""


# =============================================================================
# PUBLIC API - Called by CLI
# =============================================================================


def create_chatbot_project(
    name: str,
    display_name: str | None,
    description: str | None,
    output_dir: str,
    macsdk_source: dict[str, str] | None = None,
    with_rag: bool = False,
) -> None:
    """Create a new chatbot project using Jinja2 templates.

    Args:
        name: Project name (e.g., my-chatbot).
        display_name: Human-readable display name.
        description: Project description.
        output_dir: Output directory path.
        macsdk_source: Optional dict with 'type' (pip/git/path) and 'value'.
        with_rag: Include RAG agent for documentation Q&A.
    """
    project_slug = slugify(name)
    display_name = display_name or name.replace("-", " ").replace("_", " ").title()
    description = description or "A multi-agent chatbot built with MACSDK"

    output_path = Path(output_dir) / name

    if output_path.exists():
        console.print(f"[red]Error:[/red] Directory '{name}' already exists")
        raise SystemExit(1)

    # Prepare template context
    context = {
        "name": name,
        "project_slug": project_slug,
        "display_name": display_name,
        "description": description,
        "config_class_name": project_slug.title().replace("_", ""),
        "script_name": project_slug.replace("_", "-"),
        "with_rag": with_rag,
        "uv_sources": _generate_uv_sources(macsdk_source),
    }

    # Create directory structure
    src_dir = output_path / "src" / project_slug
    src_dir.mkdir(parents=True)

    # Render and write templates
    templates = [
        ("chatbot/__init__.py.j2", src_dir / "__init__.py"),
        ("chatbot/agents.py.j2", src_dir / "agents.py"),
        ("chatbot/prompts.py.j2", src_dir / "prompts.py"),
        ("chatbot/config.py.j2", src_dir / "config.py"),
        ("chatbot/cli.py.j2", src_dir / "cli.py"),
        ("chatbot/__main__.py.j2", src_dir / "__main__.py"),
        ("chatbot/py.typed.j2", src_dir / "py.typed"),
        ("chatbot/pyproject.toml.j2", output_path / "pyproject.toml"),
        ("chatbot/env.example.j2", output_path / ".env.example"),
        ("chatbot/config.yml.example.j2", output_path / "config.yml.example"),
        ("chatbot/README.md.j2", output_path / "README.md"),
        ("shared/gitignore.j2", output_path / ".gitignore"),
        ("shared/Containerfile.j2", output_path / "Containerfile"),
    ]

    for template_name, output_file in templates:
        content = render_template(template_name, context)
        output_file.write_text(content)

    # Create static files for web interface
    static_src = TEMPLATES_DIR / "chatbot" / "static"
    static_dst = output_path / "static"
    if static_src.exists():
        static_dst.mkdir(parents=True, exist_ok=True)
        # Render index.html template with project context
        index_template = static_src / "index.html.j2"
        if index_template.exists():
            content = render_template("chatbot/static/index.html.j2", context)
            (static_dst / "index.html").write_text(content)
        # Copy any other static files (CSS, JS, images) directly
        for item in static_src.iterdir():
            if item.suffix != ".j2":
                if item.is_file():
                    shutil.copy2(item, static_dst / item.name)
                elif item.is_dir():
                    shutil.copytree(item, static_dst / item.name)

    # Output success message
    console.print(f"\n[green]✓[/green] Created chatbot project: [bold]{name}[/bold]")
    if with_rag:
        console.print("[green]✓[/green] RAG agent included")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  cd {name}")
    console.print("  uv sync")
    if with_rag:
        console.print("  # Edit config.yml to configure RAG sources")
    console.print(f"  uv run {project_slug.replace('_', '-')}")


def create_agent_project(
    name: str,
    description: str | None,
    output_dir: str,
    macsdk_source: dict[str, str] | None = None,
    with_knowledge: bool = False,
) -> None:
    """Create a new agent project using Jinja2 templates.

    Args:
        name: Agent name (e.g., my-agent).
        description: Agent description.
        output_dir: Output directory path.
        macsdk_source: Optional dict with 'type' (pip/git/path) and 'value'.
        with_knowledge: Include knowledge tools (skills/facts) in the agent.
    """
    agent_slug = slugify(name)
    description = description or "A specialist agent for MACSDK chatbots"

    output_path = Path(output_dir) / name

    if output_path.exists():
        console.print(f"[red]Error:[/red] Directory '{name}' already exists")
        raise SystemExit(1)

    # Prepare template context
    agent_class = derive_class_name(name)
    package_name = agent_slug  # For use in templates
    context = {
        "name": name,
        "agent_slug": agent_slug,
        "agent_class": agent_class,
        "package_name": package_name,
        "description": description,
        "description_lower": description.lower(),
        "script_name": agent_slug.replace("_", "-"),
        "uv_sources": _generate_uv_sources(macsdk_source),
        "with_rag": False,  # Agents don't have RAG by default
        "with_knowledge": with_knowledge,
    }

    # Create directory structure
    src_dir = output_path / "src" / agent_slug
    src_dir.mkdir(parents=True)
    tests_dir = output_path / "tests"
    tests_dir.mkdir(parents=True)

    # Render and write templates
    templates = [
        ("agent/__init__.py.j2", src_dir / "__init__.py"),
        ("agent/config.py.j2", src_dir / "config.py"),
        ("agent/models.py.j2", src_dir / "models.py"),
        ("agent/tools.py.j2", src_dir / "tools.py"),
        ("agent/agent.py.j2", src_dir / "agent.py"),
        ("agent/cli.py.j2", src_dir / "cli.py"),
        ("agent/py.typed.j2", src_dir / "py.typed"),
        ("agent/test_agent.py.j2", tests_dir / "test_agent.py"),
        ("agent/pyproject.toml.j2", output_path / "pyproject.toml"),
        ("agent/env.example.j2", output_path / ".env.example"),
        ("agent/config.yml.example.j2", output_path / "config.yml.example"),
        ("agent/README.md.j2", output_path / "README.md"),
        ("shared/gitignore.j2", output_path / ".gitignore"),
        ("shared/Containerfile.j2", output_path / "Containerfile"),
    ]

    for template_name, output_file in templates:
        content = render_template(template_name, context)
        output_file.write_text(content)

    # Create knowledge directories and examples if requested
    if with_knowledge:
        skills_dir = src_dir / "skills"
        facts_dir = src_dir / "facts"
        skills_dir.mkdir(parents=True)
        facts_dir.mkdir(parents=True)

        # Render and write example skill
        skill_content = render_template("agent/skills/example-skill.md.j2", context)
        (skills_dir / "example-skill.md").write_text(skill_content)

        # Render and write example fact
        fact_content = render_template("agent/facts/example-fact.md.j2", context)
        (facts_dir / "example-fact.md").write_text(fact_content)

    # Output success message
    console.print(f"\n[green]✓[/green] Created agent: [bold]{name}[/bold]")
    if with_knowledge:
        console.print("  [green]✓[/green] Included knowledge tools (skills/facts)")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  cd {name}")
    console.print("  # Implement your tools in tools.py")
    if with_knowledge:
        console.print(
            "  # Add your skills and facts in src/{}/skills/ and src/{}/facts/".format(
                agent_slug, agent_slug
            )
        )
    console.print("  uv sync")
    console.print("  uv run pytest")
