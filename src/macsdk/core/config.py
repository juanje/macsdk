"""Configuration management for MACSDK.

This module provides configuration classes and utilities for
customizing the chatbot framework.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""

    pass


# Default config file name
DEFAULT_CONFIG_FILE = "config.yml"

# Environment variable to override config file path
CONFIG_FILE_ENV_VAR = "MACSDK_CONFIG_FILE"


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file lazily (imports yaml only when needed).

    Args:
        path: Path to the YAML file.

    Returns:
        Dictionary with the YAML content.

    Raises:
        ConfigurationError: If YAML parsing fails or file cannot be read.
    """
    try:
        import yaml  # Lazy import - only loaded when YAML file exists
    except ImportError:
        raise ConfigurationError(
            "PyYAML is required to load config.yml files.\n"
            "Install it with: pip install pyyaml"
        )

    try:
        with open(path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if content else {}
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {path}: {e}")
    except OSError as e:
        raise ConfigurationError(f"Cannot read {path}: {e}")


def load_config_from_yaml(
    config_path: str | Path | None = None,
    search_path: Path | None = None,
) -> dict[str, Any]:
    """Load configuration from a YAML file if it exists.

    The function searches for config in this order:
    1. Explicit config_path if provided
    2. Path from MACSDK_CONFIG_FILE environment variable
    3. config.yml in search_path (defaults to current directory)

    Args:
        config_path: Explicit path to config file. If provided, file must exist.
        search_path: Directory to search for config.yml. Defaults to cwd.

    Returns:
        Dictionary with configuration values, or empty dict if no file found.

    Raises:
        ConfigurationError: If explicit config_path doesn't exist or is invalid.
    """
    # 1. Explicit path - must exist
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(f"Config file not found: {path}")
        return _load_yaml_file(path)

    # 2. Environment variable
    env_path = os.environ.get(CONFIG_FILE_ENV_VAR)
    if env_path:
        path = Path(env_path)
        if not path.exists():
            raise ConfigurationError(
                f"Config file from {CONFIG_FILE_ENV_VAR} not found: {path}"
            )
        return _load_yaml_file(path)

    # 3. Default location - optional, no error if not found
    if search_path is None:
        search_path = Path.cwd()
    default_path = search_path / DEFAULT_CONFIG_FILE
    if default_path.exists():
        return _load_yaml_file(default_path)

    return {}


class MACSDKConfig(BaseSettings):
    """Base configuration for MACSDK chatbots.

    This class can be extended by custom chatbots to add
    their own configuration options.

    Configuration is loaded from multiple sources (in order of precedence):
    1. Explicit values passed to constructor
    2. Environment variables
    3. .env file
    4. config.yml file (if exists)
    5. Default values

    Attributes:
        llm_model: The LLM model to use for responses.
        llm_temperature: Temperature for response generation.
        llm_reasoning_effort: Reasoning effort level for supported models.
        google_api_key: API key for Google AI services.
        classifier_model: Model to use for classification tasks.
        classifier_temperature: Temperature for classification.
        classifier_reasoning_effort: Reasoning effort for classification.
        server_host: Host for the web server.
        server_port: Port for the web server.
        message_max_length: Maximum message length in characters.
        warmup_timeout: Timeout for graph warmup on startup.
    """

    # LLM Configuration
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = 0.3
    llm_reasoning_effort: Optional[str] = "medium"
    google_api_key: Optional[str] = None
    classifier_model: str = "gemini-2.5-flash"
    classifier_temperature: float = 0.0
    classifier_reasoning_effort: Optional[str] = "low"

    # Web Server Configuration
    # Bind to all interfaces by default (users can override to localhost in production)
    server_host: str = "0.0.0.0"  # nosec B104
    server_port: int = 8000
    message_max_length: int = 5000
    warmup_timeout: float = 15.0

    # Middleware Configuration
    include_datetime: bool = True  # Inject datetime context into prompts
    enable_todo: bool = True  # Enable ToDo middleware for task planning

    # Summarization Configuration
    summarization_enabled: bool = False  # Enable context summarization
    summarization_trigger_tokens: int = 100000  # Token threshold to trigger
    summarization_keep_messages: int = 6  # Messages to keep unsummarized

    # Agent Execution Configuration
    recursion_limit: int = 50  # Max iterations for agent tool calls
    # Use higher values (100+) for complex workflows with many steps

    # Debug Configuration
    debug: bool = False  # Enable debug mode (shows prompts sent to LLM)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow custom config fields in subclasses
    )

    def validate_api_key(self) -> None:
        """Validate that Google API key is configured.

        Raises:
            ConfigurationError: If GOOGLE_API_KEY is not set.
        """
        if not self.google_api_key:
            raise ConfigurationError(
                "GOOGLE_API_KEY is not configured.\n\n"
                "Please set it in one of these ways:\n"
                "  1. Create a .env file with: GOOGLE_API_KEY=your_key_here\n"
                "  2. Add to config.yml: google_api_key: your_key_here\n"
                "  3. Export the environment variable:\n"
                "     export GOOGLE_API_KEY=your_key_here\n\n"
                "Get an API key from: https://aistudio.google.com/apikey"
            )

    def get_api_key(self) -> str:
        """Get Google API key, raising an error if not configured.

        Returns:
            The Google API key.

        Raises:
            ConfigurationError: If GOOGLE_API_KEY is not set.
        """
        self.validate_api_key()
        return self.google_api_key  # type: ignore[return-value]


def create_config(
    config_path: str | Path | None = None,
    search_path: Path | None = None,
    **overrides: Any,
) -> MACSDKConfig:
    """Create a configuration instance with optional YAML file loading.

    This is the recommended way to create config in chatbots and agents.
    It automatically loads config.yml if present.

    Args:
        config_path: Explicit path to config file.
        search_path: Directory to search for config.yml.
        **overrides: Additional values to override.

    Returns:
        Configured MACSDKConfig instance.

    Example:
        >>> # In chatbot main.py
        >>> config = create_config()  # Loads config.yml if present
        >>>
        >>> # With explicit path
        >>> config = create_config(config_path="custom_config.yml")
        >>>
        >>> # With overrides
        >>> config = create_config(llm_model="gemini-2.0-pro")
    """
    yaml_config = load_config_from_yaml(config_path, search_path)
    # Merge: overrides > yaml_config
    merged = {**yaml_config, **overrides}
    return MACSDKConfig(**merged)


# Default configuration instance (loads config.yml from cwd if present)
# Note: For standalone agent testing, agents should create their own config
# using create_config() in their entry point
config = MACSDKConfig()


def validate_config() -> None:
    """Validate the global configuration.

    Call this at application startup to fail fast if configuration is missing.

    Raises:
        ConfigurationError: If required configuration is missing.
    """
    config.validate_api_key()
