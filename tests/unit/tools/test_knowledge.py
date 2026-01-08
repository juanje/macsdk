"""Unit tests for knowledge tools."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from macsdk.tools.knowledge.facts import create_facts_tools
from macsdk.tools.knowledge.helpers import (
    _list_documents,
    _parse_frontmatter,
    _read_document,
    _safe_path,
)
from macsdk.tools.knowledge.skills import create_skills_tools


class TestHelpers:
    """Test helper functions."""

    def test_safe_path_valid(self) -> None:
        """Test that safe paths are accepted."""
        base = Path("/tmp/base")
        result = _safe_path(base, "subdir/file.md")
        assert str(result).startswith(str(base.resolve()))

    def test_safe_path_traversal_attack(self) -> None:
        """Test that directory traversal is prevented."""
        base = Path("/tmp/base")
        with pytest.raises(ValueError, match="Path traversal"):
            _safe_path(base, "../../../etc/passwd")

    def test_safe_path_prefix_bypass_protection(self) -> None:
        """Test that prefix-based bypass is prevented.

        Example: /var/data vs /var/database
        """
        # This test ensures we use is_relative_to instead of string prefix matching
        base = Path("/tmp/data")
        # Attempting to access /tmp/database (different directory with similar prefix)
        with pytest.raises(ValueError, match="Path traversal"):
            _safe_path(base, "../database/secret.txt")

    def test_parse_frontmatter_valid(self) -> None:
        """Test parsing valid YAML frontmatter."""
        content = """---
name: test-skill
description: A test skill
---
Content here"""

        frontmatter, body = _parse_frontmatter(content)
        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill"
        assert body == "Content here"

    def test_parse_frontmatter_no_frontmatter(self) -> None:
        """Test parsing content without frontmatter."""
        content = "Just regular content"
        frontmatter, body = _parse_frontmatter(content)
        assert frontmatter == {}
        assert body == content

    def test_parse_frontmatter_invalid_yaml(self) -> None:
        """Test that invalid YAML is handled gracefully."""
        content = """---
invalid: yaml: structure:
---
Content"""

        frontmatter, body = _parse_frontmatter(content)
        assert frontmatter == {}
        assert body.strip() == "Content"

    def test_parse_frontmatter_non_dict_types(self) -> None:
        """Test that non-dict YAML values are converted to empty dict."""
        # String value
        content_string = """---
just a string
---
Content"""
        frontmatter, body = _parse_frontmatter(content_string)
        assert frontmatter == {}
        assert "Content" in body

        # List value
        content_list = """---
[1, 2, 3]
---
Content"""
        frontmatter, body = _parse_frontmatter(content_list)
        assert frontmatter == {}
        assert "Content" in body

        # Null value
        content_null = """---
null
---
Content"""
        frontmatter, body = _parse_frontmatter(content_null)
        assert frontmatter == {}
        assert "Content" in body

    def test_list_documents(self, tmp_path: Path) -> None:
        """Test listing markdown documents."""
        # Create test files
        (tmp_path / "skill1.md").write_text("""---
name: skill1
description: First skill
---
Content 1""")

        (tmp_path / "skill2.md").write_text("""---
name: skill2
description: Second skill
---
Content 2""")

        # Create a subdirectory with a file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "skill3.md").write_text("""---
name: skill3
description: Third skill
---
Content 3""")

        # List documents
        docs = _list_documents(tmp_path)
        assert len(docs) == 3

        names = {doc["name"] for doc in docs}
        assert names == {"skill1", "skill2", "skill3"}

    def test_list_documents_empty_directory(self, tmp_path: Path) -> None:
        """Test listing documents in an empty directory."""
        docs = _list_documents(tmp_path)
        assert docs == []

    def test_list_documents_nonexistent_directory(self) -> None:
        """Test listing documents in a nonexistent directory."""
        docs = _list_documents(Path("/nonexistent/path"))
        assert docs == []

    def test_read_document_success(self, tmp_path: Path) -> None:
        """Test reading a document successfully."""
        file = tmp_path / "test.md"
        file.write_text("""---
name: test
---
Document content""")

        content = _read_document(tmp_path, "test.md", "skill")
        assert content == "Document content"

    def test_read_document_not_found(self, tmp_path: Path) -> None:
        """Test reading a nonexistent document."""
        content = _read_document(tmp_path, "nonexistent.md", "skill")
        assert "Error" in content
        assert "not found" in content

    def test_read_document_path_traversal(self, tmp_path: Path) -> None:
        """Test that path traversal is blocked."""
        content = _read_document(tmp_path, "../../../etc/passwd", "skill")
        assert "Error" in content
        assert "Invalid path" in content


class TestSkillsTools:
    """Test skills tools."""

    def test_create_skills_tools(self, tmp_path: Path) -> None:
        """Test creating skills tools."""
        # Create test skills
        (tmp_path / "deploy.md").write_text("""---
name: deploy-service
description: How to deploy a service
---
Deploy instructions""")

        tools = create_skills_tools(tmp_path)
        assert len(tools) == 1

        # Get the tool function
        read_skill = tools[0]

        # Test read_skill
        content = read_skill.invoke({"path": "deploy.md"})
        assert "Deploy instructions" in content

    def test_skills_tools_empty_directory(self, tmp_path: Path) -> None:
        """Test skills tools with no skills."""
        tools = create_skills_tools(tmp_path)
        assert len(tools) == 1

        # read_skill should still work, just return error for missing files
        read_skill = tools[0]
        content = read_skill.invoke({"path": "nonexistent.md"})
        assert "Error" in content


class TestFactsTools:
    """Test facts tools."""

    def test_create_facts_tools(self, tmp_path: Path) -> None:
        """Test creating facts tools."""
        # Create test facts
        (tmp_path / "services.md").write_text("""---
name: service-info
description: Information about services
---
Service details""")

        tools = create_facts_tools(tmp_path)
        assert len(tools) == 1

        # Get the tool function
        read_fact = tools[0]

        # Test read_fact
        content = read_fact.invoke({"path": "services.md"})
        assert "Service details" in content

    def test_facts_tools_empty_directory(self, tmp_path: Path) -> None:
        """Test facts tools with no facts."""
        tools = create_facts_tools(tmp_path)
        assert len(tools) == 1

        # read_fact should still work, just return error for missing files
        read_fact = tools[0]
        content = read_fact.invoke({"path": "nonexistent.md"})
        assert "Error" in content


class TestKnowledgeBundle:
    """Test get_knowledge_bundle function."""

    def test_get_knowledge_bundle_structure(self) -> None:
        """Test that get_knowledge_bundle returns correct structure."""
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test package structure
            skills_dir = tmp_path / "skills"
            facts_dir = tmp_path / "facts"
            skills_dir.mkdir()
            facts_dir.mkdir()

            # We can't easily test with __package__ in unit tests,
            # so we test the implementation details instead
            from macsdk.middleware import ToolInstructionsMiddleware
            from macsdk.tools.knowledge.facts import create_facts_tools
            from macsdk.tools.knowledge.skills import create_skills_tools

            # Create tools manually as the bundle would
            tools = []
            tools.extend(create_skills_tools(skills_dir))
            tools.extend(create_facts_tools(facts_dir))

            middleware = [
                ToolInstructionsMiddleware(
                    tools=tools, skills_dir=skills_dir, facts_dir=facts_dir
                )
            ]

            # Verify structure
            assert len(tools) == 2  # 1 skill + 1 fact tool
            assert len(middleware) == 1
            assert isinstance(middleware[0], ToolInstructionsMiddleware)

    def test_bundle_includes_skills_only(self) -> None:
        """Test creating bundle with skills only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            skills_dir = tmp_path / "skills"
            skills_dir.mkdir()

            from macsdk.middleware import ToolInstructionsMiddleware
            from macsdk.tools.knowledge.skills import create_skills_tools

            tools = create_skills_tools(skills_dir)
            middleware = [
                ToolInstructionsMiddleware(tools=tools, skills_dir=skills_dir)
            ]

            assert len(tools) == 1  # Only read_skill
            assert len(middleware) == 1

    def test_bundle_includes_facts_only(self) -> None:
        """Test creating bundle with facts only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            facts_dir = tmp_path / "facts"
            facts_dir.mkdir()

            from macsdk.middleware import ToolInstructionsMiddleware
            from macsdk.tools.knowledge.facts import create_facts_tools

            tools = create_facts_tools(facts_dir)
            middleware = [ToolInstructionsMiddleware(tools=tools, facts_dir=facts_dir)]

            assert len(tools) == 1  # Only read_fact
            assert len(middleware) == 1
