"""Shared fixtures for integration tests.

These fixtures handle the creation and cleanup of temporary
projects for end-to-end testing of the SDK.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest
from click.testing import CliRunner

from macsdk.cli.main import cli
from macsdk.cli.utils import derive_class_name

if TYPE_CHECKING:
    pass


# =============================================================================
# CONSTANTS
# =============================================================================

INTEGRATION_TEST_DIR = Path(__file__).parent / "_generated"
TEST_CHATBOT_NAME = "integration-chatbot"
TEST_AGENT_NAME = "integration-agent"

# Path to the macsdk source (for local development)
MACSDK_ROOT = Path(__file__).parent.parent.parent


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def run_uv_command(
    args: list[str],
    cwd: Path,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run a uv command in a directory.

    Args:
        args: Command arguments (without 'uv').
        cwd: Working directory.
        timeout: Command timeout in seconds.
        env: Optional environment variables to add/override.

    Returns:
        CompletedProcess with stdout/stderr.

    Raises:
        subprocess.TimeoutExpired: If command times out.
        subprocess.CalledProcessError: If command fails.
    """
    import os

    cmd = ["uv", *args]

    # Build environment with optional overrides
    run_env = os.environ.copy()

    # Remove VIRTUAL_ENV to avoid conflicts with parent project's venv
    run_env.pop("VIRTUAL_ENV", None)

    if env:
        run_env.update(env)

    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
        env=run_env,
    )


def run_pytest_in_project(
    project_dir: Path,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    """Run pytest in a generated project.

    Args:
        project_dir: Path to project directory.
        timeout: Test timeout in seconds.

    Returns:
        CompletedProcess with test results.
    """
    # Use the project's venv Python directly to avoid path issues
    venv_python = project_dir / ".venv" / "bin" / "python"

    if not venv_python.exists():
        # Fallback to uv run if venv doesn't exist
        return run_uv_command(
            ["run", "pytest", "-v", "--tb=short"],
            cwd=project_dir,
            timeout=timeout,
        )

    # Run pytest using the project's venv Python
    import os

    run_env = os.environ.copy()
    run_env.pop("VIRTUAL_ENV", None)

    return subprocess.run(
        [str(venv_python), "-m", "pytest", "-v", "--tb=short"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
        env=run_env,
    )


def add_local_macsdk_dependency(project_dir: Path) -> None:
    """Add local macsdk path dependency to a generated project.

    This is necessary for integration tests because macsdk is not
    published to PyPI during development.

    Args:
        project_dir: Path to the generated project.
    """
    pyproject_path = project_dir / "pyproject.toml"
    content = pyproject_path.read_text()

    # Calculate relative path from project to macsdk root
    # Structure: tests/integration/_generated/project-name → need 4 levels up
    relative_path = "../../../.."

    # Add source override for macsdk
    if "[tool.uv.sources]" not in content:
        content += f"""
[tool.uv.sources]
macsdk = {{ path = "{relative_path}" }}
"""
    elif "macsdk" not in content.split("[tool.uv.sources]")[1].split("[")[0]:
        # Add macsdk to existing sources section
        content = content.replace(
            "[tool.uv.sources]",
            f'[tool.uv.sources]\nmacsdk = {{ path = "{relative_path}" }}',
        )

    pyproject_path.write_text(content)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def integration_test_dir() -> Generator[Path, None, None]:
    """Create and clean up the integration test directory.

    This fixture creates a temporary directory for generated projects
    and cleans it up after all integration tests complete.

    Yields:
        Path to the integration test directory.
    """
    # Create directory
    INTEGRATION_TEST_DIR.mkdir(parents=True, exist_ok=True)

    yield INTEGRATION_TEST_DIR

    # Cleanup after all tests (comment out for debugging)
    if INTEGRATION_TEST_DIR.exists():
        shutil.rmtree(INTEGRATION_TEST_DIR)


@pytest.fixture(scope="session")
def generated_chatbot(integration_test_dir: Path) -> Generator[Path, None, None]:
    """Generate a chatbot project for testing.

    This fixture:
    1. Creates a new chatbot using 'macsdk new chatbot'
    2. Runs 'uv sync' to install dependencies
    3. Yields the project path for tests
    4. Cleans up after tests

    Yields:
        Path to the generated chatbot project.
    """
    chatbot_dir = integration_test_dir / TEST_CHATBOT_NAME

    # Skip if already generated (for faster re-runs during development)
    if not chatbot_dir.exists():
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "chatbot",
                TEST_CHATBOT_NAME,
                "--output-dir",
                str(integration_test_dir),
                "--display-name",
                "Integration Test Bot",
            ],
        )

        if result.exit_code != 0:
            pytest.fail(f"Failed to create chatbot: {result.output}")

        # Add local macsdk dependency for testing
        add_local_macsdk_dependency(chatbot_dir)

        # Install dependencies (including dev group for testing)
        try:
            run_uv_command(["sync", "--group", "dev"], cwd=chatbot_dir)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Failed to sync chatbot dependencies: {e.stderr}")

    yield chatbot_dir


@pytest.fixture(scope="session")
def generated_agent(integration_test_dir: Path) -> Generator[Path, None, None]:
    """Generate an agent project for testing.

    This fixture:
    1. Creates a new agent using 'macsdk new agent'
    2. Runs 'uv sync' to install dependencies
    3. Yields the project path for tests
    4. Cleans up after tests

    Yields:
        Path to the generated agent project.
    """
    agent_dir = integration_test_dir / TEST_AGENT_NAME

    # Skip if already generated
    if not agent_dir.exists():
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "agent",
                TEST_AGENT_NAME,
                "--output-dir",
                str(integration_test_dir),
                "--description",
                "Integration test agent for monitoring services",
            ],
        )

        if result.exit_code != 0:
            pytest.fail(f"Failed to create agent: {result.output}")

        # Add local macsdk dependency for testing
        add_local_macsdk_dependency(agent_dir)

        # Install dependencies (including dev group for testing)
        try:
            run_uv_command(["sync", "--group", "dev"], cwd=agent_dir)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Failed to sync agent dependencies: {e.stderr}")

    yield agent_dir


@pytest.fixture(scope="session")
def chatbot_with_agent(
    generated_chatbot: Path,
    generated_agent: Path,
) -> Generator[Path, None, None]:
    """Create a chatbot with the agent registered.

    This fixture modifies the generated chatbot to import and
    register the generated agent.

    Yields:
        Path to the chatbot project with agent registered.
    """
    chatbot_dir = generated_chatbot
    _ = generated_agent  # Ensure agent is generated first

    # Add agent as a dependency in chatbot's pyproject.toml
    pyproject_path = chatbot_dir / "pyproject.toml"
    pyproject_content = pyproject_path.read_text()

    # Add path dependency to agent (for local development)
    agent_slug = TEST_AGENT_NAME.replace("-", "_")
    if agent_slug not in pyproject_content:
        # Insert after [project.dependencies]
        pyproject_content = pyproject_content.replace(
            "dependencies = [",
            f'dependencies = [\n    "{agent_slug}",',
        )

        # Add source for local path
        if "[tool.uv.sources]" not in pyproject_content:
            pyproject_content += f"""
[tool.uv.sources]
{agent_slug} = {{ path = "../{TEST_AGENT_NAME}" }}
"""
        else:
            source_line = f'{agent_slug} = {{ path = "../{TEST_AGENT_NAME}" }}'
            pyproject_content = pyproject_content.replace(
                "[tool.uv.sources]",
                f"[tool.uv.sources]\n{source_line}",
            )

        pyproject_path.write_text(pyproject_content)

        # Sync again with new dependency
        try:
            run_uv_command(["sync"], cwd=chatbot_dir)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Failed to sync with agent dependency: {e.stderr}")

    # Modify agents.py to register the agent
    chatbot_slug = TEST_CHATBOT_NAME.replace("-", "_")
    agents_py = chatbot_dir / "src" / chatbot_slug / "agents.py"
    agents_content = agents_py.read_text()

    if agent_slug not in agents_content:
        # Add import and registration with all required functions
        agent_class = derive_class_name(TEST_AGENT_NAME)
        new_content = f'''"""Agent registration for {chatbot_slug}."""

from __future__ import annotations

from typing import Any

from {agent_slug} import {agent_class}

from macsdk.core import get_registry, register_agent


def register_all_agents() -> None:
    """Register all specialist agents for the chatbot."""
    registry = get_registry()
    if not registry.is_registered("{agent_slug}"):
        register_agent({agent_class}())


# Alias for backwards compatibility
register_agents = register_all_agents


def get_registered_agents() -> list[dict[str, Any]]:
    """Get information about all registered agents."""
    register_all_agents()
    registry = get_registry()
    agents_info: list[dict[str, Any]] = []
    for name, agent in registry.get_all().items():
        info = {{
            "name": name,
            "description": getattr(agent, "capabilities", "No description"),
            "tools_count": len(getattr(agent, "tools", [])),
        }}
        agents_info.append(info)
    return agents_info
'''
        agents_py.write_text(new_content)

    yield chatbot_dir


@pytest.fixture(scope="session")
def chatbot_with_local_agent(
    integration_test_dir: Path,
) -> Generator[Path, None, None]:
    """Create a chatbot with a local agent (mono-repo approach).

    This fixture:
    1. Creates a new chatbot using 'macsdk new chatbot'
    2. Adds a local agent using 'macsdk add-agent --new'
    3. Runs 'uv sync' to install dependencies
    4. Yields the project path for tests

    Yields:
        Path to the chatbot project with local agent.
    """
    chatbot_name = "mono-chatbot"
    chatbot_dir = integration_test_dir / chatbot_name

    # Skip if already generated
    if not chatbot_dir.exists():
        runner = CliRunner()

        # Create chatbot
        result = runner.invoke(
            cli,
            [
                "new",
                "chatbot",
                chatbot_name,
                "--output-dir",
                str(integration_test_dir),
                "--display-name",
                "Mono Repo Test Bot",
            ],
        )

        if result.exit_code != 0:
            pytest.fail(f"Failed to create chatbot: {result.output}")

        # Add local macsdk dependency for testing
        add_local_macsdk_dependency(chatbot_dir)

        # Install dependencies first
        try:
            run_uv_command(["sync", "--group", "dev"], cwd=chatbot_dir)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Failed to sync chatbot dependencies: {e.stderr}")

        # Add local agent using add-agent command
        result = runner.invoke(
            cli,
            [
                "add-agent",
                str(chatbot_dir),
                "--new",
                "weather",
                "--description",
                "Weather information service",
            ],
        )

        if result.exit_code != 0:
            pytest.fail(f"Failed to add local agent: {result.output}")

    yield chatbot_dir
