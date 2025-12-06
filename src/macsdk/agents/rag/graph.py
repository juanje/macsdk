"""LangGraph workflow for the RAG agent.

This module defines the RAG workflow graph that processes questions
through a retrieve-grade-transform-generate pipeline.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from .models import RAGState
from .nodes import (
    create_decide_to_generate,
    create_generate_node,
    create_grade_node,
    create_retrieve_node,
    create_transform_node,
)

if TYPE_CHECKING:
    from langchain_core.vectorstores import VectorStoreRetriever
    from langgraph.graph.graph import CompiledGraph

    from .config import RAGConfig

logger = logging.getLogger(__name__)


def create_rag_graph(
    retriever: "VectorStoreRetriever",
    config: "RAGConfig",
) -> "CompiledGraph":
    """Create the RAG workflow graph for processing a single question.

    The graph workflow is as follows:
    1. START -> retrieve: Get documents from vectorstore
    2. retrieve -> grade: Check document relevance
    3. If documents are relevant: generate answer and END
    4. If documents are not relevant: transform query and retry retrieve
    5. After max rewrites: generate fallback answer and END

    Args:
        retriever: Vector store retriever for document search.
        config: RAG configuration.

    Returns:
        Compiled LangGraph workflow.

    Example:
        >>> from macsdk.agents.rag import get_rag_config
        >>> from macsdk.agents.rag.indexer import create_retriever
        >>>
        >>> config = get_rag_config()
        >>> retriever = create_retriever(config=config)
        >>> graph = create_rag_graph(retriever, config)
        >>> state = create_initial_state("What is LangChain?")
        >>> result = graph.invoke(state)
        >>> print(result["answer"])
    """
    logger.info("Building RAG graph")

    # Create workflow
    workflow: StateGraph[RAGState] = StateGraph(RAGState)

    # Create nodes with dependencies
    retrieve_node = create_retrieve_node(retriever, config)
    grade_node = create_grade_node(config)
    transform_node = create_transform_node(config)
    generate_node = create_generate_node(config)
    decide_to_generate = create_decide_to_generate(config)

    # Add nodes
    workflow.add_node("retrieve", retrieve_node)  # type: ignore[call-overload]
    workflow.add_node("grade", grade_node)  # type: ignore[call-overload]
    workflow.add_node("transform", transform_node)  # type: ignore[call-overload]
    workflow.add_node("generate", generate_node)  # type: ignore[call-overload]

    # Build graph edges
    # START -> retrieve
    workflow.add_edge(START, "retrieve")

    # retrieve -> grade (always)
    workflow.add_edge("retrieve", "grade")

    # grade -> conditional: check if documents are relevant
    workflow.add_conditional_edges(
        "grade",
        decide_to_generate,
        {
            "transform": "transform",
            "generate": "generate",
        },
    )

    # transform -> retrieve (retry with better question)
    workflow.add_edge("transform", "retrieve")

    # generate -> END (finish processing this question)
    workflow.add_edge("generate", END)

    # Compile
    logger.info("Graph compiled successfully")
    return workflow.compile()


def create_initial_state(question: str = "") -> RAGState:
    """Create the initial state for processing a question.

    Args:
        question: The user's question to process.

    Returns:
        Initial RAGState with the question.
    """
    return {
        "messages": [],
        "question": question,
        "documents": [],
        "answer": "",
        "rewrite_count": 0,
        "relevant_docs": [],
        "sources": [],
    }
