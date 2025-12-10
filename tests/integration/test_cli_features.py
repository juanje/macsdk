"""Integration tests for CLI features.

These tests verify that:
1. Generated projects include all expected files (.gitignore, .env.example)
2. CLI commands work correctly (--help, tools, agents, info)
3. RAG integration option works correctly
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .conftest import run_uv_command

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestProjectFiles:
    """Tests for generated project files."""

    def test_agent_has_gitignore(self, generated_agent: Path) -> None:
        """Agent project includes .gitignore file."""
        gitignore = generated_agent / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"

        content = gitignore.read_text()
        # Check for expected entries
        assert "__pycache__/" in content
        assert ".venv/" in content
        assert ".env" in content
        assert ".mypy_cache/" in content

    def test_agent_has_env_example(self, generated_agent: Path) -> None:
        """Agent project includes .env.example file."""
        env_example = generated_agent / ".env.example"
        assert env_example.exists(), ".env.example not found"

        content = env_example.read_text()
        assert "GOOGLE_API_KEY" in content

    def test_agent_has_config_example(self, generated_agent: Path) -> None:
        """Agent project includes config.yml.example file."""
        config_example = generated_agent / "config.yml.example"
        assert config_example.exists(), "config.yml.example not found"

    def test_chatbot_has_gitignore(self, generated_chatbot: Path) -> None:
        """Chatbot project includes .gitignore file."""
        gitignore = generated_chatbot / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"

        content = gitignore.read_text()
        assert "__pycache__/" in content
        assert ".venv/" in content
        assert ".env" in content

    def test_chatbot_has_env_example(self, generated_chatbot: Path) -> None:
        """Chatbot project includes .env.example file."""
        env_example = generated_chatbot / ".env.example"
        assert env_example.exists(), ".env.example not found"

        content = env_example.read_text()
        assert "GOOGLE_API_KEY" in content

    def test_chatbot_has_config_example(self, generated_chatbot: Path) -> None:
        """Chatbot project includes config.yml.example file."""
        config_example = generated_chatbot / "config.yml.example"
        assert config_example.exists(), "config.yml.example not found"


class TestAgentCLI:
    """Tests for agent CLI commands."""

    def test_agent_help_command(self, generated_agent: Path) -> None:
        """Agent --help shows usage information."""
        result = run_uv_command(
            ["run", "integration-agent", "--help"],
            cwd=generated_agent,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Options:" in result.stdout
        assert "Commands:" in result.stdout
        assert "tools" in result.stdout
        assert "info" in result.stdout
        assert "chat" in result.stdout

    def test_agent_version_command(self, generated_agent: Path) -> None:
        """Agent --version shows version information."""
        result = run_uv_command(
            ["run", "integration-agent", "--version"],
            cwd=generated_agent,
        )

        assert result.returncode == 0
        assert "v0.1.0" in result.stdout

    def test_agent_tools_command(self, generated_agent: Path) -> None:
        """Agent tools command lists available tools."""
        result = run_uv_command(
            ["run", "integration-agent", "tools"],
            cwd=generated_agent,
        )

        assert result.returncode == 0
        assert "Tools" in result.stdout
        assert "api_get" in result.stdout
        assert "fetch_file" in result.stdout
        assert "Total:" in result.stdout

    def test_agent_info_command(self, generated_agent: Path) -> None:
        """Agent info command shows agent information."""
        result = run_uv_command(
            ["run", "integration-agent", "info"],
            cwd=generated_agent,
        )

        assert result.returncode == 0
        assert "integration-agent" in result.stdout.lower()
        # Rich output shows "X tools available" instead of "Tools: X"
        assert "tools available" in result.stdout.lower()


class TestChatbotCLI:
    """Tests for chatbot CLI commands."""

    def test_chatbot_help_command(self, generated_chatbot: Path) -> None:
        """Chatbot --help shows usage information."""
        result = run_uv_command(
            ["run", "integration-chatbot", "--help"],
            cwd=generated_chatbot,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Options:" in result.stdout
        assert "Commands:" in result.stdout
        assert "agents" in result.stdout
        assert "info" in result.stdout
        assert "chat" in result.stdout

    def test_chatbot_version_command(self, generated_chatbot: Path) -> None:
        """Chatbot --version shows version information."""
        result = run_uv_command(
            ["run", "integration-chatbot", "--version"],
            cwd=generated_chatbot,
        )

        assert result.returncode == 0
        assert "v0.1.0" in result.stdout

    def test_chatbot_agents_command_no_agents(self, generated_chatbot: Path) -> None:
        """Chatbot agents command works with no agents registered."""
        result = run_uv_command(
            ["run", "integration-chatbot", "agents"],
            cwd=generated_chatbot,
        )

        assert result.returncode == 0
        assert "Agents" in result.stdout

    def test_chatbot_info_command(self, generated_chatbot: Path) -> None:
        """Chatbot info command shows chatbot information."""
        result = run_uv_command(
            ["run", "integration-chatbot", "info"],
            cwd=generated_chatbot,
        )

        assert result.returncode == 0
        assert "Integration Test Bot" in result.stdout
        assert "Model:" in result.stdout
        assert "Temperature:" in result.stdout


class TestChatbotWithAgentCLI:
    """Tests for chatbot CLI with registered agent."""

    def test_chatbot_agents_shows_registered_agent(
        self, chatbot_with_agent: Path
    ) -> None:
        """Chatbot agents command shows the registered agent."""
        result = run_uv_command(
            ["run", "integration-chatbot", "agents"],
            cwd=chatbot_with_agent,
        )

        assert result.returncode == 0
        assert "integration_agent" in result.stdout.lower()
        assert "Total:" in result.stdout


class TestRagChatbot:
    """Tests for chatbot with RAG integration."""

    @pytest.fixture(scope="class")
    def rag_chatbot(self, integration_test_dir: Path) -> Path:
        """Generate a chatbot with RAG enabled."""
        from click.testing import CliRunner

        from macsdk.cli.main import cli

        from .conftest import add_local_macsdk_dependency

        chatbot_dir = integration_test_dir / "rag-chatbot"

        if not chatbot_dir.exists():
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "new",
                    "chatbot",
                    "rag-chatbot",
                    "--output-dir",
                    str(integration_test_dir),
                    "--with-rag",
                ],
            )

            if result.exit_code != 0:
                pytest.fail(f"Failed to create RAG chatbot: {result.output}")

            add_local_macsdk_dependency(chatbot_dir)

            try:
                run_uv_command(["sync"], cwd=chatbot_dir, timeout=180)
            except subprocess.CalledProcessError as e:
                pytest.fail(f"Failed to sync RAG chatbot: {e.stderr}")

        return chatbot_dir

    def test_rag_chatbot_has_rag_gitignore_entries(self, rag_chatbot: Path) -> None:
        """RAG chatbot .gitignore includes RAG-specific entries."""
        gitignore = rag_chatbot / ".gitignore"
        content = gitignore.read_text()

        assert "chroma_db/" in content
        assert ".macsdk_llm_cache.db" in content

    def test_rag_chatbot_config_has_rag_section(self, rag_chatbot: Path) -> None:
        """RAG chatbot config.yml.example includes RAG configuration."""
        config_example = rag_chatbot / "config.yml.example"
        content = config_example.read_text()

        assert "rag:" in content
        assert "sources:" in content

    def test_rag_chatbot_agents_shows_rag_agent(self, rag_chatbot: Path) -> None:
        """RAG chatbot agents command shows the RAG agent."""
        result = run_uv_command(
            ["run", "rag-chatbot", "agents"],
            cwd=rag_chatbot,
        )

        assert result.returncode == 0
        assert "rag_agent" in result.stdout.lower()

    def test_rag_chatbot_info_shows_rag_status(self, rag_chatbot: Path) -> None:
        """RAG chatbot info shows RAG configuration status."""
        result = run_uv_command(
            ["run", "rag-chatbot", "info"],
            cwd=rag_chatbot,
        )

        assert result.returncode == 0
        # RAG sources should show status since this is a RAG chatbot
        assert "RAG Sources:" in result.stdout
