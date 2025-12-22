"""Tests for agent-specific configuration."""

from __future__ import annotations

from macsdk.core import MACSDKConfig


def test_global_enable_todo_config() -> None:
    """Test global enable_todo configuration (for supervisor)."""
    config = MACSDKConfig(enable_todo=True)
    assert config.enable_todo is True


def test_agent_specific_config_as_dict() -> None:
    """Test agent-specific configuration loaded as dict."""
    config = MACSDKConfig(
        enable_todo=True,  # Global setting (supervisor only)
        api_agent={"enable_todo": True},  # type: ignore[call-arg]
    )

    # Global setting (for supervisor)
    assert config.enable_todo is True

    # Agent-specific setting
    agent_config = getattr(config, "api_agent", {})
    assert isinstance(agent_config, dict)
    assert agent_config["enable_todo"] is True


def test_agent_config_independent_from_global() -> None:
    """Test that agents don't inherit global enable_todo."""
    config = MACSDKConfig(
        enable_todo=True,  # Global: enabled (supervisor only)
        monitoring_agent={"enable_todo": False},  # type: ignore[call-arg]
        debug_agent={"enable_todo": True},  # type: ignore[call-arg]
    )

    # Check global (supervisor)
    assert config.enable_todo is True

    # Check agent-specific settings
    monitoring_config = getattr(config, "monitoring_agent", {})
    assert monitoring_config["enable_todo"] is False

    debug_config = getattr(config, "debug_agent", {})
    assert debug_config["enable_todo"] is True


def test_agent_without_config_uses_default_false() -> None:
    """Test that agents without config use False (not global)."""
    config = MACSDKConfig(enable_todo=True)

    # Agent without specific config should not exist
    agent_config = getattr(config, "nonexistent_agent", {})
    assert agent_config == {}

    # Global is True (for supervisor)
    assert config.enable_todo is True

    # But agents without explicit config default to False
    # (this is tested in agent code, not in config)


def test_agent_explicit_enable() -> None:
    """Test that agents can explicitly enable task planning."""
    config = MACSDKConfig(
        enable_todo=False,  # Supervisor disabled
        complex_agent={"enable_todo": True},  # type: ignore[call-arg]
    )

    # Supervisor setting
    assert config.enable_todo is False

    # Agent explicitly enabled
    agent_config = getattr(config, "complex_agent", {})
    assert agent_config["enable_todo"] is True
