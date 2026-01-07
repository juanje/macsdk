"""Main CLI entry point for MACSDK.

This module uses lazy imports to ensure fast startup time.
Heavy dependencies (langchain, langgraph) are only loaded
when commands that need them are executed.
"""

from __future__ import annotations

import click

# Import version from lightweight module (avoids loading heavy __init__.py)
from .._version import __repo_url__, __version__


@click.group()
@click.version_option(version=__version__, prog_name="macsdk")
def cli() -> None:
    """MACSDK - Multi-Agent Chatbot SDK.

    Build customizable multi-agent chatbots with ease.

    \b
    Quick Start:
      macsdk new chatbot my-chatbot    Create a new chatbot project
      macsdk new agent my-agent        Create a new agent
      macsdk add-agent . --path ../agent   Add an agent to current chatbot
    """
    pass


@cli.command()
@click.argument("project_type", type=click.Choice(["chatbot", "agent"]))
@click.argument("name")
@click.option("--display-name", "-n", help="Display name (chatbot only)")
@click.option("--description", "-d", help="Description")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory (default: current directory)",
)
@click.option(
    "--macsdk-git",
    "-G",
    is_flag=True,
    help="Install macsdk from GitHub (latest development version)",
)
@click.option(
    "--macsdk-path",
    "-M",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Install macsdk from a local path",
)
@click.option(
    "--with-rag/--no-rag",
    "-R/-r",
    default=False,
    help="Include RAG agent (chatbot only, default: no)",
)
@click.option(
    "--with-knowledge/--no-knowledge",
    "-K/-k",
    default=False,
    help="Include knowledge tools (agent only, default: no)",
)
def new(
    project_type: str,
    name: str,
    display_name: str | None,
    description: str | None,
    output_dir: str,
    macsdk_git: bool,
    macsdk_path: str | None,
    with_rag: bool,
    with_knowledge: bool,
) -> None:
    """Create a new chatbot or agent project.

    \b
    MACSDK Source Options:
      Default:      Install from pip (when published)
      --macsdk-git: Install from GitHub repo (latest version)
      --macsdk-path: Install from local path (for development)

    \b
    Chatbot Options:
      --with-rag:       Include RAG agent for documentation Q&A
      --no-rag:         Don't include RAG agent (default)

    \b
    Agent Options:
      --with-knowledge: Include knowledge tools (skills/facts)
      --no-knowledge:   Don't include knowledge tools (default)

    \b
    Examples:
      macsdk new chatbot my-assistant --display-name "My Assistant"
      macsdk new chatbot docs-bot --with-rag  # With RAG for docs Q&A
      macsdk new agent weather-agent
      macsdk new agent devops-agent --with-knowledge  # With skills/facts
      macsdk new chatbot my-bot --macsdk-git
      macsdk new agent my-agent --macsdk-path /path/to/macsdk
    """
    # Lazy import to avoid loading heavy dependencies
    from .commands.new import create_agent_project, create_chatbot_project

    # Determine macsdk source configuration
    macsdk_source: dict[str, str] | None = None
    if macsdk_path:
        macsdk_source = {"type": "path", "value": macsdk_path}
    elif macsdk_git:
        macsdk_source = {"type": "git", "value": __repo_url__}

    if project_type == "chatbot":
        if with_knowledge:
            click.echo("Note: --with-knowledge is only applicable to agents, ignoring.")
        create_chatbot_project(
            name, display_name, description, output_dir, macsdk_source, with_rag
        )
    else:
        if with_rag:
            click.echo("Note: --with-rag is only applicable to chatbots, ignoring.")
        create_agent_project(
            name, description, output_dir, macsdk_source, with_knowledge
        )


@cli.command(name="add-agent")
@click.argument(
    "chatbot_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
)
@click.option("--package", "-p", help="Agent pip package name (remote)")
@click.option("--git", "-g", help="Agent git repository URL (remote)")
@click.option("--path", "-P", help="Agent local directory path (remote)")
@click.option("--new", "-n", "new_agent", help="Create new local agent with this name")
@click.option("--description", "-d", help="Description for new local agent")
def add_agent(
    chatbot_dir: str,
    package: str | None,
    git: str | None,
    path: str | None,
    new_agent: str | None,
    description: str | None,
) -> None:
    """Add an agent to a chatbot project.

    CHATBOT_DIR is the path to the chatbot project directory.
    Use "." for the current directory.

    \b
    Remote Agents (external packages):
      --package: Install from pip
      --git:     Install from git repository
      --path:    Link to local directory

    \b
    Local Agents (mono-repo):
      --new:     Create a new agent inside the chatbot project

    \b
    Examples:
      # Remote agents
      macsdk add-agent . --package weather-agent
      macsdk add-agent ./my-chatbot --git https://github.com/user/agent
      macsdk add-agent . --path ../my-local-agent
      \b
      # Local agents (mono-repo)
      macsdk add-agent . --new weather --description "Weather forecasts"
    """
    # Lazy import
    from .commands.add import add_agent_to_chatbot, add_local_agent_to_chatbot

    if new_agent:
        add_local_agent_to_chatbot(chatbot_dir, new_agent, description)
    else:
        add_agent_to_chatbot(chatbot_dir, package, git, path)


@cli.command(name="list-tools")
def list_tools() -> None:
    """List tools provided by the MACSDK.

    Shows all reusable tools available for building agents,
    including API tools, remote file tools, and more.

    \b
    Examples:
      macsdk list-tools
    """
    # Lazy import
    from .commands.list_cmd import list_sdk_tools

    list_sdk_tools()


if __name__ == "__main__":
    cli()
