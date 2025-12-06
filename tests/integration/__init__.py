"""Integration tests for MACSDK.

These tests verify end-to-end functionality by:
1. Generating real projects (chatbot and agent)
2. Installing dependencies
3. Running generated tests
4. Testing agent registration and chatbot integration

Run with: uv run pytest tests/integration/ -v

Note: These tests are slower than unit tests as they create
actual project directories and run subprocesses.
"""
