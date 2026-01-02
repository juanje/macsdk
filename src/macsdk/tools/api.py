"""REST API tools for MACSDK agents.

Generic tools for calling REST APIs with automatic authentication,
retry logic, error handling, and SSL certificate support.

Public tools (api_get, api_post, etc.) are designed for LLM use.
For programmatic use with JSONPath extraction, use make_api_request().
"""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
from typing import Any

import httpx
from langchain_core.tools import ToolException, tool

from ..core.api_registry import get_api_service
from ..core.cert_manager import get_certificate_path
from ..core.url_security import (
    URLSecurityError,
    create_redirect_validator,
    validate_url,
)

logger = logging.getLogger(__name__)


def _extract_jsonpath(data: Any, path: str) -> Any:
    """Extract data using JSONPath expression.

    Args:
        data: JSON data to extract from.
        path: JSONPath expression (e.g., "$.items[*].name").

    Returns:
        Extracted data, or original data if extraction fails.
    """
    # Validate that path looks like a JSONPath expression
    # JSONPath must start with $ or contain typical patterns
    if not path or not isinstance(path, str):
        return data

    path = path.strip()

    # Skip if it doesn't look like JSONPath (likely a mistake by LLM)
    if not path.startswith("$") and not path.startswith("@"):
        logger.debug(f"Skipping invalid JSONPath (must start with $ or @): {path}")
        return data

    try:
        from jsonpath_ng import parse

        expr = parse(path)
        matches = [match.value for match in expr.find(data)]

        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            return matches
    except Exception as e:
        logger.debug(f"JSONPath extraction failed for '{path}': {e}")
        return data


async def _make_request(
    method: str,
    service: str,
    endpoint: str,
    params: dict | None = None,
    body: dict | None = None,
    headers: dict | None = None,
    extract: str | None = None,
) -> dict[str, Any]:
    """Internal function to make HTTP requests with retry logic.

    URL security validation is performed using the global configuration.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH).
        service: Registered service name.
        endpoint: API endpoint path.
        params: Query parameters.
        body: Request body (JSON).
        headers: Additional headers.
        extract: Optional JSONPath expression for extraction.

    Returns:
        Dictionary with success status and data or error.
    """
    try:
        service_config = get_api_service(service)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # HttpUrl may add trailing slash to root domains, strip it to avoid double-slash
    url = f"{str(service_config.base_url).rstrip('/')}/{endpoint.lstrip('/')}"

    # Validate URL against security policy (uses global config)
    from ..core.config import config as app_config

    if app_config.url_security.enabled:
        try:
            validate_url(url, app_config.url_security)
        except URLSecurityError as e:
            return {"success": False, "error": str(e)}

    # Build headers
    request_headers = dict(service_config.headers)
    if service_config.token:
        request_headers["Authorization"] = (
            f"Bearer {service_config.token.get_secret_value()}"
        )
    if headers:
        request_headers.update(headers)
    if body:
        request_headers.setdefault("Content-Type", "application/json")

    # Configure SSL verification
    verify: bool | str | ssl.SSLContext = True
    if not service_config.ssl_verify:
        # Disable SSL verification (insecure, for test servers)
        verify = False
    elif service_config.ssl_cert:
        # Use custom SSL certificate (local path or URL)
        try:
            cert_path = await get_certificate_path(service_config.ssl_cert)
            verify = cert_path
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Failed to load SSL certificate: {e}")
            return {
                "success": False,
                "error": f"SSL certificate error: {e}",
            }
        except Exception as e:
            logger.error(f"Unexpected error loading SSL certificate: {e}")
            return {
                "success": False,
                "error": f"SSL certificate error: {e}",
            }

    # Configure event hooks to validate redirects
    validator = create_redirect_validator(app_config.url_security)
    event_hooks = {"request": [validator]} if validator else {}

    # Retry logic with exponential backoff
    # Create client outside retry loop for connection pooling
    last_error = None
    async with httpx.AsyncClient(
        verify=verify,
        timeout=service_config.timeout,
        follow_redirects=True,
        event_hooks=event_hooks,
    ) as client:
        for attempt in range(service_config.max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=body if body else None,
                    headers=request_headers,
                )

                # Try to parse JSON response
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError):
                    data = response.text

                if response.status_code >= 400:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}: {data}",
                    }

                # Apply JSONPath extraction if specified
                if extract and isinstance(data, (dict, list)):
                    data = _extract_jsonpath(data, extract)

                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": data,
                }

            except httpx.HTTPError as e:
                last_error = str(e)
                if attempt < service_config.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
            except Exception as e:
                last_error = str(e)
                break

    retries = service_config.max_retries
    return {
        "success": False,
        "error": f"Request failed after {retries} attempts: {last_error}",
    }


async def make_api_request(
    method: str,
    service: str,
    endpoint: str,
    params: dict | None = None,
    body: dict | None = None,
    headers: dict | None = None,
    extract: str | None = None,
) -> dict[str, Any]:
    """Make an API request with optional JSONPath extraction.

    This is the programmatic interface for developers who need JSONPath
    extraction. For LLM-facing tools, use api_get, api_post, etc.

    URL security validation is performed automatically using the global
    configuration (macsdk.core.config.config).

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH).
        service: Registered service name.
        endpoint: API endpoint path (without query string).
        params: Query parameters as dict.
        body: Request body (for POST, PUT, PATCH).
        headers: Additional headers.
        extract: JSONPath expression to extract specific fields (e.g., "$[*].name").

    Returns:
        Dictionary with keys: success (bool), data (if success), error (if failed).

    Example:
        >>> result = await make_api_request(
        ...     "GET", "devops", "/services",
        ...     extract="$[*].name"
        ... )
        >>> if result["success"]:
        ...     print(result["data"])  # ["web-frontend", "api-gateway", ...]
    """
    return await _make_request(
        method,
        service,
        endpoint,
        params=params,
        body=body,
        headers=headers,
        extract=extract,
    )


@tool
async def api_get(
    service: str,
    endpoint: str,
    params: dict | None = None,
) -> str:
    """Make a GET request to a registered API service.

    Args:
        service: Name of the registered API service (e.g., "github", "devops").
        endpoint: API endpoint path WITHOUT query string (e.g., "/users", "/repos/1").
            Do NOT include query parameters here - use params instead.
        params: Query parameters as a dictionary (e.g., {"status": "failed"}).
            All filters and query options go here, not in the endpoint.

    Returns:
        JSON response data.

    Raises:
        ToolException: If the API request fails.

    Example:
        >>> api_get("github", "/repos/langchain-ai/langchain/issues",
        ...         params={"state": "open", "per_page": 5})
    """
    result = await _make_request("GET", service, endpoint, params=params)

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        raise ToolException(
            f"API request to '{service}' failed: {result['error']}. "
            "This is a tool/connection error, not data from the API."
        )


@tool
async def api_post(
    service: str,
    endpoint: str,
    body: dict,
    params: dict | None = None,
) -> str:
    """Make a POST request to a registered API service.

    Args:
        service: Name of the registered API service (e.g., "github", "devops").
        endpoint: API endpoint path WITHOUT query string (e.g., "/users", "/items").
        body: Request body as a dictionary (will be sent as JSON).
        params: Query parameters as a dictionary. Do NOT put these in the endpoint.

    Returns:
        JSON response data.

    Raises:
        ToolException: If the API request fails.
    """
    result = await _make_request("POST", service, endpoint, params=params, body=body)

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        raise ToolException(f"API POST to '{service}' failed: {result['error']}")


@tool
async def api_put(
    service: str,
    endpoint: str,
    body: dict,
    params: dict | None = None,
) -> str:
    """Make a PUT request to replace a resource in a registered API service.

    Args:
        service: Name of the registered API service (e.g., "github", "devops").
        endpoint: API endpoint path WITHOUT query string (e.g., "/users/1").
        body: Complete resource data as a dictionary (will be sent as JSON).
        params: Query parameters as a dictionary. Do NOT put these in the endpoint.

    Returns:
        JSON response data.

    Raises:
        ToolException: If the API request fails.
    """
    result = await _make_request("PUT", service, endpoint, params=params, body=body)

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        raise ToolException(f"API PUT to '{service}' failed: {result['error']}")


@tool
async def api_delete(
    service: str,
    endpoint: str,
    params: dict | None = None,
) -> str:
    """Make a DELETE request to remove a resource from a registered API service.

    Args:
        service: Name of the registered API service (e.g., "github", "devops").
        endpoint: API endpoint path WITHOUT query string (e.g., "/users/1").
        params: Query parameters as a dictionary. Do NOT put these in the endpoint.

    Returns:
        Success message or response data.

    Raises:
        ToolException: If the API request fails.
    """
    result = await _make_request("DELETE", service, endpoint, params=params)

    if result["success"]:
        if result["data"]:
            return json.dumps(result["data"], indent=2, default=str)
        return "Successfully deleted"
    else:
        raise ToolException(f"API DELETE to '{service}' failed: {result['error']}")


@tool
async def api_patch(
    service: str,
    endpoint: str,
    body: dict,
    params: dict | None = None,
) -> str:
    """Make a PATCH request to partially update a resource in a registered API service.

    Args:
        service: Name of the registered API service (e.g., "github", "devops").
        endpoint: API endpoint path WITHOUT query string (e.g., "/users/1").
        body: Partial update data as a dictionary (only fields to update).
        params: Query parameters as a dictionary. Do NOT put these in the endpoint.

    Returns:
        JSON response data.

    Raises:
        ToolException: If the API request fails.
    """
    result = await _make_request("PATCH", service, endpoint, params=params, body=body)

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        raise ToolException(f"API PATCH to '{service}' failed: {result['error']}")
