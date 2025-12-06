"""Domain-specific glossary for technical terms and acronyms.

This glossary helps the LLM understand the correct context for technical terms
and acronyms used in the documentation, preventing misinterpretation.

The glossary is loaded from config.yml and can be extended per-chatbot.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from .config import get_rag_config

logger = logging.getLogger(__name__)


# Default glossary context (empty by default)
DEFAULT_GLOSSARY_CONTEXT = ""


def format_glossary(glossary: dict[str, str]) -> str:
    """Format a glossary dictionary as text for prompts.

    Args:
        glossary: Dictionary mapping terms to definitions.

    Returns:
        Formatted string with glossary terms.
    """
    if not glossary:
        return ""

    terms_text = "\n".join(
        [f"- {term}: {definition}" for term, definition in glossary.items()]
    )

    return f"""
DOMAIN GLOSSARY (use these definitions):
{terms_text}
"""


@lru_cache(maxsize=1)
def get_glossary_text() -> str:
    """Get formatted glossary text for inclusion in prompts.

    This function loads the glossary from config.yml and formats it
    for inclusion in LLM prompts.

    Returns:
        Formatted string with glossary terms and context, or empty string.
    """
    config = get_rag_config()
    return format_glossary(config.glossary)


def clear_glossary_cache() -> None:
    """Clear the glossary cache.

    Call this if you need to reload the glossary from config.
    """
    get_glossary_text.cache_clear()
