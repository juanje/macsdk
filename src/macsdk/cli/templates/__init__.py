"""Jinja2 templates for project scaffolding.

This module provides template rendering utilities for generating
chatbot and agent projects.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory path
TEMPLATES_DIR = Path(__file__).parent


def get_template_env() -> Environment:
    """Get the Jinja2 template environment.

    Returns:
        Configured Jinja2 Environment.
    """
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(default=False),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(template_path: str, context: dict) -> str:
    """Render a template with the given context.

    Args:
        template_path: Path to template relative to templates dir.
        context: Variables to pass to the template.

    Returns:
        Rendered template content.
    """
    env = get_template_env()
    template = env.get_template(template_path)
    return template.render(**context)
