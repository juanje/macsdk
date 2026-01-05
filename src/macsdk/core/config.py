"""Configuration management for MACSDK.

This module provides configuration classes and utilities for
customizing the chatbot framework.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from .url_security import URLSecurityConfig

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values."""

    pass


class EnvPrioritySettingsMixin:
    """Mixin that gives environment variables priority over constructor args.

    Use this mixin with BaseSettings subclasses to ensure environment variables
    can override values from config files (like config.yml).

    Priority order (highest to lowest):
    1. Environment variables
    2. .env file
    3. Constructor arguments (from YAML via load functions)
    4. Default values

    Example:
        class MyConfig(EnvPrioritySettingsMixin, BaseSettings):
            api_key: str = "default"

        # Now MY_API_KEY env var will override config.yml values
    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to prioritize environment variables.

        Returns sources in priority order (first = highest priority).
        """
        return (
            env_settings,
            dotenv_settings,
            init_settings,
            file_secret_settings,
        )


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


class MACSDKConfig(EnvPrioritySettingsMixin, BaseSettings):
    """Base configuration for MACSDK chatbots.

    This class can be extended by custom chatbots to add
    their own configuration options.

    Configuration is loaded from multiple sources (in order of precedence):
    1. Environment variables (highest priority)
    2. .env file
    3. config.yml file (via create_config)
    4. Default values (lowest priority)

    This priority order allows environment variables to override config files,
    which is useful for CI/CD environments or local development overrides.

    Attributes:
        llm_model: The LLM model to use for responses.
        llm_temperature: Temperature for response generation.
        llm_reasoning_effort: Reasoning effort level for supported models.
        google_api_key: API key for Google AI services.
        server_host: Host for the web server.
        server_port: Port for the web server.
        message_max_length: Maximum message length in characters.
        warmup_timeout: Timeout for graph warmup on startup.
        enable_todo: (DEPRECATED) TODO middleware is always enabled.
        url_security: URL security configuration for SSRF protection.
    """

    # LLM Configuration
    llm_model: str = "gemini-2.5-flash"
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    llm_reasoning_effort: Optional[str] = "medium"
    google_api_key: Optional[str] = None

    # Web Server Configuration
    # Bind to all interfaces by default (users can override to localhost in production)
    server_host: str = "0.0.0.0"  # nosec B104
    server_port: int = Field(default=8000, ge=1, le=65535)
    message_max_length: int = Field(default=5000, gt=0)
    warmup_timeout: float = Field(default=15.0, gt=0)

    # Middleware Configuration
    include_datetime: bool = True  # Inject datetime context into prompts
    enable_todo: bool = Field(
        default=True,
        deprecated=True,
        description=(
            "DEPRECATED: TODO middleware is always enabled. This setting has no effect."
        ),
    )

    # Summarization Configuration
    summarization_enabled: bool = False  # Enable context summarization
    summarization_trigger_tokens: int = Field(default=100000, gt=0)
    summarization_keep_messages: int = Field(default=6, ge=1)

    # Agent Execution Configuration
    recursion_limit: int = Field(default=50, ge=1)
    # Use higher values (100+) for complex workflows with many steps

    # Debug Configuration
    debug: bool = False  # Enable debug mode (shows prompts sent to LLM)

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_dir: Path = Field(default_factory=lambda: Path("./logs"))
    log_filename: Optional[str] = None  # None = auto-generate with date

    # Debug Middleware Configuration (improved)
    debug_prompt_max_length: int = Field(
        default=10000, gt=0, description="Max characters per prompt in debug logs"
    )
    debug_show_response: bool = True  # Changed from False

    # URL Security Configuration
    url_security: URLSecurityConfig = Field(default_factory=URLSecurityConfig)

    @field_validator("log_level", mode="before")
    @classmethod
    def uppercase_log_level(cls, v: Any) -> Any:
        """Normalize log level to uppercase for case-insensitive input."""
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("log_dir", mode="before")
    @classmethod
    def expand_log_dir_path(cls, v: Any) -> Any:
        """Expand user paths like ~/logs to absolute paths.

        Resolves symlinks and relative paths for consistent log locations.
        """
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        elif isinstance(v, Path):
            return v.expanduser().resolve()
        return v

    @field_validator("url_security", mode="before")
    @classmethod
    def validate_url_security(cls, value: Any) -> Any:
        """Convert dict from YAML to URLSecurityConfig if needed.

        Args:
            value: Raw value from YAML/config (dict or URLSecurityConfig).

        Returns:
            URLSecurityConfig instance.
        """
        if isinstance(value, dict):
            return URLSecurityConfig(**value)
        return value

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
    try:
        return MACSDKConfig(**merged)
    except ValidationError as e:
        # Pydantic validation error - build detailed message
        error_lines = ["Configuration validation failed in config.yml:"]
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_lines.append(f"  - {field}: {msg}")
        error_lines.append(
            "\nPlease fix the errors in config.yml and restart the application."
        )
        error_msg = "\n".join(error_lines)
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e


def _create_default_config() -> MACSDKConfig:
    """Create default config instance, loading config.yml if present.

    Implements "Fail Closed" security: if config.yml exists but cannot be
    loaded or parsed, raises ConfigurationError rather than silently falling
    back to insecure defaults. This ensures users are never unknowingly left
    unprotected due to configuration errors.

    Returns:
        MACSDKConfig: Configuration instance with settings from config.yml,
                      or defaults if config.yml doesn't exist.

    Raises:
        ConfigurationError: If config.yml exists but fails to load (YAML
                           syntax error, validation error, etc.). The entry
                           point (CLI/web server) should catch this and exit
                           gracefully.
    """
    try:
        yaml_config = load_config_from_yaml()
        return MACSDKConfig(**yaml_config)
    except FileNotFoundError:
        # No config file found - this is normal, use defaults silently
        return MACSDKConfig()
    except ValidationError as e:
        # Pydantic validation error - build detailed message
        error_lines = ["Configuration validation failed in config.yml:"]
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_lines.append(f"  - {field}: {msg}")
        error_lines.append(
            "\nPlease fix the errors in config.yml and restart the application."
        )
        error_msg = "\n".join(error_lines)
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e
    except Exception as e:
        # YAML parsing or other errors - build clean message
        error_type = type(e).__name__
        error_msg = (
            f"Failed to load config.yml: {error_type}: {e}\n"
            "Please fix the errors in config.yml and restart the application."
        )
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e


# Lazy-loaded configuration instance
# The config is created on first access to avoid crashing during import
# if config.yml has errors. This allows the CLI to show friendly error messages.
_config: MACSDKConfig | None = None


def _get_config() -> MACSDKConfig:
    """Get or create the global config instance (lazy loading)."""
    global _config
    if _config is None:
        _config = _create_default_config()
    return _config


# Property-based access for backward compatibility
class _ConfigProxy:
    """Proxy object that lazy-loads config on attribute access."""

    def __getattr__(self, name: str) -> Any:
        return getattr(_get_config(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(_get_config(), name, value)


config = _ConfigProxy()  # type: ignore[assignment]


def validate_config() -> None:
    """Validate the global configuration.

    Call this at application startup to fail fast if configuration is missing.

    Raises:
        ConfigurationError: If required configuration is missing.
    """
    config.validate_api_key()
