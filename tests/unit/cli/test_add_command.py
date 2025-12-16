"""Tests for 'macsdk add-agent' command.

This module tests the add-agent command including:
- Helper functions for finding files
- Adding remote agents (package, git, path)
- Creating local agents (mono-repo)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from macsdk.cli.commands.add import (
    _add_agent_to_agents_file,
    _create_local_agent,
    _find_agents_file,
    _find_chatbot_slug,
    _find_pyproject,
)
from macsdk.cli.main import cli


class TestFindChatbotSlug:
    """Tests for _find_chatbot_slug function."""

    def test_finds_package_in_src(self, tmp_path: Path) -> None:
        """Finds the chatbot package slug from src/ directory."""
        # Create chatbot structure
        src_pkg = tmp_path / "src" / "my_chatbot"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        result = _find_chatbot_slug(tmp_path)
        assert result == "my_chatbot"

    def test_returns_none_if_no_src(self, tmp_path: Path) -> None:
        """Returns None if no src/ directory."""
        result = _find_chatbot_slug(tmp_path)
        assert result is None

    def test_returns_none_if_no_package(self, tmp_path: Path) -> None:
        """Returns None if no package (no __init__.py) in src/."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "not_a_package").mkdir()

        result = _find_chatbot_slug(tmp_path)
        assert result is None

    def test_uses_pyproject_name_with_multiple_packages(self, tmp_path: Path) -> None:
        """Uses pyproject.toml name when multiple packages exist in src/."""
        # Create pyproject.toml with project name
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-chatbot"')

        # Create multiple packages in src/
        src = tmp_path / "src"
        for pkg_name in ["my_chatbot", "my_chatbot_utils", "another_pkg"]:
            pkg_dir = src / pkg_name
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "__init__.py").touch()

        # Should find my_chatbot (matches project name), not depend on filesystem order
        result = _find_chatbot_slug(tmp_path)
        assert result == "my_chatbot"

    def test_falls_back_to_scan_if_pyproject_missing(self, tmp_path: Path) -> None:
        """Falls back to scanning src/ if pyproject.toml doesn't exist."""
        # Create single package without pyproject.toml
        src_pkg = tmp_path / "src" / "fallback_pkg"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        result = _find_chatbot_slug(tmp_path)
        assert result == "fallback_pkg"

    def test_fallback_prioritizes_directory_name(self, tmp_path: Path) -> None:
        """Fallback prioritizes package matching project directory name."""
        # Create project directory named "my-chatbot"
        project_dir = tmp_path / "my-chatbot"
        project_dir.mkdir()

        # Create multiple packages in src/ (no pyproject.toml)
        src = project_dir / "src"
        for pkg_name in ["other_utils", "my_chatbot", "another_pkg"]:
            pkg_dir = src / pkg_name
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "__init__.py").touch()

        # Should find my_chatbot (matches directory name), not depend on order
        result = _find_chatbot_slug(project_dir)
        assert result == "my_chatbot"


class TestFindAgentsFile:
    """Tests for _find_agents_file function."""

    def test_finds_agents_py(self, tmp_path: Path) -> None:
        """Finds agents.py in src/*/."""
        agents_file = tmp_path / "src" / "my_chatbot" / "agents.py"
        agents_file.parent.mkdir(parents=True)
        agents_file.write_text("# agents")

        result = _find_agents_file(tmp_path)
        assert result == agents_file

    def test_returns_none_if_no_agents(self, tmp_path: Path) -> None:
        """Returns None if no agents.py found."""
        src = tmp_path / "src" / "my_chatbot"
        src.mkdir(parents=True)
        (src / "__init__.py").touch()

        result = _find_agents_file(tmp_path)
        assert result is None


class TestFindPyproject:
    """Tests for _find_pyproject function."""

    def test_finds_pyproject(self, tmp_path: Path) -> None:
        """Finds pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'")

        result = _find_pyproject(tmp_path)
        assert result == pyproject

    def test_returns_none_if_no_pyproject(self, tmp_path: Path) -> None:
        """Returns None if no pyproject.toml."""
        result = _find_pyproject(tmp_path)
        assert result is None


class TestAddAgentToAgentsFile:
    """Tests for _add_agent_to_agents_file function."""

    def test_adds_remote_agent_import(self, tmp_path: Path) -> None:
        """Adds remote agent import statement."""
        agents_file = tmp_path / "agents.py"
        agents_file.write_text('''"""Agents module."""
from macsdk.core import get_registry

def register_all_agents() -> None:
    registry = get_registry()
    _ = registry  # Avoid unused variable warning
''')

        result = _add_agent_to_agents_file(
            agents_file, "weather_agent", "WeatherAgent", is_local=False
        )

        assert result is True
        content = agents_file.read_text()
        assert "from weather_agent import WeatherAgent" in content
        assert "from .local_agents" not in content

    def test_adds_local_agent_import(self, tmp_path: Path) -> None:
        """Adds local agent import with relative path."""
        agents_file = tmp_path / "agents.py"
        agents_file.write_text('''"""Agents module."""
from macsdk.core import get_registry

def register_all_agents() -> None:
    registry = get_registry()
    _ = registry  # Avoid unused variable warning
''')

        result = _add_agent_to_agents_file(
            agents_file, "weather", "WeatherAgent", is_local=True
        )

        assert result is True
        content = agents_file.read_text()
        assert "from .local_agents.weather import WeatherAgent" in content

    def test_skips_if_already_imported(self, tmp_path: Path) -> None:
        """Returns False if agent already imported."""
        agents_file = tmp_path / "agents.py"
        agents_file.write_text('''"""Agents module."""
from weather_agent import WeatherAgent

def register_all_agents() -> None:
    pass
''')

        result = _add_agent_to_agents_file(
            agents_file, "weather_agent", "WeatherAgent", is_local=False
        )

        assert result is False

    def test_no_partial_match_on_import_check(self, tmp_path: Path) -> None:
        """Does not match partial package names (e.g., 'api' vs 'api_utils')."""
        agents_file = tmp_path / "agents.py"
        # File has api_utils imported, but we're adding api
        agents_file.write_text('''"""Agents module."""
from macsdk.core import get_registry
from api_utils import ApiUtilsAgent

def register_all_agents() -> None:
    registry = get_registry()
    _ = registry
''')

        # Should add 'api' even though 'api_utils' is already imported
        result = _add_agent_to_agents_file(
            agents_file, "api", "ApiAgent", is_local=False
        )

        assert result is True
        content = agents_file.read_text()
        assert "from api import ApiAgent" in content

    def test_adds_registration_code(self, tmp_path: Path) -> None:
        """Adds agent registration code inside register_all_agents."""
        agents_file = tmp_path / "agents.py"
        agents_file.write_text('''"""Agents module."""
from macsdk.core import get_registry

def register_all_agents() -> None:
    registry = get_registry()
    _ = registry  # Avoid unused variable warning
''')

        _add_agent_to_agents_file(
            agents_file, "weather_agent", "WeatherAgent", is_local=False
        )

        content = agents_file.read_text()
        assert 'if not registry.is_registered("weather_agent"):' in content
        assert "register_agent(WeatherAgent())" in content


class TestCreateLocalAgent:
    """Tests for _create_local_agent function."""

    def test_creates_local_agents_directory(self, tmp_path: Path) -> None:
        """Creates local_agents directory if it doesn't exist."""
        # Setup chatbot structure
        src_pkg = tmp_path / "src" / "my_chatbot"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        _create_local_agent(
            tmp_path, "my_chatbot", "weather", "WeatherAgent", "Weather service"
        )

        local_agents = src_pkg / "local_agents"
        assert local_agents.exists()
        assert (local_agents / "__init__.py").exists()

    def test_creates_agent_module(self, tmp_path: Path) -> None:
        """Creates agent module with all required files."""
        # Setup chatbot structure
        src_pkg = tmp_path / "src" / "my_chatbot"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        agent_dir = _create_local_agent(
            tmp_path, "my_chatbot", "weather", "WeatherAgent", "Weather service"
        )

        assert agent_dir.exists()
        assert (agent_dir / "__init__.py").exists()
        assert (agent_dir / "agent.py").exists()
        assert (agent_dir / "tools.py").exists()
        assert (agent_dir / "prompts.py").exists()
        assert (agent_dir / "models.py").exists()

    def test_fails_if_agent_exists(self, tmp_path: Path) -> None:
        """Raises SystemExit if agent already exists."""
        # Setup chatbot structure
        src_pkg = tmp_path / "src" / "my_chatbot"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        # Create agent directory
        local_agents = src_pkg / "local_agents"
        local_agents.mkdir()
        (local_agents / "weather").mkdir()

        with pytest.raises(SystemExit):
            _create_local_agent(
                tmp_path, "my_chatbot", "weather", "WeatherAgent", "Weather service"
            )

    def test_fails_if_slug_not_valid_identifier(self, tmp_path: Path) -> None:
        """Raises SystemExit if agent slug is not a valid Python identifier."""
        # Setup chatbot structure
        src_pkg = tmp_path / "src" / "my_chatbot"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        # Pass an invalid identifier directly (starts with number)
        with pytest.raises(SystemExit):
            _create_local_agent(
                tmp_path, "my_chatbot", "123invalid", "InvalidAgent", "Invalid agent"
            )

    def test_agent_init_exports_class(self, tmp_path: Path) -> None:
        """Agent __init__.py exports the agent class."""
        # Setup chatbot structure
        src_pkg = tmp_path / "src" / "my_chatbot"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").touch()

        agent_dir = _create_local_agent(
            tmp_path, "my_chatbot", "weather", "WeatherAgent", "Weather service"
        )

        init_content = (agent_dir / "__init__.py").read_text()
        assert "WeatherAgent" in init_content


class TestAddAgentCommandCLI:
    """Integration tests for the add-agent CLI command."""

    def test_shows_help(self) -> None:
        """Shows help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-agent", "--help"])
        assert result.exit_code == 0
        assert "--new" in result.output
        assert "--description" in result.output
        assert "Local Agents" in result.output

    def test_requires_source_option(self) -> None:
        """Requires at least one source option."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create minimal chatbot structure
            Path("my-chatbot").mkdir()
            Path("my-chatbot/pyproject.toml").write_text('[project]\nname="my-chatbot"')
            Path("my-chatbot/src/my_chatbot").mkdir(parents=True)
            Path("my-chatbot/src/my_chatbot/__init__.py").touch()
            Path("my-chatbot/src/my_chatbot/agents.py").write_text("# agents")

            result = runner.invoke(cli, ["add-agent", "my-chatbot"])
            assert result.exit_code == 1
            assert "Must specify" in result.output

    @patch("macsdk.cli.commands.add.subprocess.run")
    def test_creates_local_agent_with_new_option(self, mock_run: MagicMock) -> None:
        """Creates local agent when using --new option."""
        mock_run.return_value = MagicMock(returncode=0)

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create minimal chatbot structure
            Path("my-chatbot").mkdir()
            Path("my-chatbot/pyproject.toml").write_text(
                '[project]\nname="my-chatbot"\ndependencies = []'
            )
            Path("my-chatbot/src/my_chatbot").mkdir(parents=True)
            Path("my-chatbot/src/my_chatbot/__init__.py").touch()
            Path("my-chatbot/src/my_chatbot/agents.py").write_text(
                '''"""Agents."""
from macsdk.core import get_registry

def register_all_agents() -> None:
    registry = get_registry()
    _ = registry
'''
            )

            result = runner.invoke(
                cli,
                ["add-agent", "my-chatbot", "--new", "weather", "-d", "Weather info"],
            )

            assert result.exit_code == 0
            assert "Local agent created successfully" in result.output

            # Verify files were created
            agent_dir = Path("my-chatbot/src/my_chatbot/local_agents/weather")
            assert agent_dir.exists()
            assert (agent_dir / "agent.py").exists()

            # Verify agents.py was updated
            agents_content = Path("my-chatbot/src/my_chatbot/agents.py").read_text()
            assert "from .local_agents.weather import WeatherAgent" in agents_content
