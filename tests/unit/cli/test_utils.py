"""Tests for CLI utility functions.

This module tests the shared utility functions used by CLI commands,
including the fix for the duplicate 'Agent' suffix bug.
"""

from __future__ import annotations

import pytest

from macsdk.cli.utils import derive_class_name, slugify


class TestSlugify:
    """Tests for the slugify function."""

    def test_converts_hyphens_to_underscores(self) -> None:
        """Converts hyphens to underscores."""
        assert slugify("my-chatbot") == "my_chatbot"

    def test_converts_spaces_to_underscores(self) -> None:
        """Converts spaces to underscores."""
        assert slugify("my chatbot") == "my_chatbot"

    def test_converts_to_lowercase(self) -> None:
        """Converts to lowercase."""
        assert slugify("MyBot") == "mybot"

    def test_removes_invalid_characters(self) -> None:
        """Removes invalid characters."""
        assert slugify("my@bot!") == "mybot"

    def test_preserves_underscores(self) -> None:
        """Preserves existing underscores."""
        assert slugify("my_chatbot") == "my_chatbot"

    def test_handles_consecutive_separators(self) -> None:
        """Handles consecutive separators."""
        assert slugify("my--chatbot") == "my_chatbot"
        assert slugify("my  chatbot") == "my_chatbot"

    def test_prepends_pkg_if_starts_with_number(self) -> None:
        """Prepends 'pkg_' if name starts with a number."""
        assert slugify("123bot") == "pkg_123bot"

    def test_agent_name_with_suffix(self) -> None:
        """Handles agent names that end with 'agent'."""
        assert slugify("infra-agent") == "infra_agent"
        assert slugify("gitlab-agent") == "gitlab_agent"


class TestDeriveClassName:
    """Tests for the derive_class_name function.

    These tests specifically verify the fix for the duplicate 'Agent' suffix bug
    where names like 'infra-agent' were incorrectly becoming 'InfraAgentAgent'.
    """

    def test_adds_agent_suffix_to_simple_names(self) -> None:
        """Adds Agent suffix to simple names without 'agent'."""
        assert derive_class_name("weather") == "WeatherAgent"
        assert derive_class_name("gitlab") == "GitlabAgent"

    def test_adds_agent_suffix_to_compound_names(self) -> None:
        """Adds Agent suffix to compound names without 'agent'."""
        assert derive_class_name("infra-monitor") == "InfraMonitorAgent"
        assert derive_class_name("api-gateway") == "ApiGatewayAgent"

    def test_no_duplicate_agent_suffix_hyphen(self) -> None:
        """Does NOT add duplicate Agent suffix when name ends with '-agent'.

        This is the main bug fix test case.
        """
        assert derive_class_name("infra-agent") == "InfraAgent"
        assert derive_class_name("gitlab-agent") == "GitlabAgent"
        assert derive_class_name("tf-agent") == "TfAgent"

    def test_no_duplicate_agent_suffix_underscore(self) -> None:
        """Does NOT add duplicate Agent suffix when name ends with '_agent'."""
        assert derive_class_name("infra_agent") == "InfraAgent"
        assert derive_class_name("gitlab_agent") == "GitlabAgent"

    def test_handles_uppercase_agent_suffix(self) -> None:
        """Handles names ending with 'Agent' in various cases."""
        assert derive_class_name("infra-Agent") == "InfraAgent"
        assert derive_class_name("infra-AGENT") == "InfraAgent"

    def test_handles_single_word_agent(self) -> None:
        """Handles the word 'agent' alone."""
        assert derive_class_name("agent") == "Agent"

    def test_handles_complex_names(self) -> None:
        """Handles complex multi-part names."""
        assert derive_class_name("my-super-cool-agent") == "MySuperCoolAgent"
        assert derive_class_name("api-v2-handler") == "ApiV2HandlerAgent"

    def test_converts_to_pascal_case(self) -> None:
        """Converts all parts to PascalCase."""
        assert derive_class_name("my-chatbot") == "MyChatbotAgent"
        assert derive_class_name("API-gateway") == "ApiGatewayAgent"

    def test_handles_spaces_in_name(self) -> None:
        """Handles spaces in names."""
        assert derive_class_name("my agent") == "MyAgent"
        assert derive_class_name("weather bot") == "WeatherBotAgent"


class TestDeriveClassNameEdgeCases:
    """Edge case tests for derive_class_name."""

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("a", "AAgent"),
            ("x-y-z", "XYZAgent"),
            ("test123", "Test123Agent"),
            ("my-123-bot", "My123BotAgent"),
        ],
    )
    def test_various_edge_cases(self, input_name: str, expected: str) -> None:
        """Tests various edge cases with parametrized inputs."""
        assert derive_class_name(input_name) == expected

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            # All these should NOT have duplicate Agent suffix
            ("devops-agent", "DevopsAgent"),
            ("monitoring-agent", "MonitoringAgent"),
            ("security-agent", "SecurityAgent"),
            ("console-ai-agent", "ConsoleAiAgent"),
            ("test-agent", "TestAgent"),
        ],
    )
    def test_agent_suffix_names(self, input_name: str, expected: str) -> None:
        """Tests that agent suffix names don't get duplicate 'Agent'."""
        assert derive_class_name(input_name) == expected
