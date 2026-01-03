"""Tests for RAG configuration validators."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from macsdk.agents.rag.config import RAGConfig


class TestRAGConfigValidators:
    """Tests for Pydantic Field validators in RAGConfig."""

    def test_default_values_valid(self) -> None:
        """Default configuration is valid."""
        config = RAGConfig()
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.retriever_k == 6

    def test_chunk_size_zero_raises(self) -> None:
        """Chunk size 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="chunk_size"):
            RAGConfig(chunk_size=0)

    def test_chunk_size_negative_raises(self) -> None:
        """Negative chunk size raises ValidationError."""
        with pytest.raises(ValidationError, match="chunk_size"):
            RAGConfig(chunk_size=-100)

    def test_chunk_overlap_negative_raises(self) -> None:
        """Negative chunk overlap raises ValidationError."""
        with pytest.raises(ValidationError, match="chunk_overlap"):
            RAGConfig(chunk_overlap=-1)

    def test_chunk_overlap_zero_valid(self) -> None:
        """Zero chunk overlap is valid (no overlap)."""
        config = RAGConfig(chunk_overlap=0)
        assert config.chunk_overlap == 0

    def test_chunk_overlap_greater_than_size_raises(self) -> None:
        """Chunk overlap >= chunk size raises ValidationError."""
        with pytest.raises(ValidationError, match="chunk_overlap.*smaller.*chunk_size"):
            RAGConfig(chunk_size=100, chunk_overlap=100)

    def test_chunk_overlap_greater_than_size_raises_2(self) -> None:
        """Chunk overlap > chunk size raises ValidationError."""
        with pytest.raises(ValidationError, match="chunk_overlap.*smaller.*chunk_size"):
            RAGConfig(chunk_size=100, chunk_overlap=150)

    def test_chunk_overlap_smaller_than_size_valid(self) -> None:
        """Chunk overlap < chunk size is valid."""
        config = RAGConfig(chunk_size=100, chunk_overlap=50)
        assert config.chunk_overlap == 50
        assert config.chunk_size == 100

    def test_max_depth_zero_raises(self) -> None:
        """Max depth 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="max_depth"):
            RAGConfig(max_depth=0)

    def test_max_depth_one_valid(self) -> None:
        """Max depth 1 is valid."""
        config = RAGConfig(max_depth=1)
        assert config.max_depth == 1

    def test_retriever_k_zero_raises(self) -> None:
        """Retriever k 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="retriever_k"):
            RAGConfig(retriever_k=0)

    def test_retriever_k_one_valid(self) -> None:
        """Retriever k 1 is valid."""
        config = RAGConfig(retriever_k=1)
        assert config.retriever_k == 1

    def test_max_rewrites_negative_raises(self) -> None:
        """Negative max rewrites raises ValidationError."""
        with pytest.raises(ValidationError, match="max_rewrites"):
            RAGConfig(max_rewrites=-1)

    def test_max_rewrites_zero_valid(self) -> None:
        """Zero max rewrites is valid (no rewrites)."""
        config = RAGConfig(max_rewrites=0)
        assert config.max_rewrites == 0

    def test_temperature_too_high_raises(self) -> None:
        """Temperature above 2.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="temperature"):
            RAGConfig(temperature=2.5)

    def test_temperature_negative_raises(self) -> None:
        """Negative temperature raises ValidationError."""
        with pytest.raises(ValidationError, match="temperature"):
            RAGConfig(temperature=-0.1)

    def test_temperature_at_boundaries_valid(self) -> None:
        """Temperature at 0.0 and 2.0 are valid."""
        config_min = RAGConfig(temperature=0.0)
        config_max = RAGConfig(temperature=2.0)
        assert config_min.temperature == 0.0
        assert config_max.temperature == 2.0

    def test_env_var_overrides_constructor_with_rag_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RAG_ prefixed env var overrides constructor argument."""
        monkeypatch.setenv("RAG_CHUNK_SIZE", "2000")
        config = RAGConfig(chunk_size=500)  # simulates yaml value
        assert config.chunk_size == 2000
