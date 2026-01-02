"""Unit tests for URL security validation."""

from __future__ import annotations

import pytest

from macsdk.core.url_security import (
    URLSecurityConfig,
    URLSecurityError,
    validate_url,
)


class TestURLSecurityConfig:
    """Tests for URLSecurityConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = URLSecurityConfig()
        assert config.enabled is False
        assert config.allow_domains == []
        assert config.allow_ips == []
        assert config.allow_localhost is False
        assert config.log_blocked_attempts is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["api.github.com", "*.example.com"],
            allow_ips=["203.0.113.0/24"],
            allow_localhost=True,
            log_blocked_attempts=False,
        )
        assert config.enabled is True
        assert len(config.allow_domains) == 2
        assert len(config.allow_ips) == 1
        assert config.allow_localhost is True
        assert config.log_blocked_attempts is False


class TestValidateURLDisabled:
    """Tests for URL validation when security is disabled."""

    def test_any_url_allowed_when_disabled(self):
        """Test that any URL is allowed when security is disabled."""
        config = URLSecurityConfig(enabled=False)

        # Should not raise any exceptions
        validate_url("https://api.github.com/repos", config)
        validate_url("https://internal.corp/api", config)
        validate_url("http://localhost:8080", config)
        validate_url("http://192.168.1.1", config)


class TestValidateURLDomains:
    """Tests for domain validation."""

    def test_exact_domain_match(self):
        """Test exact domain matching."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["api.github.com"],
        )

        # Should pass
        validate_url("https://api.github.com/repos", config)
        validate_url("http://api.github.com/users", config)

        # Should fail
        with pytest.raises(URLSecurityError, match="not in allow list"):
            validate_url("https://github.com", config)

    def test_wildcard_domain_match(self):
        """Test wildcard domain matching."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["*.example.com"],
        )

        # Should pass
        validate_url("https://api.example.com", config)
        validate_url("https://internal.example.com", config)

        # Should fail - doesn't match wildcard
        with pytest.raises(URLSecurityError):
            validate_url("https://example.com", config)

        with pytest.raises(URLSecurityError):
            validate_url("https://other.org", config)

    def test_multiple_domains(self):
        """Test multiple allowed domains."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["api.github.com", "*.example.com", "internal.corp"],
        )

        # All should pass
        validate_url("https://api.github.com/repos", config)
        validate_url("https://web.example.com", config)
        validate_url("https://internal.corp/api", config)

        # Should fail
        with pytest.raises(URLSecurityError):
            validate_url("https://malicious.com", config)

    def test_no_allow_list_blocks_everything(self):
        """Test that empty allow list blocks everything when enabled."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=[],  # Empty list
        )

        with pytest.raises(URLSecurityError, match="no allow list is configured"):
            validate_url("https://api.github.com", config)

    def test_case_insensitive_matching(self):
        """Test that domain matching is case-insensitive."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["API.GitHub.COM"],
        )

        # Should pass with different case
        validate_url("https://api.github.com", config)
        validate_url("https://API.GITHUB.COM", config)


class TestValidateURLIPs:
    """Tests for IP address validation."""

    def test_exact_ip_match(self):
        """Test exact IP matching."""
        config = URLSecurityConfig(
            enabled=True,
            allow_ips=["203.0.113.0/32"],  # Single IP
        )

        # Should pass
        validate_url("http://203.0.113.0:8080", config)

        # Should fail
        with pytest.raises(URLSecurityError):
            validate_url("http://203.0.113.1", config)

    def test_ip_range_cidr(self):
        """Test IP range matching with CIDR notation."""
        config = URLSecurityConfig(
            enabled=True,
            allow_ips=["203.0.113.0/24"],  # Range: 203.0.113.0 - 203.0.113.255
        )

        # Should pass - IPs in range
        validate_url("http://203.0.113.0", config)
        validate_url("http://203.0.113.100", config)
        validate_url("http://203.0.113.255", config)

        # Should fail - IP out of range
        with pytest.raises(URLSecurityError):
            validate_url("http://203.0.114.0", config)

    def test_localhost_blocked_by_default(self):
        """Test that localhost is blocked by default."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["example.com"],  # Has allow list but not localhost
            allow_localhost=False,
        )

        with pytest.raises(URLSecurityError, match="localhost is not allowed"):
            validate_url("http://127.0.0.1", config)

        with pytest.raises(URLSecurityError, match="localhost is not allowed"):
            validate_url("http://localhost", config)

    def test_localhost_allowed_when_configured(self):
        """Test that localhost can be explicitly allowed."""
        config = URLSecurityConfig(
            enabled=True,
            allow_localhost=True,
        )

        # Should pass
        validate_url("http://127.0.0.1:8080", config)
        validate_url("http://localhost:3000", config)

    def test_private_ip_blocked_without_allow_list(self):
        """Test that private IPs are blocked without explicit allow."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["example.com"],
        )

        # Private IPs should be blocked
        with pytest.raises(URLSecurityError, match="Private IP not allowed"):
            validate_url("http://192.168.1.1", config)

        with pytest.raises(URLSecurityError, match="Private IP not allowed"):
            validate_url("http://10.0.0.1", config)

        with pytest.raises(URLSecurityError, match="Private IP not allowed"):
            validate_url("http://172.16.0.1", config)

    def test_private_ip_allowed_in_allow_list(self):
        """Test that private IPs can be explicitly allowed."""
        config = URLSecurityConfig(
            enabled=True,
            allow_ips=["192.168.1.0/24"],
        )

        # Should pass
        validate_url("http://192.168.1.100", config)


class TestValidateURLEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_invalid_url_no_hostname(self):
        """Test that URLs without hostname are rejected."""
        config = URLSecurityConfig(enabled=True, allow_domains=["example.com"])

        with pytest.raises(URLSecurityError, match="Invalid URL"):
            validate_url("not-a-url", config)

    def test_url_with_port(self):
        """Test URLs with ports."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["api.github.com"],
        )

        # Should pass - port doesn't affect domain matching
        validate_url("https://api.github.com:443/repos", config)
        validate_url("https://api.github.com:8080/api", config)

    def test_url_with_path_and_query(self):
        """Test URLs with paths and query strings."""
        config = URLSecurityConfig(
            enabled=True,
            allow_domains=["api.github.com"],
        )

        # Should pass - path and query don't affect validation
        validate_url("https://api.github.com/repos/owner/repo?per_page=10", config)

    def test_ipv6_address(self):
        """Test IPv6 addresses."""
        config = URLSecurityConfig(
            enabled=True,
            allow_ips=["2001:db8::/32"],
        )

        # Should pass
        validate_url("http://[2001:db8::1]", config)

        # Should fail - out of range
        with pytest.raises(URLSecurityError):
            validate_url("http://[2001:db9::1]", config)
