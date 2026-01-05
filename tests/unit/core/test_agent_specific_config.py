"""Tests for agent-specific configuration."""

from __future__ import annotations

from macsdk.core import MACSDKConfig


def test_agent_specific_config_as_dict() -> None:
    """Test agent-specific configuration loaded as dict."""
    config = MACSDKConfig(
        api_agent={"custom_setting": "value"},  # type: ignore[call-arg]
    )

    # Agent-specific setting
    agent_config = getattr(config, "api_agent", {})
    assert isinstance(agent_config, dict)
    assert agent_config["custom_setting"] == "value"


def test_agent_config_with_multiple_settings() -> None:
    """Test multiple agent-specific configurations."""
    config = MACSDKConfig(
        monitoring_agent={"timeout": 30},  # type: ignore[call-arg]
        debug_agent={"verbose": True},  # type: ignore[call-arg]
    )

    # Check agent-specific settings
    monitoring_config = getattr(config, "monitoring_agent", {})
    assert monitoring_config["timeout"] == 30

    debug_config = getattr(config, "debug_agent", {})
    assert debug_config["verbose"] is True


def test_agent_without_config_returns_empty_dict() -> None:
    """Test that agents without config return empty dict."""
    config = MACSDKConfig()

    # Agent without specific config should not exist
    agent_config = getattr(config, "nonexistent_agent", {})
    assert agent_config == {}


def test_agent_config_extra_allow() -> None:
    """Test that extra='allow' enables arbitrary agent configs."""
    config = MACSDKConfig(
        custom_agent={"api_key": "secret", "base_url": "https://api.example.com"},  # type: ignore[call-arg]
    )

    # Agent config accessible via getattr
    agent_config = getattr(config, "custom_agent", {})
    assert agent_config["api_key"] == "secret"
    assert agent_config["base_url"] == "https://api.example.com"
