"""Tests for main CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from macsdk._version import __version__
from macsdk.cli.main import cli


class TestMainCLI:
    """Tests for the main CLI group."""

    def test_cli_shows_help(self) -> None:
        """CLI shows help message."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MACSDK" in result.output
        assert "Multi-Agent Chatbot SDK" in result.output

    def test_cli_shows_version(self) -> None:
        """CLI shows version from _version module."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_cli_has_new_command(self) -> None:
        """CLI has 'new' command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["new", "--help"])
        assert result.exit_code == 0
        assert "chatbot" in result.output or "agent" in result.output

    def test_cli_has_add_agent_command(self) -> None:
        """CLI has 'add-agent' command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-agent", "--help"])
        assert result.exit_code == 0
        assert "CHATBOT_DIR" in result.output

    def test_cli_has_list_tools_command(self) -> None:
        """CLI has 'list-tools' command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list-tools", "--help"])
        assert result.exit_code == 0
        assert "tools" in result.output.lower()


# Note: TestDeriveClassName tests moved to test_utils.py
# The derive_class_name function is now in macsdk.cli.utils
