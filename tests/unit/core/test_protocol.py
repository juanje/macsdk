"""Tests for SpecialistAgent protocol."""

from __future__ import annotations

from macsdk.core import SpecialistAgent

# Test constants for this module
TEST_AGENT_NAME = "test_agent"
TEST_AGENT_CAPABILITIES = "Test agent capabilities"


class TestSpecialistAgentProtocol:
    """Tests for the SpecialistAgent protocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """Protocol can be used with isinstance checks."""

        # Create a valid implementation
        class ValidAgent:
            name = TEST_AGENT_NAME
            capabilities = TEST_AGENT_CAPABILITIES

            async def run(self, query: str, context: dict | None = None) -> dict:
                return {}

            def as_tool(self):
                return None

        agent = ValidAgent()
        assert isinstance(agent, SpecialistAgent)

    def test_valid_implementation_passes_isinstance(self) -> None:
        """A class with all required attributes passes isinstance check."""

        class MyAgent:
            name = TEST_AGENT_NAME
            capabilities = TEST_AGENT_CAPABILITIES

            async def run(self, query: str, context: dict | None = None) -> dict:
                return {"response": "test", "agent_name": self.name}

            def as_tool(self):
                return None

        agent = MyAgent()
        assert isinstance(agent, SpecialistAgent)

    def test_missing_name_fails_isinstance(self) -> None:
        """Class without 'name' attribute fails isinstance check."""

        class NoName:
            capabilities = TEST_AGENT_CAPABILITIES

            async def run(self, query: str, context: dict | None = None) -> dict:
                return {}

            def as_tool(self):
                return None

        agent = NoName()
        assert not isinstance(agent, SpecialistAgent)

    def test_missing_capabilities_fails_isinstance(self) -> None:
        """Class without 'capabilities' attribute fails isinstance check."""

        class NoCapabilities:
            name = TEST_AGENT_NAME

            async def run(self, query: str, context: dict | None = None) -> dict:
                return {}

            def as_tool(self):
                return None

        agent = NoCapabilities()
        assert not isinstance(agent, SpecialistAgent)

    def test_missing_run_method_fails_isinstance(self) -> None:
        """Class without 'run' method fails isinstance check."""

        class NoRun:
            name = TEST_AGENT_NAME
            capabilities = TEST_AGENT_CAPABILITIES

            def as_tool(self):
                return None

        agent = NoRun()
        assert not isinstance(agent, SpecialistAgent)

    def test_missing_as_tool_method_fails_isinstance(self) -> None:
        """Class without 'as_tool' method fails isinstance check."""

        class NoAsTool:
            name = TEST_AGENT_NAME
            capabilities = TEST_AGENT_CAPABILITIES

            async def run(self, query: str, context: dict | None = None) -> dict:
                return {}

        agent = NoAsTool()
        assert not isinstance(agent, SpecialistAgent)
