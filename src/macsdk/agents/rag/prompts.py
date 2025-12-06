"""Prompts for the RAG agent workflow stages."""

from __future__ import annotations

# Grade Documents Prompt
GRADE_DOCUMENTS_PROMPT = """You are a grader assessing relevance of retrieved documents to a user question.
For each document, determine if it contains keyword(s) or semantic meaning related to the question.
Grade each document as 'yes' (relevant) or 'no' (not relevant).

{glossary}

IMPORTANT:
- Use the glossary above to correctly interpret technical terms and acronyms
- You must grade ALL documents in the order they are presented
- Return one grade per document, maintaining the same order"""


# Transform Query Prompt
TRANSFORM_QUERY_PROMPT = """You are a question re-writer that converts an input question to a better version
that is optimized for vectorstore retrieval. Look at the input and try to reason about the
underlying semantic intent / meaning.

{glossary}

CRITICAL INSTRUCTIONS:
1. PRESERVE all technical terms and acronyms EXACTLY as written (use the glossary above for correct meanings)
2. DO NOT translate technical terms to generic meanings - refer to the glossary for correct interpretations
3. DO NOT add unrelated domain context unless explicitly in the question
4. Focus on rephrasing for clarity while keeping the technical vocabulary intact
5. Keep the rewrite concise - one or two sentences maximum
6. Respond in the SAME LANGUAGE as the input question"""


# Generate Answer Prompt
GENERATE_ANSWER_PROMPT = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.

Provide a comprehensive but focused answer. Include all relevant details, examples, and explanations
needed to fully address the question. Be thorough when necessary, but avoid unnecessary repetition
or unrelated information.

{glossary}

IMPORTANT:
- Use the glossary above to correctly interpret technical terms and acronyms in both the question and context
- Always respond in the SAME LANGUAGE as the question
- If the question is in Spanish, answer in Spanish
- If the question is in English, answer in English
- Maintain the language consistency throughout your response

Question: {question}

Context: {context}

Answer:"""


# Fallback Message
FALLBACK_NO_DOCUMENTS_MSG = (
    "I couldn't find relevant information in the documentation to answer your question. "
    "This could mean:\n"
    "1. The information might not be in the indexed documentation\n"
    "2. Try rephrasing your question with different terms\n"
    "3. Check if you're using the correct technical terms or acronyms"
)
