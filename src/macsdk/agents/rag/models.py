"""Models for the RAG agent.

This module defines the state schema and response models
for the RAG workflow.
"""

from __future__ import annotations

from typing import Annotated, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import Field
from typing_extensions import TypedDict

from macsdk.core.models import BaseAgentResponse


class RAGState(TypedDict):
    """State for the RAG workflow.

    Attributes:
        messages: Conversation messages with add_messages reducer.
        question: Current user question.
        documents: Retrieved documents from vector store.
        answer: Generated answer.
        rewrite_count: Number of times the query has been rewritten.
        relevant_docs: Documents that passed relevance grading.
        sources: Source URLs/references for citations.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    documents: list[str]
    answer: str
    rewrite_count: int
    relevant_docs: list[str]
    sources: list[str]


class RAGResponse(BaseAgentResponse):
    """Enhanced response model for the RAG agent.

    This model extends BaseAgentResponse with RAG-specific fields
    for detailed information about the retrieval process.
    """

    sources_found: bool = Field(
        description="Whether relevant information was found in the knowledge base",
    )
    response_text: str = Field(
        description="Human-readable response based on the knowledge base",
    )
    retrieved_documents: Optional[list[str]] = Field(
        None,
        description="Documents retrieved from vector store",
    )
    relevant_documents: Optional[list[str]] = Field(
        None,
        description="Documents that passed relevance grading",
    )
    sources: Optional[list[str]] = Field(
        None,
        description="Source URLs or references for citations",
    )
    query_rewritten: Optional[bool] = Field(
        None,
        description="Whether the original query was rewritten for better retrieval",
    )
    rewrite_count: Optional[int] = Field(
        None,
        description="Number of times the query was rewritten",
    )
