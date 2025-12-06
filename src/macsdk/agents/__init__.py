"""Agents module for MACSDK.

This module provides pre-built agents that can be used in chatbots:

- RAGAgent: Retrieval-Augmented Generation agent for documentation querying

Example:
    >>> from macsdk.agents import RAGAgent
    >>> from macsdk.core import register_agent
    >>>
    >>> agent = RAGAgent()
    >>> register_agent(agent)
"""

from .rag import RAGAgent

__all__ = [
    "RAGAgent",
]
