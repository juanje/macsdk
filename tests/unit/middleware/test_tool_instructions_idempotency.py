"""Tests for ToolInstructionsMiddleware idempotency."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from langchain_core.messages import SystemMessage

from macsdk.middleware.tool_instructions import ToolInstructionsMiddleware

if TYPE_CHECKING:
    pass


class TestToolInstructionsIdempotency:
    """Test suite for ToolInstructionsMiddleware idempotency."""

    def test_idempotency_prevents_duplicate_injection(self) -> None:
        """Test that instructions are not duplicated on multiple calls."""

        # Create mock tools
        class MockTool:
            name = "list_skills"

        class MockTool2:
            name = "read_skill"

        tools = [MockTool(), MockTool2()]  # type: ignore[var-annotated]
        middleware = ToolInstructionsMiddleware(tools=tools)  # type: ignore[arg-type]

        # Create mock request
        class MockRequest:
            system_message = SystemMessage(content="Original prompt")

        request = MockRequest()

        # First injection
        middleware._inject_tool_instructions(request)  # type: ignore[arg-type]
        first_content = request.system_message.content
        assert "## Skills System" in first_content
        assert first_content.count("## Skills System") == 1

        # Second injection (simulating retry)
        middleware._inject_tool_instructions(request)  # type: ignore[arg-type]
        second_content = request.system_message.content

        # Should be identical (idempotent)
        assert second_content == first_content
        assert second_content.count("## Skills System") == 1

    def test_idempotency_with_wrap_model_call(self) -> None:
        """Test idempotency through wrap_model_call interface."""

        class MockTool:
            name = "list_facts"

        class MockTool2:
            name = "read_fact"

        tools = [MockTool(), MockTool2()]  # type: ignore[var-annotated]
        middleware = ToolInstructionsMiddleware(tools=tools)  # type: ignore[arg-type]

        class MockRequest:
            system_message = SystemMessage(content="Base prompt")

        def mock_handler(req: MockRequest) -> dict:
            return {"response": "test"}

        request = MockRequest()

        # Call wrap_model_call twice (simulating retries)
        middleware.wrap_model_call(request, mock_handler)  # type: ignore[arg-type]
        first_content = request.system_message.content

        middleware.wrap_model_call(request, mock_handler)  # type: ignore[arg-type]
        second_content = request.system_message.content

        # Should be identical
        assert second_content == first_content
        assert first_content.count("## Facts System") == 1

    @pytest.mark.asyncio
    async def test_idempotency_async(self) -> None:
        """Test idempotency in async path."""

        class MockTool:
            name = "list_skills"

        class MockTool2:
            name = "read_skill"

        tools = [MockTool(), MockTool2()]  # type: ignore[var-annotated]
        middleware = ToolInstructionsMiddleware(tools=tools)  # type: ignore[arg-type]

        class MockRequest:
            system_message = SystemMessage(content="Async prompt")

        async def mock_handler(req: MockRequest) -> dict:
            return {"response": "async test"}

        request = MockRequest()

        # Call awrap_model_call twice
        await middleware.awrap_model_call(request, mock_handler)  # type: ignore[arg-type]
        first_content = request.system_message.content

        await middleware.awrap_model_call(request, mock_handler)  # type: ignore[arg-type]
        second_content = request.system_message.content

        # Should be identical
        assert second_content == first_content
        assert "## Skills System" in first_content
