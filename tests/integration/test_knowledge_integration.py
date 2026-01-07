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
        """Test the complete skills workflow: list → read."""
        tools = create_skills_tools(test_skills_dir)
        list_skills, read_skill = tools

        # List skills
        skills = list_skills.invoke({})
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"
        assert skills[0]["description"] == "A test skill for integration testing"

        # Read skill
        content = read_skill.invoke({"path": "test-skill.md"})
        assert "Test Skill" in content
        assert "First step" in content
        assert "Second step" in content
        assert "Third step" in content

    def test_facts_tools_workflow(self, test_facts_dir: Path) -> None:
        """Test the complete facts workflow: list → read."""
        tools = create_facts_tools(test_facts_dir)
        list_facts, read_fact = tools

        # List facts
        facts = list_facts.invoke({})
        assert len(facts) == 1
        assert facts[0]["name"] == "test-fact"
        assert facts[0]["description"] == "A test fact for integration testing"

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
        assert len(all_tools) == 4

        # Extract tools
        list_skills = next(t for t in all_tools if t.name == "list_skills")
        read_skill = next(t for t in all_tools if t.name == "read_skill")
        list_facts = next(t for t in all_tools if t.name == "list_facts")
        read_fact = next(t for t in all_tools if t.name == "read_fact")

        # Use all tools in sequence
        skills = list_skills.invoke({})
        assert len(skills) == 1

        skill_content = read_skill.invoke({"path": "test-skill.md"})
        assert "First step" in skill_content

        facts = list_facts.invoke({})
        assert len(facts) == 1

        fact_content = read_fact.invoke({"path": "test-fact.md"})
        assert "Service ID: 123" in fact_content

    def test_middleware_integration(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test that middleware correctly injects instructions."""
        # Create tools
        skills_tools = create_skills_tools(test_skills_dir)
        facts_tools = create_facts_tools(test_facts_dir)
        all_tools = [*skills_tools, *facts_tools]

        # Create middleware
        middleware = ToolInstructionsMiddleware(tools=all_tools)

        # Verify tool names were extracted
        assert "list_skills" in middleware.tool_names
        assert "read_skill" in middleware.tool_names
        assert "list_facts" in middleware.tool_names
        assert "read_fact" in middleware.tool_names

        # Get instructions (should be combined)
        instructions = middleware._get_instructions()
        assert instructions
        assert "Knowledge System" in instructions
        assert "Skills" in instructions
        assert "Facts" in instructions

    def test_middleware_injection(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test that middleware correctly modifies system messages."""
        # Create tools
        skills_tools = create_skills_tools(test_skills_dir)
        all_tools = [*skills_tools]

        # Create middleware
        middleware = ToolInstructionsMiddleware(tools=all_tools)

        # Create a mock request with system message
        from unittest.mock import MagicMock

        request = MagicMock()
        request.system_message = SystemMessage(content="Original system prompt")

        # Inject instructions
        middleware._inject_tool_instructions(request)

        # Verify system message was modified
        assert request.system_message.content.startswith("Original system prompt")
        assert "Skills System" in request.system_message.content
        assert "list_skills()" in request.system_message.content

    def test_error_handling_invalid_path(self, test_skills_dir: Path) -> None:
        """Test error handling for invalid file paths."""
        tools = create_skills_tools(test_skills_dir)
        read_skill = tools[1]

        # Try to read non-existent skill
        result = read_skill.invoke({"path": "nonexistent.md"})
        assert "Error" in result
        assert "not found" in result

    def test_error_handling_path_traversal(self, test_skills_dir: Path) -> None:
        """Test security against path traversal attacks."""
        tools = create_skills_tools(test_skills_dir)
        read_skill = tools[1]

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
        list_skills = tools[0]

        # Should return empty list, not error
        skills = list_skills.invoke({})
        assert skills == []

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
        list_skills, read_skill = tools

        # List should show both
        skills = list_skills.invoke({})
        assert len(skills) == 2

        names = {s["name"] for s in skills}
        assert "deploy-frontend" in names
        assert "deploy-backend" in names

        # Read using relative path
        content = read_skill.invoke({"path": "deploy/deploy-frontend.md"})
        assert "Content" in content

    def test_partial_knowledge(self, test_skills_dir: Path) -> None:
        """Test using only skills without facts."""
        # Create only skills tools
        tools = create_skills_tools(test_skills_dir)
        middleware = ToolInstructionsMiddleware(tools=tools)

        # Should generate skills-only instructions
        instructions = middleware._get_instructions()
        assert "Skills System" in instructions
        assert "Facts" not in instructions

    def test_middleware_caching(
        self, test_skills_dir: Path, test_facts_dir: Path
    ) -> None:
        """Test that middleware caches instructions for performance."""
        tools = [
            *create_skills_tools(test_skills_dir),
            *create_facts_tools(test_facts_dir),
        ]
        middleware = ToolInstructionsMiddleware(tools=tools)

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
        assert "list_skills" in middleware.tool_names
        assert "read_skill" in middleware.tool_names
        assert "custom_tool" in middleware.tool_names
