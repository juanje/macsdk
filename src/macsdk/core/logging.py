"""Logging configuration for MACSDK.

This module provides centralized logging setup that:
- Keeps stdout clean for user interaction (CLI chat)
- Logs to file for debugging and monitoring
- Provides consistent behavior across CLI and Web interfaces
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from .config import MACSDKConfig

# Default log directory (current working directory)
DEFAULT_LOG_DIR = Path("./logs")

# Third-party loggers that generate excessive debug output
# Silenced to keep logs readable when showing LLM calls
DEFAULT_QUIET_LOGGERS = {
    "httpcore": "WARNING",
    "httpx": "WARNING",
    "httpcore.connection": "WARNING",
    "httpcore.http11": "WARNING",
}


def determine_log_level(
    log_level: str | None,
    quiet: bool,
    verbose: int,
    config_default: str,
) -> Literal["DEBUG", "INFO", "WARNING", "ERROR"]:
    """Determine effective log level from CLI flags and config.

    This centralizes the precedence logic used across all CLI entry points:
    1. Explicit --log-level flag (highest priority)
    2. Quiet flag (-q) → ERROR
    3. Verbose flags (-vv → DEBUG, -v → INFO)
    4. Config file default (lowest priority)

    Args:
        log_level: Explicit log level from CLI flag.
        quiet: Whether quiet mode is enabled.
        verbose: Verbosity count (0, 1, 2, ...).
        config_default: Default level from configuration.

    Returns:
        The effective log level as a string (DEBUG, INFO, WARNING, ERROR).
    """
    if log_level:
        return cast(Literal["DEBUG", "INFO", "WARNING", "ERROR"], log_level)
    elif quiet:
        return "ERROR"
    elif verbose >= 2:
        return "DEBUG"
    elif verbose >= 1:
        return "INFO"
    else:
        return cast(Literal["DEBUG", "INFO", "WARNING", "ERROR"], config_default)


def _validate_log_directory(log_dir: Path) -> None:
    """Validate that a log directory is writable.

    Args:
        log_dir: Directory path to validate.

    Raises:
        OSError: If directory cannot be created or is not writable.
        PermissionError: If directory exists but lacks write permissions.
    """
    import os

    # Try to create the directory if it doesn't exist
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise OSError(
            f"Failed to create log directory {log_dir} (permission denied). "
            f"Check permissions or specify a different path with "
            f"--log-file or LOG_DIR."
        ) from e
    except OSError as e:
        # Other OS errors (disk full, invalid path, etc.)
        raise OSError(
            f"Failed to create log directory {log_dir}. "
            f"Check permissions or specify a different path with "
            f"--log-file or LOG_DIR."
        ) from e

    # Quick check using os.access (more reliable than write test on some systems)
    if not os.access(log_dir, os.W_OK):
        raise OSError(
            f"Log directory {log_dir} is not writable. "
            f"Check permissions or specify a different path with "
            f"--log-file or LOG_DIR."
        )

    # Verify write permissions with actual file operation
    # This catches cases where os.access returns true but writes still fail
    # (e.g., SELinux policies, quota limits)
    test_file = log_dir / ".macsdk_write_test"
    try:
        test_file.write_text("test", encoding="utf-8")
    except PermissionError as e:
        raise OSError(
            f"Log directory {log_dir} is not writable (permission denied). "
            f"Check permissions or specify a different path with "
            f"--log-file or LOG_DIR."
        ) from e
    except OSError as e:
        # Other write errors (disk full, read-only filesystem, etc.)
        raise OSError(
            f"Log directory {log_dir} is not writable. "
            f"Check permissions or specify a different path with "
            f"--log-file or LOG_DIR."
        ) from e
    finally:
        # Always try to clean up the test file, even if write failed
        try:
            if test_file.exists():
                test_file.unlink()
        except OSError:
            # Ignore cleanup errors - the write test already determined writability
            pass


def configure_cli_logging(
    show_llm_calls: bool,
    verbose: int,
    quiet: bool,
    log_level: str | None,
    log_file: str | None,
    config: "MACSDKConfig",
    app_name: str,
    log_to_stderr: bool = False,
) -> tuple[Path | None, bool]:
    """Configure logging for CLI applications with standard options.

    This helper encapsulates the common logging setup pattern used across
    all CLI entry points (chat, web, agents), reducing boilerplate in templates.

    Args:
        show_llm_calls: Whether to show LLM prompts in logs.
        verbose: Verbosity count from -v/-vv flags.
        quiet: Whether quiet mode is enabled.
        log_level: Explicit log level override.
        log_file: Explicit log file path override.
        config: Configuration object with log_level, log_dir, log_filename.
        app_name: Application name for log file naming.
        log_to_stderr: Whether to log to stderr (for web mode).

    Returns:
        Tuple of (log_file_path, debug_enabled).
        log_file_path is None if file logging is disabled.

    Example:
        >>> actual_log, debug_enabled = configure_cli_logging(
        ...     show_llm_calls, verbose, quiet, log_level, log_file,
        ...     config, "my-chatbot"
        ... )
        >>> if actual_log:
        ...     print(f"Logs: {actual_log}")
    """
    # Determine if debug middleware should be enabled
    # Multiple ways to enable it for backward compatibility:
    # 1. Explicit --show-llm-calls flag
    # 2. config.debug setting in config.yml
    # 3. High verbosity (-vv) implies wanting to see debug info
    debug_middleware_enabled = show_llm_calls or config.debug or (verbose >= 2)

    # Determine effective log level
    effective_level = determine_log_level(
        log_level=log_level,
        quiet=quiet,
        verbose=verbose,
        config_default=config.log_level,
    )

    # Fix: Ensure LLM calls are visible if middleware is enabled
    # PromptDebugMiddleware logs at INFO level, so we need at least INFO
    if debug_middleware_enabled and effective_level in ("WARNING", "ERROR"):
        effective_level = "INFO"

    # Configure selective logging when showing LLM calls
    loggers_override = DEFAULT_QUIET_LOGGERS if debug_middleware_enabled else None

    # Determine if file logging should be enabled
    log_path = Path(log_file) if log_file else None
    log_to_file_enabled = True
    if log_to_stderr:
        # Web mode: only enable file logging if explicitly requested
        log_to_file_enabled = log_path is not None or config.log_filename is not None

    # Setup logging
    try:
        actual_log = setup_logging(
            level=effective_level,
            log_file=log_path,
            log_dir=config.log_dir,
            log_filename=config.log_filename,
            log_to_stderr=log_to_stderr,
            log_to_file=log_to_file_enabled,
            app_name=app_name,
            loggers_config=loggers_override,
            clean_llm_format=debug_middleware_enabled,
        )
    except OSError as e:
        # Let caller handle the error display
        raise OSError(f"Failed to setup logging: {e}") from e

    return actual_log, debug_middleware_enabled


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    log_file: Path | None = None,
    log_dir: Path | None = None,
    log_filename: str | None = None,
    log_to_stderr: bool = False,
    log_to_file: bool = True,
    app_name: str = "macsdk",
    loggers_config: dict[str, str] | None = None,
    clean_llm_format: bool = False,
) -> Path | None:
    """Configure logging for the application.

    For CLI chat mode:
    - Logs go to a file (not stdout)
    - stdout remains clean for user interaction

    For Web mode (containers/K8s):
    - Logs go to stderr only (12-factor app pattern)
    - No file logging by default

    Args:
        level: Minimum log level to capture for the root logger.
        log_file: Explicit path for log file (highest priority).
                 If provided, log_dir and log_filename are ignored.
        log_dir: Directory for log files (from config.yml).
                If None, uses DEFAULT_LOG_DIR (./logs).
        log_filename: Custom filename template (from config.yml).
                     If None, auto-generates timestamped filename.
        log_to_stderr: If True, also log to stderr (for web mode).
        log_to_file: If False, skips file logging entirely (for containers).
                    Defaults to True for backward compatibility.
        app_name: Name used for log file naming when auto-generating.
        loggers_config: Optional dict of logger_name -> level overrides.
                       Example: {"httpcore": "WARNING", "macsdk.middleware": "DEBUG"}
                       Useful for silencing noisy third-party loggers while
                       enabling debug output for specific modules.
        clean_llm_format: If True, the LLM debug middleware logger will use a clean
                         format without timestamp/logger name for better readability.

    Returns:
        Path to the log file if file logging is enabled, None otherwise.
    """
    # Safe mapping of level strings to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    # Configure root logger
    root_logger = logging.getLogger()
    log_level_int = level_map.get(level.upper(), logging.INFO)
    root_logger.setLevel(log_level_int)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler (optional, disabled in container environments)
    actual_log_file: Path | None = None
    if log_to_file:
        # Determine log directory and validate write permissions early
        if log_file is None:
            # Use configured log_dir or fallback to default
            base_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
            # Validate directory is writable (raises OSError with helpful message)
            _validate_log_directory(base_dir)

            # Use configured log_filename or auto-generate
            if log_filename:
                filename = log_filename
            else:
                # Include date and time for multiple test sessions per day
                timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                filename = f"{app_name}-{timestamp}.log"

            actual_log_file = base_dir / filename
        else:
            actual_log_file = log_file
            # Validate parent directory is writable
            _validate_log_directory(actual_log_file.parent)

        # Ensure log file has restrictive permissions (0o600)
        # This protects sensitive data (LLM prompts/responses, PII)
        # Apply to both new and existing files for security
        #
        # SECURITY NOTE: On Windows, os.chmod only affects the read-only attribute
        # and does NOT provide POSIX-style user/group/other permissions.
        # Windows log files may still be readable by other users on the system.
        # For production Windows deployments, consider using NTFS ACLs or
        # storing logs in a protected directory.
        import os

        try:
            if not actual_log_file.exists():
                # Create with secure permissions from the start
                actual_log_file.touch(mode=0o600)
            else:
                # Update permissions on existing files
                os.chmod(actual_log_file, 0o600)
        except (OSError, NotImplementedError) as e:
            # Handle non-POSIX filesystems or permission errors gracefully
            # Warn user but continue - FileHandler will create/open the file
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to set restrictive permissions (0o600) on log file: {e}. "
                f"Log file {actual_log_file} may be readable by other users."
            )

        file_handler = logging.FileHandler(actual_log_file, encoding="utf-8")
        file_handler.setLevel(log_level_int)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Verify and enforce permissions after FileHandler opens the file
        # This catches cases where touch() failed but FileHandler created it
        try:
            if actual_log_file.exists():
                os.chmod(actual_log_file, 0o600)
        except (OSError, NotImplementedError):
            # Already warned above, no need to warn again
            pass

    # Stderr handler (for web mode)
    if log_to_stderr:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(log_level_int)
        stderr_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stderr_handler.setFormatter(stderr_formatter)
        root_logger.addHandler(stderr_handler)

    # Apply per-logger configuration for fine-grained control
    # This is useful for silencing noisy third-party libraries (httpcore, httpx)
    # while enabling debug output for specific modules (e.g., prompt debugging)
    if loggers_config:
        for logger_name, logger_level in loggers_config.items():
            specific_logger = logging.getLogger(logger_name)
            specific_level = level_map.get(logger_level.upper(), logging.INFO)
            specific_logger.setLevel(specific_level)

    # Configure clean format for LLM debug middleware if requested
    # This removes timestamp/logger name for better readability of LLM calls
    if clean_llm_format:
        debug_logger = logging.getLogger("macsdk.middleware.debug_prompts")

        # Clear any existing handlers (including inherited ones)
        # Note: This is intentional - this logger is exclusively managed by this
        # configuration. If setup_logging is called multiple times (e.g., in tests),
        # handlers are reset to ensure consistent behavior.
        for handler in debug_logger.handlers[:]:
            debug_logger.removeHandler(handler)

        # CRITICAL: Set propagate to False FIRST to prevent logs from
        # going to root logger. This must be done before adding new handlers.
        debug_logger.propagate = False

        # Set the logger level
        debug_logger.setLevel(log_level_int)

        # Create a clean formatter that only shows the message
        clean_formatter = logging.Formatter("%(message)s")

        # Add file handler with clean format if file logging is enabled
        if actual_log_file:
            clean_file_handler = logging.FileHandler(
                actual_log_file, mode="a", encoding="utf-8"
            )
            clean_file_handler.setLevel(log_level_int)
            clean_file_handler.setFormatter(clean_formatter)
            debug_logger.addHandler(clean_file_handler)

        # Add stderr handler with clean format if stderr logging is enabled
        if log_to_stderr:
            clean_stderr_handler = logging.StreamHandler(sys.stderr)
            clean_stderr_handler.setLevel(log_level_int)
            clean_stderr_handler.setFormatter(clean_formatter)
            debug_logger.addHandler(clean_stderr_handler)

    return actual_log_file
