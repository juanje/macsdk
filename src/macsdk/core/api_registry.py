"""API Service Registry for MACSDK.

This module provides a registry for managing API service configurations.
Each service has its own base URL, authentication, retry settings, and
rate limits, allowing agents to interact with multiple APIs without
knowing the implementation details.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr

logger = logging.getLogger(__name__)

# Global registry of API services
_api_services: dict[str, "APIServiceConfig"] = {}


class APIServiceConfig(BaseModel):
    """Configuration for a single API service."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    base_url: HttpUrl
    token: SecretStr | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: int = Field(default=30, gt=0)
    max_retries: int = Field(default=3, ge=0)
    rate_limit: int | None = Field(default=None, gt=0)
    ssl_cert: str | None = None  # Path to SSL certificate file
    ssl_verify: bool = True  # Set to False to disable SSL verification (insecure!)


def register_api_service(
    name: str,
    base_url: str,
    token: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    rate_limit: int | None = None,
    ssl_cert: str | None = None,
    ssl_verify: bool = True,
) -> None:
    """Register an API service for use by API tools.

    Args:
        name: Service identifier (e.g., "github", "jira").
        base_url: Base URL for the API.
        token: Optional bearer token for authentication.
        headers: Optional additional headers.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        rate_limit: Optional rate limit (requests per hour).
        ssl_cert: Optional path or URL to SSL certificate file for HTTPS verification.
                  If URL (http/https), certificate will be downloaded and cached
                  locally.
        ssl_verify: Whether to verify SSL certificates (default: True).
                    Set to False for test servers (insecure!).

    Example:
        >>> # Basic service with token
        >>> register_api_service(
        ...     "github",
        ...     "https://api.github.com",
        ...     token=os.environ["GITHUB_TOKEN"],
        ...     rate_limit=5000,
        ... )
        >>> # With local SSL certificate file
        >>> register_api_service(
        ...     "internal_api",
        ...     "https://api.internal.company.com",
        ...     token=os.environ["INTERNAL_TOKEN"],
        ...     ssl_cert="/path/to/company-ca.pem",
        ... )
        >>> # With remote SSL certificate (will be downloaded and cached)
        >>> register_api_service(
        ...     "corporate_api",
        ...     "https://api.internal.company.com",
        ...     token=os.environ["INTERNAL_TOKEN"],
        ...     ssl_cert="https://certs.company.com/corporate-ca.pem",
        ... )
        >>> # Test server without SSL verification (insecure!)
        >>> register_api_service(
        ...     "test_api",
        ...     "https://test.local:8443",
        ...     ssl_verify=False,
        ... )
    """
    if not ssl_verify:
        logger.warning(f"SSL verification disabled for service '{name}' - INSECURE!")

    # Normalize URL (remove trailing slash)
    normalized_url = base_url.rstrip("/")
    _api_services[name] = APIServiceConfig(
        name=name,
        base_url=HttpUrl(normalized_url),
        token=SecretStr(token) if token else None,
        headers=headers or {},
        timeout=timeout,
        max_retries=max_retries,
        rate_limit=rate_limit,
        ssl_cert=ssl_cert,
        ssl_verify=ssl_verify,
    )
    logger.info(f"Registered API service: {name} ({normalized_url})")


def get_api_service(name: str) -> APIServiceConfig:
    """Get registered service configuration.

    Args:
        name: Service identifier.

    Returns:
        APIServiceConfig for the service.

    Raises:
        ValueError: If service is not registered.
    """
    if name not in _api_services:
        available = list(_api_services.keys())
        raise ValueError(f"Unknown service '{name}'. Available: {available}")
    return _api_services[name]


def list_api_services() -> list[str]:
    """List all registered API service names.

    Returns:
        List of registered service names.
    """
    return list(_api_services.keys())


def clear_api_services() -> None:
    """Clear all registered API services.

    Useful for testing or reconfiguration.
    """
    _api_services.clear()
    logger.info("Cleared all API services")


def load_api_services_from_config(config: dict[str, Any]) -> None:
    """Load API services from configuration dictionary.

    This function loads services from the `api_services` section
    of config.yml.

    Args:
        config: Configuration dictionary with `api_services` key.

    Example config.yml:
        api_services:
          github:
            base_url: "https://api.github.com"
            token: ${GITHUB_TOKEN}
            rate_limit: 5000
          jira:
            base_url: "https://company.atlassian.net/rest/api/3"
            token: ${JIRA_TOKEN}
          internal:
            base_url: "https://api.internal.company.com"
            token: ${INTERNAL_TOKEN}
            ssl_cert: "/path/to/company-ca.pem"  # Local path
          corporate:
            base_url: "https://api.corporate.company.com"
            token: ${CORPORATE_TOKEN}
            ssl_cert: "https://certs.company.com/ca.pem"  # Remote URL (downloaded)
          test_server:
            base_url: "https://test.local:8443"
            ssl_verify: false  # Disable SSL verification (insecure!)
    """
    services = config.get("api_services", {})

    for name, service_config in services.items():
        if isinstance(service_config, dict):
            register_api_service(
                name=name,
                base_url=service_config.get("base_url", ""),
                token=service_config.get("token"),
                headers=service_config.get("headers", {}),
                timeout=service_config.get("timeout", 30),
                max_retries=service_config.get("max_retries", 3),
                rate_limit=service_config.get("rate_limit"),
                ssl_cert=service_config.get("ssl_cert"),
                ssl_verify=service_config.get("ssl_verify", True),
            )
