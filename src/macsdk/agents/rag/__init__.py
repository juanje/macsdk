"""RAG (Retrieval-Augmented Generation) agent for MACSDK.

This module provides a RAG agent that can query documentation
and answer questions based on indexed content.

Features:
- Document indexing from multiple URLs
- ChromaDB vector store for semantic search
- Relevance grading and query transformation
- Configurable via config.yml
- SSL certificate support for internal URLs

Example:
    >>> from macsdk.agents.rag import RAGAgent
    >>> from macsdk.core import register_agent
    >>>
    >>> agent = RAGAgent()
    >>> register_agent(agent)
"""

from .agent import RAGAgent, clear_rag_cache
from .config import RAGConfig, get_rag_config
from .indexer import create_retriever
from .models import RAGResponse, RAGState

__all__ = [
    "RAGAgent",
    "RAGConfig",
    "RAGResponse",
    "RAGState",
    "clear_rag_cache",
    "create_retriever",
    "get_rag_config",
]
