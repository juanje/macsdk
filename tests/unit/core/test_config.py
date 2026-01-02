"""Tests for MACSDK configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from macsdk.core.config import (
    CONFIG_FILE_ENV_VAR,
    DEFAULT_CONFIG_FILE,
    ConfigurationError,
    MACSDKConfig,
    _create_default_config,
    create_config,
    load_config_from_yaml,
)

if TYPE_CHECKING:
    pass


# Test constants
TEST_LLM_MODEL = "test-model-1.0"
TEST_TEMPERATURE = 0.5
TEST_API_KEY = "test-api-key-12345"
TEST_SERVER_PORT = 9999


class TestDefaultConfigFile:
    """Tests for default config file constant."""

    def test_default_config_file_name(self) -> None:
        """Default config file name is config.yml."""
        assert DEFAULT_CONFIG_FILE == "config.yml"


class TestConfigFileEnvVar:
    """Tests for config file environment variable constant."""

    def test_env_var_name(self) -> None:
        """Environment variable name is correct."""
        assert CONFIG_FILE_ENV_VAR == "MACSDK_CONFIG_FILE"


class TestMACSDKConfig:
    """Tests for MACSDKConfig class."""

    def test_default_values(self) -> None:
        """Config has sensible defaults."""
        config = MACSDKConfig()
        assert config.llm_model == "gemini-2.5-flash"
        assert config.llm_temperature == 0.3
        assert config.server_port == 8000

    def test_custom_values(self) -> None:
        """Config accepts custom values."""
        config = MACSDKConfig(
            llm_model=TEST_LLM_MODEL,
            llm_temperature=TEST_TEMPERATURE,
            server_port=TEST_SERVER_PORT,
        )
        assert config.llm_model == TEST_LLM_MODEL
        assert config.llm_temperature == TEST_TEMPERATURE
        assert config.server_port == TEST_SERVER_PORT

    def test_validate_api_key_raises_when_missing(self) -> None:
        """validate_api_key raises when API key is not set."""
        config = MACSDKConfig(google_api_key=None)
        with pytest.raises(ConfigurationError, match="GOOGLE_API_KEY"):
            config.validate_api_key()

    def test_validate_api_key_passes_when_set(self) -> None:
        """validate_api_key passes when API key is set."""
        config = MACSDKConfig(google_api_key=TEST_API_KEY)
        config.validate_api_key()  # Should not raise

    def test_get_api_key_returns_key_when_set(self) -> None:
        """get_api_key returns the key when set."""
        config = MACSDKConfig(google_api_key=TEST_API_KEY)
        assert config.get_api_key() == TEST_API_KEY

    def test_get_api_key_raises_when_missing(self) -> None:
        """get_api_key raises when API key is not set."""
        config = MACSDKConfig(google_api_key=None)
        with pytest.raises(ConfigurationError):
            config.get_api_key()


class TestLoadConfigFromYaml:
    """Tests for load_config_from_yaml function."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for config files."""
        return tmp_path

    def test_returns_empty_dict_when_no_file(self, temp_config_dir: Path) -> None:
        """Returns empty dict when no config file exists."""
        result = load_config_from_yaml(search_path=temp_config_dir)
        assert result == {}

    def test_loads_config_yml(self, temp_config_dir: Path) -> None:
        """Loads config.yml from search path."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text(f"llm_model: {TEST_LLM_MODEL}\n")

        result = load_config_from_yaml(search_path=temp_config_dir)
        assert result["llm_model"] == TEST_LLM_MODEL

    def test_explicit_path_must_exist(self, temp_config_dir: Path) -> None:
        """Raises error when explicit path doesn't exist."""
        nonexistent = temp_config_dir / "nonexistent.yml"
        with pytest.raises(ConfigurationError, match="not found"):
            load_config_from_yaml(config_path=nonexistent)

    def test_loads_explicit_path(self, temp_config_dir: Path) -> None:
        """Loads config from explicit path."""
        config_file = temp_config_dir / "custom.yml"
        config_file.write_text(f"llm_temperature: {TEST_TEMPERATURE}\n")

        result = load_config_from_yaml(config_path=config_file)
        assert result["llm_temperature"] == TEST_TEMPERATURE

    def test_env_var_overrides_default(self, temp_config_dir: Path) -> None:
        """Environment variable path is used over default location."""
        env_config = temp_config_dir / "env_config.yml"
        env_config.write_text(f"server_port: {TEST_SERVER_PORT}\n")

        default_config = temp_config_dir / "config.yml"
        default_config.write_text("server_port: 1111\n")

        with patch.dict(os.environ, {CONFIG_FILE_ENV_VAR: str(env_config)}):
            result = load_config_from_yaml(search_path=temp_config_dir)
        assert result["server_port"] == TEST_SERVER_PORT

    def test_env_var_path_must_exist(self, temp_config_dir: Path) -> None:
        """Raises error when env var path doesn't exist."""
        nonexistent = temp_config_dir / "nonexistent.yml"
        with patch.dict(os.environ, {CONFIG_FILE_ENV_VAR: str(nonexistent)}):
            with pytest.raises(ConfigurationError, match=CONFIG_FILE_ENV_VAR):
                load_config_from_yaml(search_path=temp_config_dir)

    def test_handles_empty_yaml_file(self, temp_config_dir: Path) -> None:
        """Handles empty YAML file gracefully."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text("")

        result = load_config_from_yaml(search_path=temp_config_dir)
        assert result == {}

    def test_handles_yaml_with_comments_only(self, temp_config_dir: Path) -> None:
        """Handles YAML file with only comments."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text("# This is a comment\n# Another comment\n")

        result = load_config_from_yaml(search_path=temp_config_dir)
        assert result == {}

    def test_raises_on_invalid_yaml(self, temp_config_dir: Path) -> None:
        """Raises error on invalid YAML syntax."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text("invalid: yaml: syntax:\n  - broken")

        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            load_config_from_yaml(search_path=temp_config_dir)


class TestCreateConfig:
    """Tests for create_config function."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for config files."""
        return tmp_path

    def test_creates_default_config(self) -> None:
        """Creates config with defaults when no file exists."""
        config = create_config()
        assert config.llm_model == "gemini-2.5-flash"

    def test_loads_yaml_config(self, temp_config_dir: Path) -> None:
        """Loads values from YAML file."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text(f"llm_model: {TEST_LLM_MODEL}\n")

        config = create_config(search_path=temp_config_dir)
        assert config.llm_model == TEST_LLM_MODEL

    def test_overrides_take_precedence(self, temp_config_dir: Path) -> None:
        """Explicit overrides take precedence over YAML."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text("llm_model: yaml-model\n")

        config = create_config(
            search_path=temp_config_dir,
            llm_model=TEST_LLM_MODEL,
        )
        assert config.llm_model == TEST_LLM_MODEL

    def test_explicit_path(self, temp_config_dir: Path) -> None:
        """Uses explicit config path."""
        config_file = temp_config_dir / "custom.yml"
        config_file.write_text(f"llm_temperature: {TEST_TEMPERATURE}\n")

        config = create_config(config_path=config_file)
        assert config.llm_temperature == TEST_TEMPERATURE

    def test_multiple_values_from_yaml(self, temp_config_dir: Path) -> None:
        """Loads multiple values from YAML."""
        config_file = temp_config_dir / "config.yml"
        config_file.write_text(
            f"""
llm_model: {TEST_LLM_MODEL}
llm_temperature: {TEST_TEMPERATURE}
server_port: {TEST_SERVER_PORT}
"""
        )

        config = create_config(search_path=temp_config_dir)
        assert config.llm_model == TEST_LLM_MODEL
        assert config.llm_temperature == TEST_TEMPERATURE
        assert config.server_port == TEST_SERVER_PORT


class TestMACSDKConfigValidators:
    """Tests for Pydantic Field validators in MACSDKConfig."""

    def test_temperature_too_high_raises(self) -> None:
        """Temperature above 2.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="llm_temperature"):
            MACSDKConfig(llm_temperature=2.5)

    def test_temperature_negative_raises(self) -> None:
        """Negative temperature raises ValidationError."""
        with pytest.raises(ValidationError, match="llm_temperature"):
            MACSDKConfig(llm_temperature=-0.1)

    def test_temperature_at_boundaries_valid(self) -> None:
        """Temperature at 0.0 and 2.0 are valid."""
        config_min = MACSDKConfig(llm_temperature=0.0)
        config_max = MACSDKConfig(llm_temperature=2.0)
        assert config_min.llm_temperature == 0.0
        assert config_max.llm_temperature == 2.0

    def test_classifier_temperature_too_high_raises(self) -> None:
        """Classifier temperature above 2.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="classifier_temperature"):
            MACSDKConfig(classifier_temperature=2.1)

    def test_server_port_too_high_raises(self) -> None:
        """Port above 65535 raises ValidationError."""
        with pytest.raises(ValidationError, match="server_port"):
            MACSDKConfig(server_port=70000)

    def test_server_port_zero_raises(self) -> None:
        """Port 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="server_port"):
            MACSDKConfig(server_port=0)

    def test_server_port_at_boundaries_valid(self) -> None:
        """Port at 1 and 65535 are valid."""
        config_min = MACSDKConfig(server_port=1)
        config_max = MACSDKConfig(server_port=65535)
        assert config_min.server_port == 1
        assert config_max.server_port == 65535

    def test_message_max_length_zero_raises(self) -> None:
        """Message max length 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="message_max_length"):
            MACSDKConfig(message_max_length=0)

    def test_warmup_timeout_zero_raises(self) -> None:
        """Warmup timeout 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="warmup_timeout"):
            MACSDKConfig(warmup_timeout=0.0)

    def test_summarization_trigger_tokens_zero_raises(self) -> None:
        """Summarization trigger tokens 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="summarization_trigger_tokens"):
            MACSDKConfig(summarization_trigger_tokens=0)

    def test_summarization_keep_messages_zero_raises(self) -> None:
        """Summarization keep messages 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="summarization_keep_messages"):
            MACSDKConfig(summarization_keep_messages=0)

    def test_recursion_limit_zero_raises(self) -> None:
        """Recursion limit 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="recursion_limit"):
            MACSDKConfig(recursion_limit=0)


class TestCreateDefaultConfig:
    """Tests for _create_default_config function."""

    def test_no_config_file_returns_defaults_silently(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When config.yml doesn't exist, returns defaults without warning."""
        with patch("macsdk.core.config.load_config_from_yaml") as mock_load:
            mock_load.side_effect = FileNotFoundError("config.yml not found")

            config = _create_default_config()

            assert config.llm_model == "gemini-2.5-flash"
            assert config.url_security.enabled is False
            # No warning should be logged for missing file
            assert "Failed to load config.yml" not in caplog.text

    def test_invalid_yaml_exits_app(self, caplog: pytest.LogCaptureFixture) -> None:
        """When config.yml is invalid, exits with error message (Fail Closed)."""
        with patch("macsdk.core.config.load_config_from_yaml") as mock_load:
            mock_load.side_effect = ValueError("Invalid YAML syntax")

            import logging

            caplog.set_level(logging.ERROR)

            # Should exit rather than returning insecure defaults
            with pytest.raises(SystemExit) as exc_info:
                _create_default_config()

            assert exc_info.value.code == 1
            assert "Failed to load config.yml" in caplog.text
            assert "Invalid YAML syntax" in caplog.text

    def test_pydantic_validation_error_exits_app(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When config values are invalid, exits with error message (Fail Closed)."""
        with patch("macsdk.core.config.load_config_from_yaml") as mock_load:
            # Return invalid config that will fail Pydantic validation
            mock_load.return_value = {"llm_temperature": 999.0}  # Invalid temp

            import logging

            caplog.set_level(logging.ERROR)

            # Should exit rather than returning insecure defaults
            with pytest.raises(SystemExit) as exc_info:
                _create_default_config()

            assert exc_info.value.code == 1
            assert "Configuration validation failed" in caplog.text

    def test_typo_in_url_security_field_exits_app(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When url_security has typo (e.g. 'ennabled'), exits with error."""
        with patch("macsdk.core.config.load_config_from_yaml") as mock_load:
            # Typo: "ennabled" instead of "enabled"
            mock_load.return_value = {
                "url_security": {"ennabled": True}  # Typo in field name
            }

            import logging

            caplog.set_level(logging.ERROR)

            # Should exit due to extra field not allowed
            with pytest.raises(SystemExit) as exc_info:
                _create_default_config()

            assert exc_info.value.code == 1
            assert "Configuration validation failed" in caplog.text
            # Should mention the problematic field
            assert "url_security" in caplog.text
