"""Unit tests for ToolInstructionsMiddleware."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import SystemMessage

from macsdk.middleware.tool_instructions import ToolInstructionsMiddleware


class MockTool:
    """Mock LangChain tool with a name attribute."""

    def __init__(self, name: str) -> None:
        self.name = name


def mock_function_tool() -> None:
    """Mock function tool (has __name__)."""
    pass


class TestToolInstructionsMiddleware:
    """Test suite for ToolInstructionsMiddleware."""

    def test_extract_tool_names_from_functions(self) -> None:
        """Test that tool names are extracted from raw functions."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills, read_skill])
        assert "list_skills" in middleware.tool_names
        assert "read_skill" in middleware.tool_names

    def test_extract_tool_names_from_langchain_tools(self) -> None:
        """Test that tool names are extracted from LangChain BaseTool instances."""
        tool1 = MockTool("list_facts")
        tool2 = MockTool("read_fact")

        middleware = ToolInstructionsMiddleware(tools=[tool1, tool2])  # type: ignore[list-item]
        assert "list_facts" in middleware.tool_names
        assert "read_fact" in middleware.tool_names

    def test_extract_tool_names_mixed(self) -> None:
        """Test extracting names from mixed tool types."""

        def list_skills() -> None:
            pass

        tool = MockTool("read_fact")

        middleware = ToolInstructionsMiddleware(tools=[list_skills, tool])  # type: ignore[list-item]
        assert "list_skills" in middleware.tool_names
        assert "read_fact" in middleware.tool_names

    def test_skills_pattern_detection(self) -> None:
        """Test that skills pattern is detected and instructions are generated."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills, read_skill])
        instructions = middleware._get_instructions()

        assert instructions
        assert "Skills System" in instructions or "skills" in instructions.lower()

    def test_facts_pattern_detection(self) -> None:
        """Test that facts pattern is detected and instructions are generated."""

        def list_facts() -> None:
            pass

        def read_fact() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_facts, read_fact])
        instructions = middleware._get_instructions()

        assert instructions
        assert "Facts System" in instructions or "facts" in instructions.lower()

    def test_combined_pattern_priority(self) -> None:
        """Test that combined pattern takes priority over individual patterns."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        def list_facts() -> None:
            pass

        def read_fact() -> None:
            pass

        middleware = ToolInstructionsMiddleware(
            tools=[list_skills, read_skill, list_facts, read_fact]
        )
        instructions = middleware._get_instructions()

        # Should get combined instructions, not individual ones
        assert instructions
        assert "Knowledge System" in instructions

    def test_no_pattern_match(self) -> None:
        """Test that no instructions are generated when no patterns match."""

        def random_tool() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[random_tool])
        instructions = middleware._get_instructions()

        assert instructions == ""

    def test_instruction_caching(self) -> None:
        """Test that instructions are cached after first retrieval."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills, read_skill])

        # First call should generate and cache
        instructions1 = middleware._get_instructions()
        assert middleware._cached_instructions == instructions1

        # Second call should return cached value
        instructions2 = middleware._get_instructions()
        assert instructions1 == instructions2
        assert instructions2 is instructions1  # Same object

    def test_inject_into_existing_system_message(self) -> None:
        """Test that instructions are appended to existing system message."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills, read_skill])

        # Create mock request with existing system message
        request = MagicMock()
        request.system_message = SystemMessage(content="Original prompt")

        # Inject instructions
        middleware._inject_tool_instructions(request)

        # Verify the system message was updated
        content = str(request.system_message.content)
        assert content.startswith("Original prompt")
        assert "Skills System" in content or "skills" in content.lower()

    def test_create_system_message_if_none(self) -> None:
        """Test that system message is created if it doesn't exist."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills, read_skill])

        # Create mock request with no system message
        request = MagicMock()
        request.system_message = None

        # Inject instructions
        middleware._inject_tool_instructions(request)

        # Verify system message was created
        assert request.system_message is not None
        assert isinstance(request.system_message, SystemMessage)
        content = str(request.system_message.content)
        assert "Skills System" in content or "skills" in content.lower()

    def test_wrap_model_call_when_disabled(self) -> None:
        """Test that wrap_model_call does nothing when disabled."""

        def list_skills() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills], enabled=False)

        request = MagicMock()
        request.system_message = SystemMessage(content="Original")
        original_content = request.system_message.content

        handler = MagicMock(return_value="response")
        result = middleware.wrap_model_call(request, handler)

        # Handler should be called
        handler.assert_called_once_with(request)
        assert result == "response"

        # System message should be unchanged
        assert request.system_message.content == original_content

    @pytest.mark.asyncio
    async def test_awrap_model_call_when_disabled(self) -> None:
        """Test that awrap_model_call does nothing when disabled."""

        def list_skills() -> None:
            pass

        middleware = ToolInstructionsMiddleware(tools=[list_skills], enabled=False)

        request = MagicMock()
        request.system_message = SystemMessage(content="Original")
        original_content = request.system_message.content

        async def async_handler(req):  # type: ignore[no-untyped-def]
            return "response"

        result = await middleware.awrap_model_call(request, async_handler)

        # Handler should be called and return value passed through
        assert result == "response"

        # System message should be unchanged
        assert request.system_message.content == original_content

    def test_wrap_model_call_injects_instructions(self) -> None:
        """Test that wrap_model_call injects instructions."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(
            tools=[list_skills, read_skill], enabled=True
        )

        request = MagicMock()
        request.system_message = SystemMessage(content="Original")

        handler = MagicMock(return_value="response")
        middleware.wrap_model_call(request, handler)

        # System message should be modified
        assert request.system_message.content.startswith("Original")
        assert len(request.system_message.content) > len("Original")

    @pytest.mark.asyncio
    async def test_awrap_model_call_injects_instructions(self) -> None:
        """Test that awrap_model_call injects instructions."""

        def list_skills() -> None:
            pass

        def read_skill() -> None:
            pass

        middleware = ToolInstructionsMiddleware(
            tools=[list_skills, read_skill], enabled=True
        )

        request = MagicMock()
        request.system_message = SystemMessage(content="Original")

        async def async_handler(req):  # type: ignore[no-untyped-def]
            return "response"

        await middleware.awrap_model_call(request, async_handler)

        # System message should be modified
        assert request.system_message.content.startswith("Original")
        assert len(request.system_message.content) > len("Original")
