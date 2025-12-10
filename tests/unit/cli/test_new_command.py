"""Tests for 'macsdk new' command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from macsdk.cli.main import cli

# Test constants
TEST_CHATBOT_NAME = "test-chatbot"
TEST_CHATBOT_SLUG = "test_chatbot"
TEST_AGENT_NAME = "test-agent"
TEST_AGENT_SLUG = "test_agent"
TEST_DISPLAY_NAME = "My Bot"
TEST_DESCRIPTION = "Custom description"
TEST_OUTPUT_SUBDIR = "subdir"


class TestNewChatbotCommand:
    """Tests for 'macsdk new chatbot' command."""

    def test_creates_chatbot_directory(self) -> None:
        """Creates chatbot project directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["new", "chatbot", TEST_CHATBOT_NAME])
            assert result.exit_code == 0
            assert Path(TEST_CHATBOT_NAME).exists()

    def test_creates_pyproject_toml(self) -> None:
        """Creates pyproject.toml file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "chatbot", TEST_CHATBOT_NAME])
            assert (Path(TEST_CHATBOT_NAME) / "pyproject.toml").exists()

    def test_creates_src_directory(self) -> None:
        """Creates src directory with package."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "chatbot", TEST_CHATBOT_NAME])
            assert (Path(TEST_CHATBOT_NAME) / "src" / TEST_CHATBOT_SLUG).exists()

    def test_creates_agents_py(self) -> None:
        """Creates agents.py file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "chatbot", TEST_CHATBOT_NAME])
            assert (
                Path(TEST_CHATBOT_NAME) / "src" / TEST_CHATBOT_SLUG / "agents.py"
            ).exists()

    def test_creates_cli_py(self) -> None:
        """Creates cli.py file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "chatbot", TEST_CHATBOT_NAME])
            assert (
                Path(TEST_CHATBOT_NAME) / "src" / TEST_CHATBOT_SLUG / "cli.py"
            ).exists()

    def test_fails_if_directory_exists(self) -> None:
        """Fails if directory already exists."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path(TEST_CHATBOT_NAME).mkdir()
            result = runner.invoke(cli, ["new", "chatbot", TEST_CHATBOT_NAME])
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_custom_display_name(self) -> None:
        """Uses custom display name."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "new",
                    "chatbot",
                    TEST_CHATBOT_NAME,
                    "--display-name",
                    TEST_DISPLAY_NAME,
                ],
            )
            assert result.exit_code == 0
            # Check that display name is used in files
            cli_py = (
                Path(TEST_CHATBOT_NAME) / "src" / TEST_CHATBOT_SLUG / "cli.py"
            ).read_text()
            assert TEST_DISPLAY_NAME in cli_py


class TestNewAgentCommand:
    """Tests for 'macsdk new agent' command."""

    def test_creates_agent_directory(self) -> None:
        """Creates agent project directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["new", "agent", TEST_AGENT_NAME])
            assert result.exit_code == 0
            assert Path(TEST_AGENT_NAME).exists()

    def test_creates_agent_pyproject(self) -> None:
        """Creates pyproject.toml for agent."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "agent", TEST_AGENT_NAME])
            assert (Path(TEST_AGENT_NAME) / "pyproject.toml").exists()

    def test_creates_agent_module(self) -> None:
        """Creates agent module with required files."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "agent", TEST_AGENT_NAME])
            agent_dir = Path(TEST_AGENT_NAME) / "src" / TEST_AGENT_SLUG
            assert agent_dir.exists()
            assert (agent_dir / "agent.py").exists()
            assert (agent_dir / "tools.py").exists()
            assert (agent_dir / "models.py").exists()
            assert (agent_dir / "prompts.py").exists()

    def test_creates_tests_directory(self) -> None:
        """Creates tests directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(cli, ["new", "agent", TEST_AGENT_NAME])
            assert (Path(TEST_AGENT_NAME) / "tests").exists()

    def test_creates_agent_with_description(self) -> None:
        """Creates agent with custom description."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                ["new", "agent", TEST_AGENT_NAME, "--description", TEST_DESCRIPTION],
            )
            assert result.exit_code == 0
            # Check prompts file has system prompt defined
            prompts_content = (
                Path(TEST_AGENT_NAME) / "src" / TEST_AGENT_SLUG / "prompts.py"
            ).read_text()
            assert "SYSTEM_PROMPT" in prompts_content
            assert "api_get" in prompts_content.lower()

    def test_creates_agent_with_output_dir(self) -> None:
        """Creates agent in specified output directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path(TEST_OUTPUT_SUBDIR).mkdir()
            result = runner.invoke(
                cli,
                ["new", "agent", TEST_AGENT_NAME, "--output-dir", TEST_OUTPUT_SUBDIR],
            )
            assert result.exit_code == 0
            assert (Path(TEST_OUTPUT_SUBDIR) / TEST_AGENT_NAME).exists()
