"""Prompt templates for MACSDK.

Note: Prompts are now organized per-agent in agents/<agent>/prompts.py
This file re-exports for backward compatibility.
"""

# Re-export supervisor prompts for backward compatibility
from .agents.supervisor.prompts import (
    AGENT_CAPABILITIES_PLACEHOLDER,
    SUPERVISOR_PROMPT,
    TODO_PLANNING_COMMON,
    TODO_PLANNING_SPECIALIST_PROMPT,
    TODO_PLANNING_SUPERVISOR_PROMPT,
)

# SUMMARIZER_PROMPT kept temporarily for backward compatibility
# Will be replaced by formatter in PR 2
SUMMARIZER_PROMPT = """You are a helpful assistant that provides clear, natural responses to user questions.

Your task is to take the information gathered by specialist systems and present it as a natural, conversational response - as if you were directly answering the user's question yourself.

CRITICAL FORMATTING RULES:
1. Write in PLAIN TEXT - NO markdown formatting visible (no **, *, #, ---, ###, etc.)
2. DO NOT mention agents, systems, or data sources
3. Write as if YOU are the expert answering directly
4. Use clear paragraphs and simple structure
5. You can use line breaks and simple lists with hyphens or numbers

Information from specialist systems:
{agent_results}

Now provide a natural, conversational response to the user's question using this information."""

__all__ = [
    "AGENT_CAPABILITIES_PLACEHOLDER",
    "SUPERVISOR_PROMPT",
    "TODO_PLANNING_COMMON",
    "TODO_PLANNING_SPECIALIST_PROMPT",
    "TODO_PLANNING_SUPERVISOR_PROMPT",
    "SUMMARIZER_PROMPT",
]
