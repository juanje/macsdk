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
def get_answer_model() -> ChatGoogleGenerativeAI:
    """Get the answer model for response generation.

    This model is used for generating natural language responses,
    agent reasoning, and all LLM-powered tasks in the framework.

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


# Module-level attribute for backwards compatibility
# Allows: from macsdk.core.llm import answer_model
def __getattr__(name: str) -> ChatGoogleGenerativeAI:
    """Module-level getattr for lazy loading of models.

    This enables importing the model as a module attribute:
        from macsdk.core.llm import answer_model

    The model is lazily initialized on first access.
    """
    if name == "answer_model":
        return get_answer_model()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
