# Response Formatter Reference

The Response Formatter Agent synthesizes raw agent results into polished, user-friendly responses.

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Supervisor │ -> │  Formatter  │ -> │    User     │
│             │    │             │    │             │
│ Raw Results │    │ Synthesize  │    │  Polished   │
│ from Agents │    │  + Format   │    │  Response   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Workflow

1. **Supervisor** orchestrates specialist agents and collects raw results
2. **Formatter** receives raw results via `agent_results` state field
3. **Formatter** applies tone, format, and synthesis rules
4. **User** sees the final polished response

## Composable Prompts

The formatter uses composable prompts that can be individually customized:

### FORMATTER_CORE_PROMPT

Base instructions for the formatter (rarely needs customization):

```python
from macsdk.agents.formatter import FORMATTER_CORE_PROMPT

print(FORMATTER_CORE_PROMPT)
```

Defines the formatter's core task: synthesize information and present it naturally.

### FORMATTER_TONE_PROMPT

Controls response personality:

```python
from macsdk.prompts import build_formatter_prompt

custom_formatter = build_formatter_prompt(
    tone="""
## Tone Guidelines

- Professional and technical
- Direct and efficient  
- Use industry-standard terminology
- Avoid casual language
"""
)
```

### FORMATTER_FORMAT_PROMPT

Controls output structure:

```python
from macsdk.prompts import build_formatter_prompt

custom_formatter = build_formatter_prompt(
    format_rules="""
## Format Guidelines

- Use plain text (no markdown)
- Always provide a summary first
- Use bullet points for lists
- Keep responses concise (< 300 words)
"""
)
```

### FORMATTER_EXTRA_PROMPT

Domain-specific or custom rules:

```python
from macsdk.prompts import build_formatter_prompt

custom_formatter = build_formatter_prompt(
    extra="""
## Additional Guidelines

- Always cite sources when available
- Flag uncertain information
- Provide actionable next steps
- Include relevant timestamps
"""
)
```

## Using in Your Chatbot

In your chatbot's `prompts.py`:

```python
from macsdk.prompts import build_formatter_prompt

# Option 1: Override specific components
FORMATTER_PROMPT = build_formatter_prompt(
    tone="## Tone\n- Friendly and encouraging\n- Use simple language",
    format_rules="## Format\n- Use numbered lists\n- Keep responses brief"
)

# Option 2: Use defaults (recommended for most cases)
# No changes needed - the default formatter works well
```

## Configuration

The formatter doesn't require separate configuration. It uses the same LLM settings as other components:

```yaml
# config.yml
llm_model: gemini-2.5-flash
llm_temperature: 0.3  # Used by formatter
```

## Best Practices

1. **Start with defaults**: The built-in prompts are well-tested
2. **Override selectively**: Only customize the parts you need
3. **Test thoroughly**: Changes affect all responses
4. **Keep it simple**: Overly complex rules can confuse the LLM
5. **Be specific**: Vague instructions lead to inconsistent output

## Error Handling

The formatter includes graceful fallbacks:

- **Empty results**: Returns "I don't have enough information" message
- **LLM failure**: Returns raw agent results as fallback
- **Cancellation**: Properly handles async shutdown signals

## Security

The formatter agent has a minimal security footprint by design:

- **No input sanitization needed**: User input and agent results are passed directly without escaping
  - The formatter has no tools (cannot execute actions)
  - No access to sensitive data or external systems
  - Only formats text for display
  - Worst case: poorly formatted output (cosmetic issue only)
- **History consistency**: Formatted responses are always added to conversation history to prevent context loss
- **Error isolation**: Errors in formatting don't break the entire chatbot - raw results are returned as fallback

## Examples

### Example 1: Multilingual Formatter

```python
# prompts.py
from macsdk.prompts import build_formatter_prompt

FORMATTER_PROMPT = build_formatter_prompt(
    tone="""
## Tone Guidelines

- Always respond in Spanish
- Use formal language (usted)
- Be professional and helpful
"""
)
```

### Example 2: Technical Documentation Bot

```python
# prompts.py
from macsdk.prompts import build_formatter_prompt

FORMATTER_PROMPT = build_formatter_prompt(
    format_rules="""
## Format Guidelines

- Use markdown code blocks for commands and code
- Include section headings for long responses
- Always provide examples
- Link to official documentation when relevant
""",
    extra="""
## Additional Guidelines

- Cite the documentation source
- Mention the version if applicable
- Warn about deprecated features
"""
)
```

### Example 3: Customer Support Bot

```python
# prompts.py
from macsdk.prompts import build_formatter_prompt

FORMATTER_PROMPT = build_formatter_prompt(
    tone="""
## Tone Guidelines

- Empathetic and understanding
- Patient and reassuring
- Use simple, non-technical language
- Always offer to help further
""",
    extra="""
## Additional Guidelines

- Always end with "Is there anything else I can help you with?"
- If the issue is unresolved, offer to escalate
- Thank the user for their patience
"""
)
```

## Advanced: Full Prompt Override

If you need complete control, override the entire prompt:

```python
# prompts.py
from macsdk.prompts import build_formatter_prompt

FORMATTER_PROMPT = build_formatter_prompt(
    core="""Your completely custom core instructions...""",
    tone="""Your custom tone...""",
    format_rules="""Your custom format...""",
    extra="""Your custom extras..."""
)
```

**Warning**: This replaces all default behavior. Only do this if you have specific requirements the defaults don't meet.

## See Also

- [Creating Chatbots Guide](../guides/creating-chatbots.md#customizing-response-format)
- [Configuration Reference](configuration.md)
- [Protocol Reference](protocol.md)

