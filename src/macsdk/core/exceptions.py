"""Custom exceptions for MACSDK.

This module defines custom exception classes used throughout the framework.
"""

from __future__ import annotations


class SpecialistTimeoutError(TimeoutError):
    """Raised when a specialist agent exceeds its execution timeout.

    This exception is raised by run_agent_with_tools() when a specialist
    agent fails to complete within the configured specialist_timeout.

    Attributes:
        agent_name: Name of the agent that timed out.
        timeout: The timeout value in seconds that was exceeded.
    """

    def __init__(self, agent_name: str, timeout: float) -> None:
        """Initialize the exception.

        Args:
            agent_name: Name of the agent that timed out.
            timeout: The timeout value in seconds.
        """
        self.agent_name = agent_name
        self.timeout = timeout
        super().__init__(
            f"Agent '{agent_name}' timed out after {timeout} seconds. "
            "The LLM may be unresponsive."
        )
