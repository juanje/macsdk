"""RAG-specific configuration management.

This module provides configuration classes for the RAG agent,
loaded from the `rag` section of config.yml.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from macsdk.core.config import load_config_from_yaml

logger = logging.getLogger(__name__)

# Default documentation URL (LangChain docs)
DEFAULT_RAG_SOURCE = {
    "name": "langchain",
    "url": "https://python.langchain.com/docs/introduction/",
    "tags": ["framework", "llm", "agents"],
}


class RAGSourceConfig(BaseModel):
    """Configuration for a single documentation source.

    Supported types:
    - html: Web pages (crawled recursively)
    - markdown: Markdown files (local path or remote URL)

    For markdown type, the url/path field can be:
    - A URL to a .md file (https://...)
    - A local file path (/path/to/file.md or ./relative/path.md)
    - A directory path to load all .md files recursively
    """

    name: str = Field(description="Human-readable name for the source")
    url: str = Field(description="URL or local path to the source")
    type: str = Field(
        default="html",
        description="Source type: 'html' for web pages, 'markdown' for .md files",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for filtering and metadata",
    )
    cert_url: str | None = Field(
        default=None,
        description="URL to download SSL certificate (auto-cached)",
    )
    cert_path: str | None = Field(
        default=None,
        description="Local path to SSL certificate file",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify SSL certificates (disable for self-signed)",
    )


class RAGConfig(BaseModel):
    """Configuration for the RAG agent.

    This configuration is loaded from the `rag` section of config.yml.
    All settings have sensible defaults for out-of-the-box usage.
    """

    enabled: bool = Field(
        default=True,
        description="Whether RAG is enabled",
    )

    # Documentation sources
    sources: list[RAGSourceConfig] = Field(
        default_factory=lambda: [RAGSourceConfig(**DEFAULT_RAG_SOURCE)],  # type: ignore[arg-type]
        description="Documentation sources to index",
    )

    # Indexing settings
    chunk_size: int = Field(
        default=1000,
        description="Size of text chunks for indexing",
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between consecutive chunks",
    )
    max_depth: int = Field(
        default=3,
        description="Maximum crawl depth for documentation URLs",
    )
    embedding_model: str = Field(
        default="models/embedding-001",
        description="Google embedding model to use",
    )

    # Retrieval settings
    retriever_k: int = Field(
        default=6,
        description="Number of documents to retrieve",
    )
    max_rewrites: int = Field(
        default=2,
        description="Maximum query rewrites before fallback",
    )
    model_name: str = Field(
        default="gemini-2.5-flash",
        description="LLM model for grading and generation",
    )
    temperature: float = Field(
        default=0.3,
        description="Temperature for answer generation",
    )

    # Caching
    enable_llm_cache: bool = Field(
        default=True,
        description="Enable LLM response caching",
    )

    # Custom glossary
    glossary: dict[str, str] = Field(
        default_factory=dict,
        description="Domain-specific glossary for technical terms",
    )

    # Storage paths
    chroma_db_dir: Path = Field(
        default=Path("./chroma_db"),
        description="Directory for ChromaDB storage",
    )
    cert_cache_dir: Path = Field(
        default=Path.home() / ".cache" / "macsdk" / "certs",
        description="Directory for cached SSL certificates",
    )


def load_rag_config(
    yaml_config: dict[str, Any] | None = None,
    config_path: str | Path | None = None,
) -> RAGConfig:
    """Load RAG configuration from YAML or defaults.

    Args:
        yaml_config: Pre-loaded YAML config dict (optional).
        config_path: Path to config.yml file (optional).

    Returns:
        RAGConfig instance with merged configuration.
    """
    if yaml_config is None:
        yaml_config = load_config_from_yaml(config_path)

    rag_section = yaml_config.get("rag", {})

    # Handle sources specially - convert dicts to RAGSourceConfig
    if "sources" in rag_section and rag_section["sources"] is not None:
        rag_section["sources"] = [
            RAGSourceConfig(**src) if isinstance(src, dict) else src
            for src in rag_section["sources"]
        ]

    # Handle None values from YAML (empty keys like "glossary:")
    # Remove None values so Pydantic uses defaults
    rag_section = {k: v for k, v in rag_section.items() if v is not None}

    return RAGConfig(**rag_section)


@lru_cache(maxsize=1)
def get_rag_config() -> RAGConfig:
    """Get the cached RAG configuration.

    This function loads the configuration once and caches it.
    Use this for most RAG operations.

    Returns:
        Cached RAGConfig instance.
    """
    return load_rag_config()


def clear_rag_config_cache() -> None:
    """Clear the RAG configuration cache.

    Call this if you need to reload the configuration.
    """
    get_rag_config.cache_clear()
