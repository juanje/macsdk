"""Graph nodes for the RAG workflow.

This module provides the node functions for the LangGraph RAG workflow:
- retrieve_node: Retrieves documents from the vector store
- grade_node: Grades document relevance (batch processing)
- transform_node: Rewrites queries for better retrieval
- generate_node: Generates answers from relevant documents
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Literal, cast

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from macsdk.core.config import config as macsdk_config
from macsdk.core.utils import log_progress

from .glossary import get_glossary_text
from .models import RAGState
from .prompts import (
    FALLBACK_NO_DOCUMENTS_MSG,
    GENERATE_ANSWER_PROMPT,
    GRADE_DOCUMENTS_PROMPT,
    TRANSFORM_QUERY_PROMPT,
)

if TYPE_CHECKING:
    from langchain_core.vectorstores import VectorStoreRetriever

    from .config import RAGConfig

logger = logging.getLogger(__name__)


class DocumentGrade(BaseModel):
    """Grade for a single document."""

    index: int = Field(description="Index of the document (0-based)")
    score: Literal["yes", "no"] = Field(
        description="Relevance score: 'yes' if relevant, 'no' if not relevant"
    )


class BatchGradeDocuments(BaseModel):
    """Grades for multiple documents evaluated in batch."""

    grades: list[DocumentGrade] = Field(
        description="List of grades, one per document in the same order as input"
    )


def create_retrieve_node(
    retriever: "VectorStoreRetriever",
    config: "RAGConfig",
) -> Callable[[RAGState], RAGState]:
    """Create a retrieval node.

    Args:
        retriever: Vector store retriever.
        config: RAG configuration.

    Returns:
        Retrieve node function.
    """

    def retrieve_node(state: RAGState) -> RAGState:
        """Retrieve documents based on the question."""
        question = state["question"]
        log_progress("📚 Retrieving relevant documents...\n")
        logger.info(f"Retrieving documents for: {question}")

        documents = retriever.invoke(question)
        log_progress(f"📄 Retrieved {len(documents)} documents\n")
        logger.info(f"Retrieved {len(documents)} documents")

        return cast(RAGState, {"documents": [doc.page_content for doc in documents]})

    return retrieve_node


def create_grade_node(config: "RAGConfig") -> Callable[[RAGState], RAGState]:
    """Create a document grading node.

    Uses batch grading to evaluate all documents in a single LLM call,
    which is much more efficient than grading documents individually.

    Args:
        config: RAG configuration.

    Returns:
        Grade node function.
    """
    # LLM with structured output for batch grading
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=0.0,
        google_api_key=macsdk_config.google_api_key,
    )
    structured_llm = llm.with_structured_output(BatchGradeDocuments)

    glossary = get_glossary_text()
    system_prompt = GRADE_DOCUMENTS_PROMPT.format(glossary=glossary)

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "User question: {question}\n\nDocuments to grade:\n\n{documents}\n\n"
                "Grade each document for relevance to the question.",
            ),
        ]
    )

    retrieval_grader = grade_prompt | structured_llm

    def grade_node(state: RAGState) -> RAGState:
        """Grade retrieved documents for relevance using batch processing."""
        question = state["question"]
        documents = state["documents"]

        if not documents:
            log_progress("⚠️  No documents to grade\n")
            logger.info("No documents to grade")
            return cast(RAGState, {"relevant_docs": [], "documents": []})

        log_progress(f"🔍 Grading {len(documents)} documents for relevance...\n")
        logger.info(f"Batch grading {len(documents)} documents for relevance")

        # Format documents for batch grading
        formatted_docs = "\n\n".join(
            [f"Document {i}:\n{doc}" for i, doc in enumerate(documents)]
        )

        # Single LLM call to grade all documents
        try:
            batch_result = cast(
                BatchGradeDocuments,
                retrieval_grader.invoke(
                    {
                        "question": question,
                        "documents": formatted_docs,
                    }
                ),
            )

            # Filter documents based on grades
            filtered_docs = []
            for grade in batch_result.grades:
                if grade.index < len(documents):
                    if grade.score == "yes":
                        logger.info(f"✓ Document {grade.index} is relevant")
                        filtered_docs.append(documents[grade.index])
                    else:
                        logger.info(f"✗ Document {grade.index} is not relevant")
                else:
                    logger.warning(f"Invalid document index: {grade.index}")

            log_progress(f"✅ Found {len(filtered_docs)} relevant documents\n")
            logger.info(f"Filtered to {len(filtered_docs)} relevant documents")
            return cast(
                RAGState, {"relevant_docs": filtered_docs, "documents": filtered_docs}
            )

        except Exception as e:
            log_progress("⚠️  Grading error, using all documents\n")
            logger.error(f"Error in batch grading: {e}")
            logger.warning("Falling back to using all documents")
            return cast(RAGState, {"relevant_docs": documents, "documents": documents})

    return grade_node


def create_transform_node(config: "RAGConfig") -> Callable[[RAGState], RAGState]:
    """Create a query transformation node.

    Args:
        config: RAG configuration.

    Returns:
        Transform node function.
    """
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=0.0,
        google_api_key=macsdk_config.google_api_key,
    )

    glossary = get_glossary_text()
    system_prompt = TRANSFORM_QUERY_PROMPT.format(glossary=glossary)

    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "Here is the initial question:\n\n{question}\n\n"
                "Formulate an improved question.",
            ),
        ]
    )

    question_rewriter = rewrite_prompt | llm | StrOutputParser()

    def transform_node(state: RAGState) -> RAGState:
        """Transform the query to produce a better question."""
        question = state["question"]
        rewrite_count = state.get("rewrite_count", 0)

        log_progress("🔄 Optimizing query for better results...\n")
        logger.info("Transforming query for better retrieval")

        better_question = question_rewriter.invoke({"question": question})
        log_progress("✏️  Query rewritten\n")
        logger.info(f"Rewritten question: {better_question}")

        return cast(
            RAGState,
            {
                "question": better_question,
                "rewrite_count": rewrite_count + 1,
            },
        )

    return transform_node


def create_generate_node(config: "RAGConfig") -> Callable[[RAGState], RAGState]:
    """Create an answer generation node.

    Args:
        config: RAG configuration.

    Returns:
        Generate node function.
    """
    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=macsdk_config.google_api_key,
    )

    glossary = get_glossary_text()
    prompt_text = GENERATE_ANSWER_PROMPT.format(
        glossary=glossary, question="{question}", context="{context}"
    )
    prompt = ChatPromptTemplate.from_template(prompt_text)

    chain = prompt | llm | StrOutputParser()

    def generate_node(state: RAGState) -> RAGState:
        """Generate answer using retrieved documents."""
        question = state["question"]
        documents = state["documents"]

        log_progress("💭 Generating answer from documents...\n")
        logger.info("Generating answer")

        # If no documents, generate a "no information found" response
        if not documents:
            log_progress("⚠️  No relevant documents found\n")
            logger.warning("Generating answer without relevant documents")
            return cast(
                RAGState, {"answer": FALLBACK_NO_DOCUMENTS_MSG, "rewrite_count": 0}
            )

        # Format documents as context
        context = "\n\n".join(documents)

        answer = chain.invoke({"question": question, "context": context})
        log_progress("✅ Answer generated successfully\n")
        logger.info("Answer generated")

        # Reset rewrite counter for next question
        return cast(RAGState, {"answer": answer, "rewrite_count": 0})

    return generate_node


def create_decide_to_generate(
    config: "RAGConfig",
) -> Callable[[RAGState], Literal["transform", "generate"]]:
    """Create a decision function for whether to generate or transform.

    Args:
        config: RAG configuration.

    Returns:
        Decision function.
    """

    def decide_to_generate(state: RAGState) -> Literal["transform", "generate"]:
        """Determine whether to generate an answer or re-generate the question.

        Args:
            state: Current graph state.

        Returns:
            "transform" if no relevant documents and rewrites available,
            "generate" otherwise.
        """
        filtered_documents = state["documents"]
        rewrite_count = state.get("rewrite_count", 0)
        max_rewrites = config.max_rewrites

        if not filtered_documents:
            if rewrite_count >= max_rewrites:
                logger.warning(
                    f"No relevant documents found after {rewrite_count} rewrites, "
                    "generating fallback answer"
                )
                return "generate"
            else:
                logger.info(
                    f"No relevant documents found (rewrite {rewrite_count + 1}/"
                    f"{max_rewrites}), transforming query"
                )
                return "transform"
        else:
            logger.info("Relevant documents found, generating answer")
            return "generate"

    return decide_to_generate
