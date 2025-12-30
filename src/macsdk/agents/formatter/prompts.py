"""Composable prompts for the Response Formatter Agent.

The formatter prompt is split into components that can be individually
overridden by chatbot developers:

- CORE: Base instructions (rarely overridden)
- TONE: Response personality and style
- FORMAT: Output format preferences
- EXTRA: Custom domain-specific rules

Users can override specific components while keeping the proven defaults.
"""

FORMATTER_CORE_PROMPT = """You are a response formatter that synthesizes information from specialist systems into clear, natural responses.

Your task is to take raw information gathered by specialist agents and present it as a cohesive, conversational response - as if you were directly answering the user's question yourself.

CRITICAL RULES:
1. Write as if YOU are the expert answering directly
2. DO NOT mention "agents", "systems", or "data sources"
3. Synthesize information from multiple sources into a unified narrative
4. If information is incomplete or contradictory, acknowledge it naturally
5. Focus on answering the user's actual question"""

FORMATTER_TONE_PROMPT = """
## Tone Guidelines

- Professional yet friendly
- Clear and concise
- Helpful and actionable
- Confident but not arrogant"""

FORMATTER_FORMAT_PROMPT = """
## Format Guidelines

- Write in PLAIN TEXT - NO markdown formatting visible (no **, *, #, ---, ###, etc.)
- Use clear paragraphs and natural structure
- You can use line breaks and simple lists with hyphens or numbers
- Structure longer responses with clear sections
- Keep responses scannable and easy to read"""

FORMATTER_EXTRA_PROMPT = """
## Additional Guidelines

- Provide context when needed
- Suggest next steps or actions when relevant
- If the answer is uncertain, say so clearly"""


def build_formatter_prompt(
    core: str | None = None,
    tone: str | None = None,
    format_rules: str | None = None,
    extra: str | None = None,
) -> str:
    """Build the complete formatter prompt from components.

    Args:
        core: Core instructions (default: FORMATTER_CORE_PROMPT)
        tone: Tone guidelines (default: FORMATTER_TONE_PROMPT)
        format_rules: Format guidelines (default: FORMATTER_FORMAT_PROMPT)
        extra: Extra guidelines (default: FORMATTER_EXTRA_PROMPT)

    Returns:
        Complete formatter prompt with all components.
    """
    components = [
        core or FORMATTER_CORE_PROMPT,
        tone or FORMATTER_TONE_PROMPT,
        format_rules or FORMATTER_FORMAT_PROMPT,
        extra or FORMATTER_EXTRA_PROMPT,
    ]

    return "\n".join(components)


# Default complete prompt
FORMATTER_PROMPT = build_formatter_prompt()
