"""Instruction templates for ToolInstructionsMiddleware.

This module contains the instruction text that is injected into agent
system prompts when specific tool sets are detected.
"""

from __future__ import annotations

# Individual tool set instructions
SKILLS_INSTRUCTIONS = """
## Skills System
Use skills to discover how to perform tasks correctly:
- list_skills(): Get available task instructions
- read_skill(name): Get detailed steps for a specific task

Always check skills before guessing how to use APIs or execute complex tasks.
"""

FACTS_INSTRUCTIONS = """
## Facts System
Use facts to get accurate contextual information:
- list_facts(): Get available information categories
- read_fact(name): Get specific details (names, policies, configurations)

Use facts for accurate names, identifiers, and business rules.
"""

# Combined instructions (used when both skills and facts are present)
KNOWLEDGE_SYSTEM_INSTRUCTIONS = """
## Knowledge System
You have access to skills (how-to instructions) and facts (contextual information):

**Skills** - Task instructions:
- list_skills() → read_skill(name) to learn how to do something

**Facts** - Contextual data:
- list_facts() → read_fact(name) to get accurate information

Check skills before complex tasks. Use facts for precise details.
"""
