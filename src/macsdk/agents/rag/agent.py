"""RAG Agent implementation for MACSDK.

This module provides the RAGAgent class that implements the SpecialistAgent
protocol, enabling integration with the MACSDK supervisor and chatbot system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from macsdk.core.utils import log_progress

from .cache import setup_llm_cache
from .config import RAGConfig, get_rag_config
from .graph import create_initial_state, create_rag_graph
from .indexer import create_retriever
from .models import RAGResponse

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool
    from langchain_core.vectorstores import VectorStoreRetriever
    from langgraph.graph.graph import CompiledGraph

logger = logging.getLogger(__name__)

# Agent capabilities description
CAPABILITIES = (
    "Answers questions based on indexed documentation. "
    "Uses RAG (Retrieval-Augmented Generation) with vector store retrieval, "
    "document relevance grading, query transformation, and answer generation. "
    "Configured via config.yml with customizable documentation sources."
)


# Cached instances (module-level to avoid hashability issues with lru_cache)
_cached_retriever: "VectorStoreRetriever | None" = None
_cached_workflow: "CompiledGraph | None" = None


def _create_rag_retriever() -> "VectorStoreRetriever":
    """Create or load the vector store retriever with module-level cache.

    Returns:
        Cached VectorStoreRetriever instance.
    """
    global _cached_retriever
    if _cached_retriever is None:
        config = get_rag_config()
        logger.info("Creating RAG retriever (cached)")
        _cached_retriever = create_retriever(config=config, force_reindex=False)
    return _cached_retriever


def _create_rag_workflow() -> "CompiledGraph":
    """Create the LangGraph RAG workflow with module-level cache.

    Returns:
        Cached compiled graph instance.
    """
    global _cached_workflow
    if _cached_workflow is None:
        config = get_rag_config()
        logger.info("Creating RAG workflow (cached)")
        retriever = _create_rag_retriever()
        _cached_workflow = create_rag_graph(retriever, config)
    return _cached_workflow


def clear_rag_cache() -> None:
    """Clear the RAG retriever and workflow cache.

    Call this if you need to reload the RAG configuration.
    """
    global _cached_retriever, _cached_workflow
    _cached_retriever = None
    _cached_workflow = None
    logger.info("RAG cache cleared")


def _setup_rag_agent(config: RAGConfig | None = None) -> None:
    """Set up the RAG agent with caching and indexing.

    Args:
        config: Optional RAG configuration.
    """
    if config is None:
        config = get_rag_config()
    setup_llm_cache(enable=config.enable_llm_cache)
    logger.info("RAG agent setup complete")


async def run_rag_agent(
    query: str,
    context: dict | None = None,
    config: RunnableConfig | None = None,
    filter_tags: list[str] | None = None,
) -> dict:
    """Run the RAG agent with LangGraph workflow.

    This function processes queries through the RAG pipeline:
    1. Document retrieval from vector store
    2. Batch relevance grading
    3. Query transformation if needed
    4. Answer generation with relevant documents

    Args:
        query: User's question.
        context: Optional context (not used in current implementation).
        config: Optional LangGraph config for streaming.
        filter_tags: Optional tags to filter documents by.

    Returns:
        Dictionary with structured response data.
    """
    rag_config = get_rag_config()

    try:
        # Emit progress message
        log_progress("[rag_agent] Processing query...\n", config)

        # Set up agent if not already done
        _setup_rag_agent(rag_config)

        # Get the workflow (uses cached config)
        workflow = _create_rag_workflow()

        # Create initial state
        initial_state = create_initial_state(question=query)

        logger.info(f"Processing query with RAG workflow: {query}")

        # Run the LangGraph workflow with streaming support
        final_state: dict = dict(initial_state)
        async for event in workflow.astream(
            initial_state, config=config, stream_mode=["updates", "custom"]
        ):
            if isinstance(event, tuple) and len(event) == 2:
                stream_type, data = event
                if stream_type == "updates":
                    # Update state from node updates
                    for node_name, node_state in data.items():
                        final_state.update(node_state)
                elif stream_type == "custom":
                    # Re-emit custom progress messages with config for proper streaming
                    if isinstance(data, str):
                        log_progress(data, config)
            elif isinstance(event, dict):
                final_state = event

        # Extract information from the workflow result
        answer = final_state.get("answer", "")
        documents = final_state.get("documents", [])
        relevant_docs = final_state.get("relevant_docs", [])
        rewrite_count = final_state.get("rewrite_count", 0)
        sources = final_state.get("sources", [])

        # Create response
        response = RAGResponse(
            sources_found=bool(relevant_docs),
            response_text=answer,
            retrieved_documents=documents[:5] if documents else None,
            relevant_documents=relevant_docs[:5] if relevant_docs else None,
            sources=sources if sources else None,
            query_rewritten=rewrite_count > 0,
            rewrite_count=rewrite_count if rewrite_count > 0 else None,
        )

        logger.info(f"RAG workflow completed. Sources found: {response.sources_found}")

        # Build result dict following standard agent convention
        result_dict = {
            "response": response.response_text,
            "agent_name": "rag_agent",
            "tools_used": [
                "vector_store_retrieval",
                "document_grading",
                "answer_generation",
            ],
            "success": True,
        }

        # Add additional RAG-specific fields
        for field_name, field_value in response.model_dump().items():
            if field_name not in ["response_text", "tools_used"]:
                result_dict[field_name] = field_value

        return result_dict

    except Exception as e:
        logger.error(f"Error in RAG agent: {e}")

        error_message = (
            f"I encountered an error while processing your question: {str(e)}. "
            "Please try rephrasing your question or contact support."
        )

        return {
            "response": error_message,
            "agent_name": "rag_agent",
            "tools_used": [],
            "success": False,
            "error": str(e),
            "sources_found": False,
        }


class RAGAgent:
    """RAG Agent that implements the SpecialistAgent protocol.

    This class provides the interface that MACSDK expects:
    - name: Unique identifier for the agent
    - capabilities: Description of what the agent can do
    - run(): Execute the agent
    - as_tool(): Return the agent as a callable tool

    Example:
        >>> from macsdk.agents.rag import RAGAgent
        >>> from macsdk.core import register_agent
        >>>
        >>> agent = RAGAgent()
        >>> register_agent(agent)
    """

    name: str = "rag_agent"
    capabilities: str = CAPABILITIES

    def __init__(self, config: RAGConfig | None = None) -> None:
        """Initialize the RAG agent.

        Args:
            config: Optional RAG configuration. If None, loads from config.yml.
        """
        self._config = config

    @property
    def config(self) -> RAGConfig:
        """Get the RAG configuration."""
        if self._config is None:
            self._config = get_rag_config()
        return self._config

    async def run(
        self,
        query: str,
        context: dict | None = None,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Execute the agent.

        Args:
            query: User query to process.
            context: Optional context from previous interactions.
            config: Optional runnable configuration.

        Returns:
            Agent response dictionary.
        """
        return await run_rag_agent(query, context, config)

    def as_tool(self) -> "BaseTool":
        """Return this agent as a LangChain tool.

        This allows the supervisor to call this agent as a tool,
        enabling dynamic agent orchestration.

        Returns:
            A LangChain tool wrapping this agent.
        """
        agent_instance = self

        @tool
        async def invoke_rag_agent(
            query: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
        ) -> str:
            """Query the documentation knowledge base.

            Use this tool to find information from indexed documentation.
            Ask questions about the configured documentation sources.

            Args:
                query: The question to answer from the documentation.
                config: Runnable configuration (injected).

            Returns:
                The answer based on the documentation.
            """
            result = await agent_instance.run(query, config=config)
            return str(result["response"])

        return invoke_rag_agent
