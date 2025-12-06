"""Tests for MACSDK configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from macsdk.core.config import (
    CONFIG_FILE_ENV_VAR,
    DEFAULT_CONFIG_FILE,
    ConfigurationError,
    MACSDKConfig,
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
