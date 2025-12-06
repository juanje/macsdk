"""Shared fixtures for MACSDK tests.

This module provides common fixtures for testing:
- Mock agents that implement SpecialistAgent protocol
- Clean registry management
- Environment variable mocking
- Sample state for chatbot tests

Note: Test constants are defined locally in each test module
to avoid import issues with pytest's collection mechanism.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Generator
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from macsdk.core import ChatbotState

# Default values for mock agent (used by fixtures)
_DEFAULT_AGENT_NAME = "mock_agent"
_DEFAULT_AGENT_CAPABILITIES = "Mock capabilities"
_DEFAULT_AGENT_RESPONSE = "Mock response"


# =============================================================================
# MOCK AGENT
# =============================================================================


class MockAgent:
    """Mock implementation of SpecialistAgent for testing.

    Implements the SpecialistAgent protocol without external dependencies.
    """

    def __init__(
        self,
        name: str = _DEFAULT_AGENT_NAME,
        capabilities: str = _DEFAULT_AGENT_CAPABILITIES,
    ):
        """Initialize mock agent.

        Args:
            name: Agent identifier.
            capabilities: Agent capabilities description.
        """
        self.name = name
        self.capabilities = capabilities

    async def run(
        self,
        query: str,
        context: dict | None = None,
        config: dict | None = None,
    ) -> dict:
        """Mock run method.

        Args:
            query: User query.
            context: Optional context.
            config: Optional config.

        Returns:
            Mock response dictionary.
        """
        return {
            "response": f"{_DEFAULT_AGENT_RESPONSE}: {query}",
            "agent_name": self.name,
            "tools_used": [],
        }

    def as_tool(self) -> MagicMock:
        """Return a mock tool.

        Returns:
            MagicMock representing a LangChain tool.
        """
        mock_tool = MagicMock()
        mock_tool.name = f"invoke_{self.name}"
        return mock_tool


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_agent() -> MockAgent:
    """Create a mock agent for testing.

    Returns:
        MockAgent instance with default values.
    """
    return MockAgent()


@pytest.fixture
def mock_agent_factory():
    """Factory for creating mock agents with custom names.

    Returns:
        Function that creates MockAgent instances.
    """

    def _create(
        name: str = _DEFAULT_AGENT_NAME,
        capabilities: str = _DEFAULT_AGENT_CAPABILITIES,
    ) -> MockAgent:
        return MockAgent(name=name, capabilities=capabilities)

    return _create


@pytest.fixture
def sample_state() -> "ChatbotState":
    """Create a sample chatbot state for testing.

    Returns:
        ChatbotState with test values.
    """
    return {
        "messages": [],
        "user_query": "test query",
        "chatbot_response": "",
        "workflow_step": "query",
    }


@pytest.fixture
def clean_registry():
    """Provide a clean registry for tests, restoring original state after.

    Yields:
        Empty AgentRegistry that is cleaned up after the test.
    """
    from macsdk.core import get_registry

    registry = get_registry()
    original_agents = dict(registry._agents)
    registry.clear()

    yield registry

    # Restore original agents
    registry.clear()
    registry._agents.update(original_agents)


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Mock environment variables for testing.

    Provides a clean environment without real API keys.
    This prevents tests from accidentally using real credentials.

    Yields:
        Dictionary of mocked environment variables.
    """
    mock_vars = {
        "GOOGLE_API_KEY": "test-api-key-12345",
        "LLM_MODEL": "test-model",
        "LLM_TEMPERATURE": "0.5",
    }

    with patch.dict(os.environ, mock_vars, clear=False):
        yield mock_vars


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove API-related environment variables for testing.

    Use this when testing configuration error handling.

    Yields:
        None (environment is cleaned).
    """
    keys_to_remove = ["GOOGLE_API_KEY", "LLM_MODEL", "LLM_TEMPERATURE"]
    original_values = {key: os.environ.get(key) for key in keys_to_remove}

    # Remove keys
    for key in keys_to_remove:
        os.environ.pop(key, None)

    yield

    # Restore original values
    for key, value in original_values.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
