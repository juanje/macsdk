"""Core module for MACSDK framework.

This module provides the essential building blocks for creating
multi-agent chatbots:

- SpecialistAgent: Protocol that agents must implement
- AgentRegistry: Registry for managing agents
- ChatbotState: State schema for chatbot graphs
- create_chatbot_graph: Function to create the chatbot workflow
- supervisor_agent_node: The main supervisor node
- Utility functions for logging and agent execution

Example:
    >>> from macsdk.core import SpecialistAgent, register_agent, create_chatbot_graph
    >>>
    >>> class MyAgent:
    ...     name = "my_agent"
    ...     capabilities = "Does something useful"
    ...     async def run(self, query, context=None):
    ...         return {"response": "Hello!", "agent_name": self.name}
    ...     def as_tool(self):
    ...         ...
    >>>
    >>> register_agent(MyAgent())
    >>> graph = create_chatbot_graph()
"""

from ..agents.supervisor import supervisor_agent_node
from .api_registry import (
    APIServiceConfig,
    clear_api_services,
    get_api_service,
    list_api_services,
    load_api_services_from_config,
    register_api_service,
)
from .cert_manager import (
    clear_certificate_cache,
    download_certificate,
    get_certificate_path,
    set_cache_directory,
)
from .config import (
    CONFIG_FILE_ENV_VAR,
    DEFAULT_CONFIG_FILE,
    ConfigurationError,
    EnvPrioritySettingsMixin,
    MACSDKConfig,
    config,
    create_config,
    load_config_from_yaml,
    validate_config,
)
from .graph import create_chatbot_graph, create_web_chatbot_graph
from .llm import get_answer_model
from .logging import (
    DEFAULT_QUIET_LOGGERS,
    configure_cli_logging,
    determine_log_level,
    setup_logging,
)
from .models import BaseAgentResponse
from .protocol import SpecialistAgent
from .registry import (
    AgentRegistry,
    get_all_agent_tools,
    get_all_capabilities,
    get_registry,
    register_agent,
)
from .state import ChatbotState
from .utils import (
    STREAM_WRITER_KEY,
    create_config_with_writer,
    log_progress,
    run_agent_with_tools,
)

__all__ = [
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
    "EnvPrioritySettingsMixin",
    "config",
    "create_config",
    "load_config_from_yaml",
    "validate_config",
    "ConfigurationError",
    "DEFAULT_CONFIG_FILE",
    "CONFIG_FILE_ENV_VAR",
    # Logging
    "configure_cli_logging",
    "determine_log_level",
    "setup_logging",
    "DEFAULT_QUIET_LOGGERS",
    # LLM (use these functions for lazy initialization)
    "get_answer_model",
    # Models
    "BaseAgentResponse",
    # Utils
    "log_progress",
    "run_agent_with_tools",
    "create_config_with_writer",
    "STREAM_WRITER_KEY",
    # API Registry
    "APIServiceConfig",
    "register_api_service",
    "get_api_service",
    "list_api_services",
    "clear_api_services",
    "load_api_services_from_config",
    # Certificate Manager
    "download_certificate",
    "get_certificate_path",
    "clear_certificate_cache",
    "set_cache_directory",
]
