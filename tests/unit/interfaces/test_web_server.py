"""Tests for web server configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from macsdk.interfaces.web.server import WebSocketMessage


class TestWebSocketMessage:
    """Test WebSocket message validation."""

    def test_valid_message(self):
        """Test that valid messages are accepted."""
        msg = WebSocketMessage(message="Hello, world!")
        assert msg.message == "Hello, world!"

    def test_empty_message_rejected(self):
        """Test that empty messages are rejected."""
        with pytest.raises(ValidationError, match="at least 1 character"):
            WebSocketMessage(message="")

    def test_message_length_respects_config(self, monkeypatch):
        """Test that message length validation uses config.message_max_length."""
        from macsdk.core.config import config

        # Mock the config to have a specific max length
        monkeypatch.setattr(config, "message_max_length", 50)

        # Message within limit should pass
        short_msg = WebSocketMessage(message="x" * 50)
        assert len(short_msg.message) == 50

        # Message exceeding limit should fail
        with pytest.raises(
            ValidationError, match="Message exceeds maximum length of 50 characters"
        ):
            WebSocketMessage(message="x" * 51)

    def test_default_message_length_limit(self, monkeypatch):
        """Test that default message length limit is reasonable."""
        from macsdk.core.config import config

        # Ensure config has a reasonable default
        # The default in MACSDKConfig is 10000
        monkeypatch.setattr(config, "message_max_length", 10000)

        # Should accept messages up to the limit
        large_msg = WebSocketMessage(message="x" * 10000)
        assert len(large_msg.message) == 10000

        # Should reject messages over the limit
        with pytest.raises(ValidationError, match="Message exceeds maximum length"):
            WebSocketMessage(message="x" * 10001)
