"""LLM configuration and initialization for MACSDK.

This module provides pre-configured LLM instances for use
throughout the framework. Models are lazily initialized to
allow for early configuration validation.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from .config import config


@lru_cache(maxsize=1)
def get_classifier_model() -> ChatGoogleGenerativeAI:
    """Get the classifier model for routing and extraction tasks.

    This model is optimized for classification, routing decisions,
    and structured data extraction.

    Returns:
        A configured ChatGoogleGenerativeAI instance.

    Raises:
        ConfigurationError: If GOOGLE_API_KEY is not configured.
    """
    return ChatGoogleGenerativeAI(
        model=config.classifier_model,
        temperature=config.classifier_temperature,
        google_api_key=config.get_api_key(),
        model_kwargs={"reasoning_effort": config.classifier_reasoning_effort},
    )


@lru_cache(maxsize=1)
def get_answer_model() -> ChatGoogleGenerativeAI:
    """Get the answer model for response generation.

    This model is optimized for generating natural language
    responses to user queries.

    Returns:
        A configured ChatGoogleGenerativeAI instance.

    Raises:
        ConfigurationError: If GOOGLE_API_KEY is not configured.
    """
    return ChatGoogleGenerativeAI(
        model=config.llm_model,
        temperature=config.llm_temperature,
        google_api_key=config.get_api_key(),
        model_kwargs={"reasoning_effort": config.llm_reasoning_effort},
    )


# Backwards compatibility - lazy properties
# These will raise ConfigurationError when accessed if API key is missing
class _LazyModelProxy:
    """Proxy class for lazy model initialization with backwards compatibility."""

    @property
    def classifier_model(self) -> ChatGoogleGenerativeAI:
        """Get classifier model (lazy initialization)."""
        return get_classifier_model()

    @property
    def answer_model(self) -> ChatGoogleGenerativeAI:
        """Get answer model (lazy initialization)."""
        return get_answer_model()


_proxy = _LazyModelProxy()

# Expose as module-level for backwards compatibility
# Access will trigger validation and potential ConfigurationError


def __getattr__(name: str) -> ChatGoogleGenerativeAI:
    """Module-level getattr for lazy loading of models."""
    if name == "classifier_model":
        return _proxy.classifier_model
    elif name == "answer_model":
        return _proxy.answer_model
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
