"""URL security validation for MACSDK.

This module provides URL filtering capabilities to prevent unauthorized
access to internal resources (SSRF protection).

Security Limitations:
- DNS Rebinding: This implementation validates the hostname at request time
  but cannot prevent DNS rebinding attacks (time-of-check to time-of-use).
  If strict internal network isolation is required, consider using a custom
  DNS resolver or network-level controls.
- Connection Pooling: HTTP connection reuse may bypass per-request validation
  if the underlying socket is reused for a different target.
"""

from __future__ import annotations

import ipaddress
import logging
from typing import TYPE_CHECKING, Any, Callable, Coroutine
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError
from pydantic.networks import AnyUrl

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class URLSecurityConfig(BaseModel):
    """Configuration for URL filtering and access control.

    Provides allowlist-based filtering for domains and IP addresses
    to prevent Server-Side Request Forgery (SSRF) attacks.

    Attributes:
        enabled: Whether URL filtering is enabled.
        allow_domains: List of allowed domain patterns (supports wildcards).
        allow_ips: List of allowed IP ranges in CIDR notation.
        allow_localhost: Whether to allow localhost/loopback addresses.
        log_blocked_attempts: Whether to log blocked URL attempts.

    Note:
        When `enabled=True` with empty allow lists, all URLs will be blocked
        (deny-all policy). This is the safest default. Configure at least one
        allow list to permit network access.
    """

    enabled: bool = False
    allow_domains: list[str] = Field(default_factory=list)
    allow_ips: list[str] = Field(default_factory=list)
    allow_localhost: bool = False
    log_blocked_attempts: bool = True

    model_config = {"extra": "forbid"}


# Configuration key for RunnableConfig
URL_SECURITY_KEY = "url_security"


class URLSecurityError(Exception):
    """Raised when URL access is blocked by security policy."""

    pass


def _is_ambiguous_ip_format(hostname: str) -> bool:
    """Check if hostname uses ambiguous IP format that could bypass filters.

    Rejects:
    - Decimal notation (2130706433 = 127.0.0.1)
    - Hex notation (0x7f000001 = 127.0.0.1)
    - Octal notation (017700000001 = 127.0.0.1)
    - Shortened IPv4 (127.1 = 127.0.0.1)

    Allows:
    - Full IPv4 with 4 octets (127.0.0.1)
    - IPv6 with colons (::1, 2001:db8::1)
    - Domain names (example.com)

    Args:
        hostname: Hostname to check.

    Returns:
        True if hostname uses ambiguous format.
    """
    # IPv6 addresses contain colons - allow them
    if ":" in hostname:
        return False

    # Check for pure decimal (e.g., "2130706433")
    if hostname.isdigit():
        return True

    # Check for hex notation (e.g., "0x7f000001")
    # Note: urlparse lowercases hostname, so only lowercase check needed
    if hostname.startswith("0x"):
        return True

    # Check for octal notation (e.g., "017700000001")
    if hostname.startswith("0") and len(hostname) > 1 and hostname[1:].isdigit():
        return True

    # Check for shortened or ambiguous IPv4 formats
    if "." in hostname:
        parts = hostname.split(".")

        # First check if ALL parts are numeric - if not, it's a domain name
        all_numeric = all(part.isdigit() for part in parts if part)
        if not all_numeric:
            return False  # It's a domain name like "example.com"

        # Now we know it's numeric - check if it's a valid full IPv4
        if len(parts) != 4:
            return True  # Shortened IPv4 like "127.1"

        # Check for empty parts (e.g., "127..0.1") - always reject
        if any(not part for part in parts):
            return True  # Empty parts are ambiguous/invalid

        # Check each octet
        for part in parts:
            if len(part) > 1 and part[0] == "0":
                return True  # Leading zero (octal notation like "0177.0.0.1")
            if int(part) > 255:
                return True  # Invalid octet value

    return False


def validate_url(url: str, config: URLSecurityConfig) -> None:
    """Validate URL against security policy.

    Uses Pydantic for strict URL validation to prevent bypasses via
    IP shorthands (127.1, 0x7f000001) and other ambiguous formats.

    Args:
        url: URL to validate.
        config: Security configuration.

    Raises:
        URLSecurityError: If URL is not allowed by the security policy.

    Example:
        >>> config = URLSecurityConfig(
        ...     enabled=True,
        ...     allow_domains=["api.github.com", "*.example.com"]
        ... )
        >>> validate_url("https://api.github.com/users", config)  # OK
        >>> validate_url("https://internal.corp/api", config)  # Raises error
    """
    if not config.enabled:
        return

    # First, extract the raw hostname BEFORE Pydantic normalizes it
    # This is critical for detecting ambiguous IP formats
    parsed_raw = urlparse(url)
    raw_hostname = parsed_raw.hostname

    if not raw_hostname:
        raise URLSecurityError(f"Invalid URL (no hostname): {url}")

    # Security hardening: Reject ambiguous IP formats BEFORE any normalization
    # This prevents bypasses like "127.1", "0x7f000001", "2130706433"
    if _is_ambiguous_ip_format(raw_hostname):
        if config.log_blocked_attempts:
            logger.warning(f"Rejected ambiguous numeric hostname: {url}")
        raise URLSecurityError(
            f"Ambiguous numeric hostname rejected for security: {url}"
        )

    # Now use Pydantic for full URL validation
    try:
        pydantic_url = AnyUrl(url)
        hostname = pydantic_url.host
    except ValidationError as e:
        raise URLSecurityError(f"Invalid URL format: {url} ({e})")

    if not hostname:
        raise URLSecurityError(f"Invalid URL (no hostname): {url}")

    # Try to parse as IP address using standard library
    # Note: IPv6 addresses from Pydantic may include brackets, strip them
    hostname_clean = hostname.strip("[]")
    try:
        ip = ipaddress.ip_address(hostname_clean)
        _validate_ip(ip, config, url)
        return
    except ValueError:
        # Not an IP address, treat as domain
        pass

    # It's a domain name
    _validate_domain(hostname, config, url)


def create_redirect_validator(
    config: URLSecurityConfig | None,
) -> Callable[[httpx.Request], Coroutine[Any, Any, None]] | None:
    """Create an event hook to validate redirects against security policy.

    This function returns an async function that can be used as an httpx event hook
    to validate all requests in a chain (including redirects).

    Args:
        config: URL security configuration. If None or disabled, returns None.

    Returns:
        An async function suitable for httpx event_hooks['request'], or None if
        validation is disabled.

    Example:
        >>> validator = create_redirect_validator(security_config)
        >>> if validator:
        ...     event_hooks = {"request": [validator]}
        ... else:
        ...     event_hooks = {}
    """
    if not config or not config.enabled:
        return None

    async def _validate_request(request: httpx.Request) -> None:
        """Validate every request in the chain, including redirects."""
        request_url = str(request.url)
        try:
            validate_url(request_url, config)
        except URLSecurityError as e:
            # Import here to avoid circular dependency
            from langchain_core.tools import ToolException

            raise ToolException(f"Redirect blocked by URL security policy: {e}")

    return _validate_request


def _validate_ip(
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
    config: URLSecurityConfig,
    url: str,
) -> None:
    """Validate IP address against security policy.

    Args:
        ip: IP address to validate.
        config: Security configuration.
        url: Original URL (for error messages).

    Raises:
        URLSecurityError: If IP is not allowed.
    """
    # Check localhost
    if ip.is_loopback:
        if not config.allow_localhost:
            if config.log_blocked_attempts:
                logger.warning(f"Blocked localhost access: {url}")
            raise URLSecurityError(f"Access to localhost is not allowed: {url}")
        return

    # Check private addresses (RFC1918, link-local, etc.)
    if ip.is_private:
        # Private IPs must be explicitly allowed
        if not config.allow_ips:
            if config.log_blocked_attempts:
                logger.warning(f"Blocked private IP access: {url}")
            raise URLSecurityError(f"Private IP not allowed: {url}")

    # Check allow list
    # If allow_ips is configured, IP must be in the list
    # If not configured, block all IPs (safest default)
    if config.allow_ips:
        allowed = False
        for allowed_range in config.allow_ips:
            try:
                # Use strict=False to allow user-friendly CIDR notation
                # e.g., "192.168.1.1/24" instead of requiring "192.168.1.0/24"
                if ip in ipaddress.ip_network(allowed_range, strict=False):
                    allowed = True
                    break
            except ValueError:
                logger.warning(f"Invalid IP range in allow_ips: {allowed_range}")
                continue

        if not allowed:
            if config.log_blocked_attempts:
                logger.warning(f"IP not in allow list: {url}")
            raise URLSecurityError(f"IP address not in allow list: {url}")
    else:
        # No IP allow list configured - block all IPs
        if config.log_blocked_attempts:
            logger.warning(f"No IP allow list configured, blocking: {url}")
        raise URLSecurityError(
            f"IP addresses not allowed (no allow_ips configured): {url}"
        )


def _validate_domain(hostname: str, config: URLSecurityConfig, url: str) -> None:
    """Validate domain name against security policy.

    Args:
        hostname: Domain name to validate.
        config: Security configuration.
        url: Original URL (for error messages).

    Raises:
        URLSecurityError: If domain is not allowed.

    Note:
        Wildcard patterns starting with '*.' match only subdomains, not the
        pattern itself. For example, '*.example.com' matches 'api.example.com'
        but NOT 'example.com'. To allow both, include both patterns:
        ['example.com', '*.example.com']
    """
    # Special handling for localhost hostname
    if hostname.lower() == "localhost":
        if not config.allow_localhost:
            if config.log_blocked_attempts:
                logger.warning(f"Blocked localhost access: {url}")
            raise URLSecurityError(f"Access to localhost is not allowed: {url}")
        return  # Allowed

    # Check allow list (if not empty, filtering is active)
    if config.allow_domains:
        allowed = False
        hostname_lower = hostname.lower()

        for pattern in config.allow_domains:
            pattern_lower = pattern.lower()

            # Handle wildcard subdomain patterns (e.g., "*.example.com")
            if pattern_lower.startswith("*."):
                # Extract suffix (e.g., ".example.com")
                suffix = pattern_lower[1:]  # Remove the '*'
                # Check if hostname ends with the suffix
                # This prevents "evil-example.com" from matching "*.example.com"
                if hostname_lower.endswith(suffix) and hostname_lower != suffix[1:]:
                    # Ensure it's a proper subdomain (has a dot before the suffix)
                    allowed = True
                    break
            # Handle exact matches
            elif hostname_lower == pattern_lower:
                allowed = True
                break

        if not allowed:
            if config.log_blocked_attempts:
                logger.warning(f"Domain not in allow list: {url}")
            raise URLSecurityError(f"Domain not in allow list: {url}")
    else:
        # No allow list configured but filtering is enabled
        # This means: block everything (safest default)
        if config.log_blocked_attempts:
            logger.warning(f"No allow list configured, blocking: {url}")
        raise URLSecurityError(
            f"URL security is enabled but no allow list is configured: {url}"
        )
