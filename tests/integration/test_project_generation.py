"""Integration tests for project generation.

These tests verify that generated projects are valid and functional:
1. Files are created correctly
2. Code can be imported without errors
3. Generated tests pass
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .conftest import run_pytest_in_project, run_uv_command

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestChatbotGeneration:
    """Tests for generated chatbot projects."""

    def test_chatbot_structure_complete(self, generated_chatbot: Path) -> None:
        """Generated chatbot has all required files."""
        chatbot_slug = "integration_chatbot"

        assert generated_chatbot.exists()
        assert (generated_chatbot / "pyproject.toml").exists()
        assert (generated_chatbot / "src" / chatbot_slug / "__init__.py").exists()
        assert (generated_chatbot / "src" / chatbot_slug / "agents.py").exists()
        assert (generated_chatbot / "src" / chatbot_slug / "cli.py").exists()

    def test_chatbot_can_import(self, generated_chatbot: Path) -> None:
        """Generated chatbot code can be imported."""
        chatbot_slug = "integration_chatbot"

        result = run_uv_command(
            ["run", "python", "-c", f"import {chatbot_slug}; print('OK')"],
            cwd=generated_chatbot,
        )

        assert "OK" in result.stdout

    def test_chatbot_cli_module_valid(self, generated_chatbot: Path) -> None:
        """Generated chatbot CLI module is valid Python."""
        chatbot_slug = "integration_chatbot"

        # Verify the CLI module can be imported and has main()
        check_code = f"""
from {chatbot_slug}.cli import main
assert callable(main), "main() should be callable"
print('CLI_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=generated_chatbot,
        )

        assert "CLI_OK" in result.stdout

    def test_chatbot_linting_passes(self, generated_chatbot: Path) -> None:
        """Generated chatbot code passes linting."""
        try:
            run_uv_command(
                ["run", "ruff", "check", "src/"],
                cwd=generated_chatbot,
            )
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Linting failed:\nstdout: {e.stdout}\nstderr: {e.stderr}")


class TestAgentGeneration:
    """Tests for generated agent projects."""

    def test_agent_structure_complete(self, generated_agent: Path) -> None:
        """Generated agent has all required files."""
        agent_slug = "integration_agent"

        assert generated_agent.exists()
        assert (generated_agent / "pyproject.toml").exists()
        assert (generated_agent / "src" / agent_slug / "__init__.py").exists()
        assert (generated_agent / "src" / agent_slug / "agent.py").exists()
        assert (generated_agent / "src" / agent_slug / "tools.py").exists()
        assert (generated_agent / "src" / agent_slug / "models.py").exists()
        assert (generated_agent / "src" / agent_slug / "prompts.py").exists()
        assert (generated_agent / "tests" / "test_agent.py").exists()

    def test_agent_can_import(self, generated_agent: Path) -> None:
        """Generated agent code can be imported."""
        agent_slug = "integration_agent"

        result = run_uv_command(
            ["run", "python", "-c", f"import {agent_slug}; print('OK')"],
            cwd=generated_agent,
        )

        assert "OK" in result.stdout

    def test_agent_implements_protocol(self, generated_agent: Path) -> None:
        """Generated agent implements SpecialistAgent protocol."""
        agent_slug = "integration_agent"
        agent_class = "IntegrationAgentAgent"

        check_code = f"""
from {agent_slug} import {agent_class}
from macsdk.core import SpecialistAgent

agent = {agent_class}()

# Check protocol attributes
assert hasattr(agent, 'name'), "Missing 'name' attribute"
assert hasattr(agent, 'capabilities'), "Missing 'capabilities' attribute"
assert hasattr(agent, 'run'), "Missing 'run' method"
assert hasattr(agent, 'as_tool'), "Missing 'as_tool' method"

# Check it's a valid protocol implementation
assert isinstance(agent, SpecialistAgent), "Does not implement SpecialistAgent"

print('PROTOCOL_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=generated_agent,
        )

        assert "PROTOCOL_OK" in result.stdout

    def test_agent_tests_pass(self, generated_agent: Path) -> None:
        """Generated agent's own tests pass."""
        try:
            result = run_pytest_in_project(generated_agent)
            # pytest returns 0 on success
            stdout_lower = result.stdout.lower()
            stderr_lower = result.stderr.lower()
            assert "passed" in stdout_lower or "passed" in stderr_lower
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Agent tests failed:\n{e.stdout}\n{e.stderr}")

    def test_agent_linting_passes(self, generated_agent: Path) -> None:
        """Generated agent code passes linting."""
        try:
            run_uv_command(
                ["run", "ruff", "check", "src/"],
                cwd=generated_agent,
            )
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Linting failed:\nstdout: {e.stdout}\nstderr: {e.stderr}")

    def test_agent_tools_are_callable(self, generated_agent: Path) -> None:
        """Generated agent tools can be imported and have correct structure."""
        agent_slug = "integration_agent"

        check_code = f"""
from {agent_slug}.tools import get_services, get_service_status, get_alerts

# Verify tools are defined and have required attributes
tools = [get_services, get_service_status, get_alerts]
for tool in tools:
    assert tool is not None, f"Tool {{tool}} is None"
    assert hasattr(tool, 'ainvoke'), f"Tool {{tool.name}} missing ainvoke"
    assert hasattr(tool, 'description'), f"Tool {{tool.name}} missing description"
    assert tool.description, f"Tool {{tool.name}} has empty description"

print('TOOLS_OK')
"""
        result = run_uv_command(
            ["run", "python", "-c", check_code],
            cwd=generated_agent,
        )

        assert "TOOLS_OK" in result.stdout
