"""Tests for Pydantic-based URL security validation."""

from __future__ import annotations

import pytest

from macsdk.core.url_security import URLSecurityConfig, URLSecurityError, validate_url


class TestPydanticURLValidation:
    """Test Pydantic's strict URL validation."""

    def test_valid_standard_url(self):
        """Test that standard URLs are validated correctly."""
        config = URLSecurityConfig(enabled=True, allow_domains=["example.com"])
        validate_url("https://example.com/path", config)  # Should pass

    def test_invalid_url_format(self):
        """Test that invalid URL formats are rejected."""
        config = URLSecurityConfig(enabled=True, allow_domains=["example.com"])
        with pytest.raises(URLSecurityError, match="Invalid URL \\(no hostname\\)"):
            validate_url("not-a-url", config)

    def test_ip_shorthand_decimal_rejected(self):
        """Test that decimal IP shorthands like 127.1 are rejected."""
        config = URLSecurityConfig(enabled=True, allow_localhost=False)
        with pytest.raises(URLSecurityError, match="Ambiguous numeric hostname"):
            validate_url("http://127.1/path", config)

    def test_ip_shorthand_hex_rejected(self):
        """Test that hexadecimal IP formats are rejected."""
        config = URLSecurityConfig(enabled=True, allow_localhost=False)
        with pytest.raises(URLSecurityError, match="Ambiguous numeric hostname"):
            validate_url("http://0x7f000001/path", config)

    def test_ip_decimal_notation_rejected(self):
        """Test that decimal IP notation (2130706433 = 127.0.0.1) is rejected."""
        config = URLSecurityConfig(enabled=True, allow_localhost=False)
        with pytest.raises(URLSecurityError, match="Ambiguous numeric hostname"):
            validate_url("http://2130706433/path", config)

    def test_mixed_hex_decimal_format_rejected(self):
        """Test that mixed hex/decimal formats are rejected or fail safe.

        Example: 127.0.0.0x1 should either be caught as ambiguous or
        fail parsing and be treated as invalid domain.
        """
        config = URLSecurityConfig(enabled=True, allow_domains=["example.com"])
        # Should fail: "Ambiguous", "Invalid URL", or "Domain not in allow list"
        with pytest.raises(URLSecurityError):
            validate_url("http://127.0.0.0x1/path", config)

    def test_full_ipv4_allowed_when_configured(self):
        """Test that full IPv4 addresses work when allowed."""
        # Note: 127.0.0.1 is localhost, so we need allow_localhost=True
        config = URLSecurityConfig(
            enabled=True, allow_ips=["127.0.0.1"], allow_localhost=True
        )
        validate_url("http://127.0.0.1/path", config)  # Should pass

    def test_full_ipv6_allowed_when_configured(self):
        """Test that full IPv6 addresses work when allowed."""
        # Note: ::1 is localhost, so we need allow_localhost=True
        config = URLSecurityConfig(
            enabled=True, allow_ips=["::1"], allow_localhost=True
        )
        validate_url("http://[::1]/path", config)  # Should pass

    def test_private_ip_blocked_by_default(self):
        """Test that private IPs are blocked unless explicitly allowed."""
        config = URLSecurityConfig(enabled=True, allow_domains=["example.com"])
        with pytest.raises(URLSecurityError, match="Private IP"):
            validate_url("http://192.168.1.1/path", config)

    def test_localhost_name_blocked_by_default(self):
        """Test that localhost hostname is blocked unless allowed."""
        config = URLSecurityConfig(enabled=True, allow_localhost=False)
        with pytest.raises(URLSecurityError, match="localhost is not allowed"):
            validate_url("http://localhost/path", config)

    def test_localhost_name_allowed_when_configured(self):
        """Test that localhost hostname works when explicitly allowed."""
        config = URLSecurityConfig(enabled=True, allow_localhost=True)
        validate_url("http://localhost/path", config)  # Should pass

    def test_wildcard_domain_matching(self):
        """Test that wildcard domain matching still works."""
        config = URLSecurityConfig(enabled=True, allow_domains=["*.example.com"])
        validate_url("https://api.example.com/path", config)  # Should pass
        validate_url("https://www.example.com/path", config)  # Should pass

    def test_wildcard_domain_not_matching(self):
        """Test that wildcard domains don't match incorrectly."""
        config = URLSecurityConfig(enabled=True, allow_domains=["*.example.com"])
        with pytest.raises(URLSecurityError, match="Domain not in allow list"):
            # Should fail (no subdomain)
            validate_url("https://example.com/path", config)

    def test_wildcard_prevents_evil_domain_bypass(self):
        """Test that wildcard doesn't allow evil-example.com with *.example.com.

        This is a critical security test. Using fnmatch would allow
        'evil-example.com' to match '*.example.com', which is a bypass.
        """
        config = URLSecurityConfig(enabled=True, allow_domains=["*.example.com"])
        # Should NOT match - this is the critical security test
        with pytest.raises(URLSecurityError, match="Domain not in allow list"):
            validate_url("https://evil-example.com/path", config)

        # But legitimate subdomains should still work
        validate_url("https://api.example.com/path", config)  # Should pass

    def test_cidr_range_matching(self):
        """Test that CIDR ranges work correctly."""
        config = URLSecurityConfig(enabled=True, allow_ips=["192.168.1.0/24"])
        validate_url("http://192.168.1.100/path", config)  # Should pass

    def test_cidr_with_host_bits_allowed(self):
        """Test that CIDR notation with host bits set is accepted (strict=False).

        Users often provide IPs like 192.168.1.1/24 instead of 192.168.1.0/24.
        We use strict=False to be user-friendly.
        """
        config = URLSecurityConfig(enabled=True, allow_ips=["192.168.1.1/24"])
        # Should allow any IP in the 192.168.1.0/24 range
        validate_url("http://192.168.1.100/path", config)  # Should pass
        validate_url("http://192.168.1.1/path", config)  # Should pass

    def test_cidr_range_not_matching(self):
        """Test that IPs outside CIDR range are blocked."""
        config = URLSecurityConfig(enabled=True, allow_ips=["192.168.1.0/24"])
        with pytest.raises(URLSecurityError, match="IP address not in allow list"):
            validate_url("http://192.168.2.100/path", config)  # Should fail

    def test_ipv6_cidr_matching(self):
        """Test that IPv6 CIDR ranges work correctly."""
        config = URLSecurityConfig(enabled=True, allow_ips=["2001:db8::/32"])
        validate_url("http://[2001:db8::1]/path", config)  # Should pass

    def test_disabled_security_allows_all(self):
        """Test that disabled security allows all URLs."""
        config = URLSecurityConfig(enabled=False)
        # All of these should pass
        validate_url("http://127.1/path", config)
        validate_url("http://0x7f000001/path", config)
        validate_url("http://localhost/path", config)
        validate_url("http://192.168.1.1/path", config)
