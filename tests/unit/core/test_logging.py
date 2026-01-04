"""Tests for logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from macsdk.core.logging import (
    configure_cli_logging,
    determine_log_level,
    setup_logging,
)


def test_setup_logging_creates_default_log_directory(tmp_path: Path) -> None:
    """Test that setup_logging creates the default log directory."""
    with patch("macsdk.core.logging.DEFAULT_LOG_DIR", tmp_path / "logs"):
        log_file = setup_logging(app_name="test-app")

        assert log_file is not None
        assert log_file.parent.exists()
        assert log_file.parent == tmp_path / "logs"


def test_setup_logging_creates_log_file(tmp_path: Path) -> None:
    """Test that setup_logging creates a log file."""
    log_file_path = tmp_path / "test.log"
    result = setup_logging(log_file=log_file_path, app_name="test-app")

    assert result == log_file_path
    assert log_file_path.exists()


def test_setup_logging_log_file_naming_with_date(tmp_path: Path) -> None:
    """Test that log file includes date in name."""
    with patch("macsdk.core.logging.DEFAULT_LOG_DIR", tmp_path):
        log_file = setup_logging(app_name="my-chatbot")

        assert log_file is not None
        assert "my-chatbot-" in log_file.name
        # Should include date like "my-chatbot-2026-01-04.log"
        assert log_file.suffix == ".log"


def test_setup_logging_respects_log_level(tmp_path: Path) -> None:
    """Test that setup_logging sets the correct log level."""
    log_file = tmp_path / "test.log"
    setup_logging(level="WARNING", log_file=log_file, app_name="test-app")

    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING


def test_setup_logging_cli_mode_no_stderr(tmp_path: Path) -> None:
    """Test CLI mode (file only, no stderr handler)."""
    log_file = tmp_path / "test.log"
    setup_logging(
        level="INFO", log_file=log_file, log_to_stderr=False, app_name="test-app"
    )

    root_logger = logging.getLogger()

    # Should have exactly 1 handler (file)
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0], logging.FileHandler)


def test_setup_logging_web_mode_with_stderr(tmp_path: Path) -> None:
    """Test web mode (stderr + optional file)."""
    log_file = tmp_path / "test.log"
    setup_logging(
        level="INFO", log_file=log_file, log_to_stderr=True, app_name="test-app"
    )

    root_logger = logging.getLogger()

    # Should have 2 handlers (file + stderr)
    assert len(root_logger.handlers) == 2
    handler_types = [type(h) for h in root_logger.handlers]
    assert logging.FileHandler in handler_types
    assert logging.StreamHandler in handler_types


def test_setup_logging_web_mode_stderr_only(tmp_path: Path) -> None:
    """Test web mode with stderr only (no file logging for containers)."""
    with patch("macsdk.core.logging.DEFAULT_LOG_DIR", tmp_path):
        result = setup_logging(
            level="INFO",
            log_to_stderr=True,
            log_to_file=False,  # No file logging
            app_name="test-app",
        )

        # Should return None when file logging is disabled
        assert result is None

        root_logger = logging.getLogger()

        # Should have exactly 1 handler (stderr only)
        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)

        # No log file should be created
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 0


def test_setup_logging_clears_existing_handlers(tmp_path: Path) -> None:
    """Test that setup_logging clears existing handlers."""
    # Add a dummy handler
    root_logger = logging.getLogger()
    dummy_handler = logging.NullHandler()
    root_logger.addHandler(dummy_handler)

    log_file = tmp_path / "test.log"
    setup_logging(level="INFO", log_file=log_file, app_name="test-app")

    # Should have replaced all handlers
    assert dummy_handler not in root_logger.handlers


def test_setup_logging_custom_log_file_path(tmp_path: Path) -> None:
    """Test custom log file path."""
    custom_path = tmp_path / "custom" / "path" / "my.log"
    result = setup_logging(log_file=custom_path, app_name="test-app")

    assert result == custom_path
    assert custom_path.exists()
    assert custom_path.parent.exists()


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    """Test that logs are actually written to the file."""
    log_file = tmp_path / "test.log"
    setup_logging(level="INFO", log_file=log_file, app_name="test-app")

    test_logger = logging.getLogger("test_module")
    test_logger.info("Test message")

    # Read the log file
    log_content = log_file.read_text()
    assert "Test message" in log_content
    assert "test_module" in log_content


def test_setup_logging_debug_level(tmp_path: Path) -> None:
    """Test DEBUG log level."""
    log_file = tmp_path / "test.log"
    setup_logging(level="DEBUG", log_file=log_file, app_name="test-app")

    test_logger = logging.getLogger("test_module")
    test_logger.debug("Debug message")

    log_content = log_file.read_text()
    assert "Debug message" in log_content
    assert "DEBUG" in log_content


def test_setup_logging_filters_below_level(tmp_path: Path) -> None:
    """Test that messages below log level are filtered."""
    log_file = tmp_path / "test.log"
    setup_logging(level="WARNING", log_file=log_file, app_name="test-app")

    test_logger = logging.getLogger("test_module")
    test_logger.info("Info message")
    test_logger.warning("Warning message")

    log_content = log_file.read_text()
    assert "Info message" not in log_content
    assert "Warning message" in log_content


def test_setup_logging_error_level(tmp_path: Path) -> None:
    """Test ERROR log level."""
    log_file = tmp_path / "test.log"
    setup_logging(level="ERROR", log_file=log_file, app_name="test-app")

    test_logger = logging.getLogger("test_module")
    test_logger.warning("Warning message")
    test_logger.error("Error message")

    log_content = log_file.read_text()
    assert "Warning message" not in log_content
    assert "Error message" in log_content


def test_setup_logging_formatter(tmp_path: Path) -> None:
    """Test that log formatter includes expected fields."""
    log_file = tmp_path / "test.log"
    setup_logging(level="INFO", log_file=log_file, app_name="test-app")

    test_logger = logging.getLogger("test_module")
    test_logger.info("Test message")

    log_content = log_file.read_text()
    # Should include: timestamp, module name, level, message
    assert "test_module" in log_content
    assert "INFO" in log_content
    assert "Test message" in log_content
    # Should have timestamp (YYYY-MM-DD format)
    assert "-" in log_content.split()[0]  # Date part


def test_setup_logging_custom_log_dir(tmp_path: Path) -> None:
    """Test that setup_logging respects custom log_dir from config."""
    custom_dir = tmp_path / "custom_logs"
    with patch("macsdk.core.logging.DEFAULT_LOG_DIR", tmp_path / "default"):
        log_file = setup_logging(
            level="INFO",
            log_dir=custom_dir,
            app_name="test-app",
        )

        assert log_file is not None
        assert log_file.parent == custom_dir
        assert custom_dir.exists()


def test_setup_logging_custom_log_filename(tmp_path: Path) -> None:
    """Test that setup_logging respects custom log_filename from config."""
    custom_filename = "my-custom-log.log"
    with patch("macsdk.core.logging.DEFAULT_LOG_DIR", tmp_path):
        log_file = setup_logging(
            level="INFO",
            log_filename=custom_filename,
            app_name="test-app",
        )

        assert log_file is not None
        assert log_file.name == custom_filename
        assert log_file.parent == tmp_path


def test_setup_logging_log_file_overrides_dir_and_filename(tmp_path: Path) -> None:
    """Test that explicit log_file parameter overrides log_dir and log_filename."""
    explicit_file = tmp_path / "explicit" / "test.log"
    custom_dir = tmp_path / "custom"

    result = setup_logging(
        level="INFO",
        log_file=explicit_file,
        log_dir=custom_dir,  # Should be ignored
        log_filename="ignored.log",  # Should be ignored
        app_name="test-app",
    )

    assert result == explicit_file
    assert explicit_file.exists()
    # custom_dir should not be created
    assert not custom_dir.exists()


def test_determine_log_level_explicit_flag() -> None:
    """Test that explicit --log-level flag has highest priority."""
    result = determine_log_level(
        log_level="DEBUG",
        quiet=True,  # Should be ignored
        verbose=2,  # Should be ignored
        config_default="ERROR",  # Should be ignored
    )
    assert result == "DEBUG"


def test_determine_log_level_quiet_flag() -> None:
    """Test that --quiet flag sets ERROR level."""
    result = determine_log_level(
        log_level=None,
        quiet=True,
        verbose=0,
        config_default="INFO",
    )
    assert result == "ERROR"


def test_determine_log_level_verbose_debug() -> None:
    """Test that -vv sets DEBUG level."""
    result = determine_log_level(
        log_level=None,
        quiet=False,
        verbose=2,
        config_default="WARNING",
    )
    assert result == "DEBUG"


def test_determine_log_level_verbose_info() -> None:
    """Test that -v sets INFO level."""
    result = determine_log_level(
        log_level=None,
        quiet=False,
        verbose=1,
        config_default="WARNING",
    )
    assert result == "INFO"


def test_determine_log_level_config_default() -> None:
    """Test that config default is used when no flags are set."""
    result = determine_log_level(
        log_level=None,
        quiet=False,
        verbose=0,
        config_default="WARNING",
    )
    assert result == "WARNING"


def test_configure_cli_logging_show_llm_calls_overrides_quiet(tmp_path: Path) -> None:
    """Test that --show-llm-calls forces INFO level even with --quiet."""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.log_level = "INFO"
    mock_config.log_dir = tmp_path
    mock_config.log_filename = None

    log_file, debug_enabled = configure_cli_logging(
        show_llm_calls=True,
        verbose=0,
        quiet=True,  # Would normally set ERROR
        log_level=None,
        log_file=None,
        config=mock_config,
        app_name="test-app",
        log_to_stderr=False,
    )

    # Should have created a log file
    assert log_file is not None
    # Debug middleware should be enabled
    assert debug_enabled is True
    # Root logger should be at INFO, not ERROR
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_configure_cli_logging_show_llm_calls_overrides_warning(tmp_path: Path) -> None:
    """Test that --show-llm-calls forces INFO level when default is WARNING."""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.log_level = "WARNING"  # Default would be WARNING
    mock_config.log_dir = tmp_path
    mock_config.log_filename = None

    log_file, debug_enabled = configure_cli_logging(
        show_llm_calls=True,
        verbose=0,
        quiet=False,
        log_level=None,
        log_file=None,
        config=mock_config,
        app_name="test-app",
        log_to_stderr=False,
    )

    # Should have created a log file
    assert log_file is not None
    # Debug middleware should be enabled
    assert debug_enabled is True
    # Root logger should be at INFO, not WARNING
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_configure_cli_logging_quiet_loggers(tmp_path: Path) -> None:
    """Test that --show-llm-calls silences noisy HTTP libraries."""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.log_level = "DEBUG"
    mock_config.log_dir = tmp_path
    mock_config.log_filename = None

    configure_cli_logging(
        show_llm_calls=True,
        verbose=2,
        quiet=False,
        log_level=None,
        log_file=None,
        config=mock_config,
        app_name="test-app",
        log_to_stderr=False,
    )

    # Noisy loggers should be set to WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    assert logging.getLogger("httpx").level == logging.WARNING


def test_configure_cli_logging_config_debug_enables_middleware(tmp_path: Path) -> None:
    """Test that config.debug=True enables the debug middleware."""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.log_level = "WARNING"
    mock_config.log_dir = tmp_path
    mock_config.log_filename = None
    mock_config.debug = True  # Backward compatibility with config.yml

    log_file, debug_enabled = configure_cli_logging(
        show_llm_calls=False,  # Not explicitly requested
        verbose=0,
        quiet=False,
        log_level=None,
        log_file=None,
        config=mock_config,
        app_name="test-app",
        log_to_stderr=False,
    )

    # Should have created a log file
    assert log_file is not None
    # Debug middleware should be enabled due to config.debug
    assert debug_enabled is True
    # Root logger should be at INFO (upgraded from WARNING)
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_configure_cli_logging_verbose_vv_enables_middleware(tmp_path: Path) -> None:
    """Test that -vv enables the debug middleware."""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.log_level = "WARNING"
    mock_config.log_dir = tmp_path
    mock_config.log_filename = None
    mock_config.debug = False

    log_file, debug_enabled = configure_cli_logging(
        show_llm_calls=False,  # Not explicitly requested
        verbose=2,  # -vv should enable middleware
        quiet=False,
        log_level=None,
        log_file=None,
        config=mock_config,
        app_name="test-app",
        log_to_stderr=False,
    )

    # Should have created a log file
    assert log_file is not None
    # Debug middleware should be enabled due to -vv
    assert debug_enabled is True
    # Root logger should be at DEBUG (from verbose=2)
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_configure_cli_logging_no_middleware_without_flags(tmp_path: Path) -> None:
    """Test that middleware is NOT enabled without any debug flags."""
    from unittest.mock import Mock

    mock_config = Mock()
    mock_config.log_level = "INFO"
    mock_config.log_dir = tmp_path
    mock_config.log_filename = None
    mock_config.debug = False

    log_file, debug_enabled = configure_cli_logging(
        show_llm_calls=False,
        verbose=0,
        quiet=False,
        log_level=None,
        log_file=None,
        config=mock_config,
        app_name="test-app",
        log_to_stderr=False,
    )

    # Should have created a log file
    assert log_file is not None
    # Debug middleware should NOT be enabled
    assert debug_enabled is False


@pytest.fixture(autouse=True)
def reset_logging() -> None:
    """Reset logging configuration before each test."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.WARNING)  # Reset to default
