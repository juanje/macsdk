"""MACSDK - Multi-Agent Chatbot SDK.

A complete SDK for building customizable multi-agent chatbots.
Provides core libraries, a framework for agent orchestration,
CLI tools for scaffolding, and reusable utilities.

Quick Start:
    >>> from macsdk import SpecialistAgent, register_agent, create_chatbot_graph
    >>>
    >>> # Create your agent
    >>> class MyAgent:
    ...     name = "my_agent"
    ...     capabilities = "Handles my domain"
    ...     async def run(self, query, context=None):
    ...         return {"response": "Hello!", "agent_name": self.name}
    ...     def as_tool(self):
    ...         # Return LangChain tool wrapper
    ...         ...
    >>>
    >>> # Register and create graph
    >>> register_agent(MyAgent())
    >>> graph = create_chatbot_graph()

For CLI scaffolding:
    $ macsdk new chatbot my-chatbot
    $ macsdk new agent my-agent
    $ macsdk add-agent . --package my-agent
"""

# Import version info from single source of truth
from ._version import __author__, __email__, __version__

# Re-export core components for convenience
from .core import (
    CONFIG_FILE_ENV_VAR,
    DEFAULT_CONFIG_FILE,
    STREAM_WRITER_KEY,
    # Registry
    AgentRegistry,
    # Models
    BaseAgentResponse,
    # State
    ChatbotState,
    # Config
    ConfigurationError,
    MACSDKConfig,
    # Protocol
    SpecialistAgent,
    config,
    # Graph
    create_chatbot_graph,
    create_config,
    create_config_with_writer,
    create_web_chatbot_graph,
    get_all_agent_tools,
    get_all_capabilities,
    # LLM (use these for lazy initialization)
    get_answer_model,
    get_registry,
    load_config_from_yaml,
    # Utils
    log_progress,
    register_agent,
    run_agent_with_tools,
    # Supervisor
    supervisor_agent_node,
    validate_config,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Protocol
    "SpecialistAgent",
    # Registry
    "AgentRegistry",
    "get_registry",
    "register_agent",
    "get_all_capabilities",
    "get_all_agent_tools",
    # State
    "ChatbotState",
    # Graph
    "create_chatbot_graph",
    "create_web_chatbot_graph",
    # Supervisor
    "supervisor_agent_node",
    # Config
    "MACSDKConfig",
    "config",
    "create_config",
    "load_config_from_yaml",
    "validate_config",
    "ConfigurationError",
    "DEFAULT_CONFIG_FILE",
    "CONFIG_FILE_ENV_VAR",
    # LLM (use these for lazy initialization)
    "get_answer_model",
    # Models
    "BaseAgentResponse",
    # Utils
    "log_progress",
    "run_agent_with_tools",
    "create_config_with_writer",
    "STREAM_WRITER_KEY",
]
