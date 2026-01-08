"""Integration tests for knowledge tools workflow."""

from __future__ import annotations

from pathlib import Path

import pytest
from langchain_core.messages import SystemMessage

from macsdk.middleware import ToolInstructionsMiddleware
from macsdk.tools.knowledge.facts import create_facts_tools
from macsdk.tools.knowledge.skills import create_skills_tools


class TestKnowledgeToolsIntegration:
    """Integration tests for the complete knowledge tools workflow."""

    @pytest.fixture
    def test_skills_dir(self, tmp_path: Path) -> Path:
        """Create a temporary skills directory with test files."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create test skill
        (skills_dir / "test-skill.md").write_text("""---
name: test-skill
description: A test skill for integration testing
---

# Test Skill

This is a test skill for integration testing.

## Steps

1. First step
2. Second step
3. Third step
""")

        return skills_dir

    @pytest.fixture
    def test_facts_dir(self, tmp_path: Path) -> Path:
        """Create a temporary facts directory with test files."""
        facts_dir = tmp_path / "facts"
        facts_dir.mkdir()

        # Create test fact
        (facts_dir / "test-fact.md").write_text("""---
name: test-fact
description: A test fact for integration testing
---

# Test Fact

This is a test fact for integration testing.

## Information

- Service ID: 123
- Service Name: Test Service
- Endpoint: https://test.example.com
""")

        return facts_dir

    def test_skills_tools_workflow(self, test_skills_dir: Path) -> None:
        """Test the skills workflow: read."""
        tools = create_skills_tools(test_skills_dir)
        assert len(tools) == 1

        read_skill = tools[0]

        # Read skill
        content = read_skill.invoke({"path": "test-skill.md"})
        assert "Test Skill" in content
        assert "First step" in content
        assert "Second step" in content
        assert "Third step" in content

    def test_facts_tools_workflow(self, test_facts_dir: Path) -> None:
        """Test the facts workflow: read."""
        tools = create_facts_tools(test_facts_dir)
        assert len(tools) == 1

        read_fact = tools[0]

        # Read fact
        content = read_fact.invoke({"path": "test-fact.md"})
        assert "Test Fact" in content
        assert "Service ID: 123" in content
        assert "Service Name: Test Service" in content

    def test_combined_workflow(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test using skills and facts together."""
        skills_tools = create_skills_tools(test_skills_dir)
        facts_tools = create_facts_tools(test_facts_dir)

        all_tools = [*skills_tools, *facts_tools]
        assert len(all_tools) == 2

        # Extract tools
        read_skill = next(t for t in all_tools if t.name == "read_skill")
        read_fact = next(t for t in all_tools if t.name == "read_fact")

        # Use tools to read content
        skill_content = read_skill.invoke({"path": "test-skill.md"})
        assert "First step" in skill_content

        fact_content = read_fact.invoke({"path": "test-fact.md"})
        assert "Service ID: 123" in fact_content

    def test_middleware_integration(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test that middleware correctly injects instructions and inventory."""
        # Create tools
        skills_tools = create_skills_tools(test_skills_dir)
        facts_tools = create_facts_tools(test_facts_dir)
        all_tools = [*skills_tools, *facts_tools]

        # Create middleware with directory paths for inventory
        middleware = ToolInstructionsMiddleware(
            tools=all_tools, skills_dir=test_skills_dir, facts_dir=test_facts_dir
        )

        # Verify tool names were extracted
        assert "read_skill" in middleware.tool_names
        assert "read_fact" in middleware.tool_names

        # Verify inventories were loaded
        assert len(middleware._skills_inventory) == 1
        assert len(middleware._facts_inventory) == 1

        # Get instructions (should be combined with inventory)
        instructions = middleware._get_instructions()
        assert instructions
        assert "Knowledge System" in instructions
        assert "Skills" in instructions
        assert "Facts" in instructions
        assert "Available Skills" in instructions
        assert "Available Facts" in instructions
        assert "test-skill" in instructions
        assert "test-fact" in instructions

    def test_middleware_injection(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test that middleware correctly modifies system messages."""
        # Create tools
        skills_tools = create_skills_tools(test_skills_dir)
        all_tools = [*skills_tools]

        # Create middleware with skills directory for inventory
        middleware = ToolInstructionsMiddleware(
            tools=all_tools, skills_dir=test_skills_dir
        )

        # Create a mock request with system message
        from unittest.mock import MagicMock

        request = MagicMock()
        request.system_message = SystemMessage(content="Original system prompt")

        # Inject instructions
        middleware._inject_tool_instructions(request)

        # Verify system message was modified
        assert request.system_message.content.startswith("Original system prompt")
        assert "Skills System" in request.system_message.content
        assert "read_skill(path)" in request.system_message.content
        assert "Available Skills" in request.system_message.content

    def test_error_handling_invalid_path(self, test_skills_dir: Path) -> None:
        """Test error handling for invalid file paths."""
        tools = create_skills_tools(test_skills_dir)
        read_skill = tools[0]

        # Try to read non-existent skill
        result = read_skill.invoke({"path": "nonexistent.md"})
        assert "Error" in result
        assert "not found" in result

    def test_error_handling_path_traversal(self, test_skills_dir: Path) -> None:
        """Test security against path traversal attacks."""
        tools = create_skills_tools(test_skills_dir)
        read_skill = tools[0]

        # Try path traversal
        result = read_skill.invoke({"path": "../../../etc/passwd"})
        assert "Error" in result
        assert "Invalid path" in result

    def test_empty_directories(self, tmp_path: Path) -> None:
        """Test behavior with empty knowledge directories."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Create tools for empty directory
        tools = create_skills_tools(empty_dir)
        assert len(tools) == 1
        read_skill = tools[0]

        # Reading non-existent file should return error message
        result = read_skill.invoke({"path": "nonexistent.md"})
        assert "Error" in result

    def test_hierarchical_structure(self, tmp_path: Path) -> None:
        """Test that hierarchical skill organization works."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create nested structure
        deploy_dir = skills_dir / "deploy"
        deploy_dir.mkdir()

        (deploy_dir / "deploy-frontend.md").write_text("""---
name: deploy-frontend
description: Deploy frontend service
---
Content""")

        (deploy_dir / "deploy-backend.md").write_text("""---
name: deploy-backend
description: Deploy backend service
---
Content""")

        # Create tools
        tools = create_skills_tools(skills_dir)
        assert len(tools) == 1
        read_skill = tools[0]

        # Create middleware to verify inventory captures both
        middleware = ToolInstructionsMiddleware(tools=tools, skills_dir=skills_dir)
        assert len(middleware._skills_inventory) == 2

        names = {s["name"] for s in middleware._skills_inventory}
        assert "deploy-frontend" in names
        assert "deploy-backend" in names

        # Read using relative path
        content = read_skill.invoke({"path": "deploy/deploy-frontend.md"})
        assert "Content" in content

    def test_partial_knowledge(self, test_skills_dir: Path) -> None:
        """Test using only skills without facts."""
        # Create only skills tools
        tools = create_skills_tools(test_skills_dir)
        middleware = ToolInstructionsMiddleware(tools=tools, skills_dir=test_skills_dir)

        # Should generate skills-only instructions with inventory
        instructions = middleware._get_instructions()
        assert "Skills System" in instructions
        assert "Available Skills" in instructions
        assert "Facts" not in instructions or "Available Facts" not in instructions

    def test_middleware_caching(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test that middleware caches instructions for performance."""
        tools = [
            *create_skills_tools(test_skills_dir),
            *create_facts_tools(test_facts_dir),
        ]
        middleware = ToolInstructionsMiddleware(
            tools=tools, skills_dir=test_skills_dir, facts_dir=test_facts_dir
        )

        # First call
        instructions1 = middleware._get_instructions()
        assert middleware._cached_instructions is not None

        # Second call should return cached value
        instructions2 = middleware._get_instructions()
        assert instructions1 is instructions2  # Same object (cached)

    def test_tool_name_extraction_mixed_types(self, test_skills_dir: Path) -> None:
        """Test that tool name extraction works with mixed tool types."""
        # LangChain tools (from create_skills_tools)
        langchain_tools = create_skills_tools(test_skills_dir)

        # Raw function tool
        def custom_tool() -> str:
            return "test"

        # Mix both types
        all_tools = [*langchain_tools, custom_tool]
        middleware = ToolInstructionsMiddleware(tools=all_tools)

        # Should extract all names correctly
        assert "read_skill" in middleware.tool_names
        assert "custom_tool" in middleware.tool_names
