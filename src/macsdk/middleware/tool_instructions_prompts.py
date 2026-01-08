"""Instruction templates for ToolInstructionsMiddleware.

This module contains the instruction text that is injected into agent
system prompts when specific tool sets are detected.
"""

from __future__ import annotations

# Individual tool set instructions
SKILLS_INSTRUCTIONS = """
## Skills System
You have access to step-by-step task instructions (skills).

**Skills**: Task instructions showing how to perform specific operations.
Use `read_skill(path)` to get detailed steps for a specific task.

The available skills are listed below. Always check skills before guessing
how to use APIs or execute complex tasks.
"""

FACTS_INSTRUCTIONS = """
## Facts System
You have access to contextual information and reference data (facts).

**Facts**: Accurate background information, configurations, and policies.
Use `read_fact(path)` to get specific details.

The available facts are listed below. Use facts for accurate names,
identifiers, and business rules.
"""

# Combined instructions (used when both skills and facts are present)
KNOWLEDGE_SYSTEM_INSTRUCTIONS = """
## Knowledge System
You have access to skills (how-to instructions) and facts (contextual
information).

**Skills**: Step-by-step task instructions. Use `read_skill(path)` to get
the content.

**Facts**: Contextual data and reference information. Use `read_fact(path)`
to get details.

The available skills and facts are listed below. Check skills before complex
tasks. Use facts for precise details.
"""
