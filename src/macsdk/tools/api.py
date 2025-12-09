"""REST API tools for MACSDK agents.

Generic tools for calling REST APIs with automatic authentication,
retry logic, error handling, SSL certificate support, and optional
JSONPath extraction.
"""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
from typing import Annotated, Any

import aiohttp
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from ..core.api_registry import get_api_service

logger = logging.getLogger(__name__)


def _extract_jsonpath(data: Any, path: str) -> Any:
    """Extract data using JSONPath expression.

    Args:
        data: JSON data to extract from.
        path: JSONPath expression (e.g., "$.items[*].name").

    Returns:
        Extracted data, or original data if extraction fails.
    """
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
        logger.warning(f"JSONPath extraction failed: {e}")
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

    url = f"{service_config.base_url}/{endpoint.lstrip('/')}"

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

    # Configure SSL context
    ssl_context: ssl.SSLContext | bool = True
    if not service_config.ssl_verify:
        # Disable SSL verification (insecure, for test servers)
        ssl_context = False
    elif service_config.ssl_cert:
        # Use custom SSL certificate
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(service_config.ssl_cert)

    # Retry logic with exponential backoff
    last_error = None
    for attempt in range(service_config.max_retries):
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=body if body else None,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=service_config.timeout),
                ) as response:
                    # Try to parse JSON response
                    try:
                        data = await response.json()
                    except (json.JSONDecodeError, aiohttp.ContentTypeError):
                        data = await response.text()

                    if response.status >= 400:
                        return {
                            "success": False,
                            "status_code": response.status,
                            "error": f"HTTP {response.status}: {data}",
                        }

                    # Apply JSONPath extraction if specified
                    if extract and isinstance(data, (dict, list)):
                        data = _extract_jsonpath(data, extract)

                    return {
                        "success": True,
                        "status_code": response.status,
                        "data": data,
                    }

        except aiohttp.ClientError as e:
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


@tool
async def api_get(
    service: str,
    endpoint: str,
    params: dict | None = None,
    extract: str | None = None,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Make a GET request to a registered API service.

    Args:
        service: Name of the registered API service (e.g., "github", "jira").
        endpoint: API endpoint path (e.g., "/repos/owner/repo/issues").
        params: Optional query parameters.
        extract: Optional JSONPath to extract specific fields (e.g., "$.items[*].name").

    Returns:
        JSON response or error message.

    Example:
        >>> api_get("github", "/repos/langchain-ai/langchain/issues",
        ...         params={"state": "open"})
    """
    result = await _make_request(
        "GET", service, endpoint, params=params, extract=extract
    )

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        return f"API Error: {result['error']}"


@tool
async def api_post(
    service: str,
    endpoint: str,
    body: dict,
    params: dict | None = None,
    extract: str | None = None,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Make a POST request to a registered API service.

    Args:
        service: Name of the registered API service.
        endpoint: API endpoint path.
        body: Request body (will be sent as JSON).
        params: Optional query parameters.
        extract: Optional JSONPath to extract specific fields.

    Returns:
        JSON response or error message.
    """
    result = await _make_request(
        "POST", service, endpoint, params=params, body=body, extract=extract
    )

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        return f"API Error: {result['error']}"


@tool
async def api_put(
    service: str,
    endpoint: str,
    body: dict,
    params: dict | None = None,
    extract: str | None = None,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Make a PUT request to a registered API service.

    Args:
        service: Name of the registered API service.
        endpoint: API endpoint path.
        body: Request body (will be sent as JSON).
        params: Optional query parameters.
        extract: Optional JSONPath to extract specific fields.

    Returns:
        JSON response or error message.
    """
    result = await _make_request(
        "PUT", service, endpoint, params=params, body=body, extract=extract
    )

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        return f"API Error: {result['error']}"


@tool
async def api_delete(
    service: str,
    endpoint: str,
    params: dict | None = None,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Make a DELETE request to a registered API service.

    Args:
        service: Name of the registered API service.
        endpoint: API endpoint path.
        params: Optional query parameters.

    Returns:
        JSON response or error message.
    """
    result = await _make_request("DELETE", service, endpoint, params=params)

    if result["success"]:
        if result["data"]:
            return json.dumps(result["data"], indent=2, default=str)
        return "Successfully deleted"
    else:
        return f"API Error: {result['error']}"


@tool
async def api_patch(
    service: str,
    endpoint: str,
    body: dict,
    params: dict | None = None,
    extract: str | None = None,
    config: Annotated[RunnableConfig | None, InjectedToolArg] = None,
) -> str:
    """Make a PATCH request to a registered API service.

    Args:
        service: Name of the registered API service.
        endpoint: API endpoint path.
        body: Partial update body (will be sent as JSON).
        params: Optional query parameters.
        extract: Optional JSONPath to extract specific fields.

    Returns:
        JSON response or error message.
    """
    result = await _make_request(
        "PATCH", service, endpoint, params=params, body=body, extract=extract
    )

    if result["success"]:
        return json.dumps(result["data"], indent=2, default=str)
    else:
        return f"API Error: {result['error']}"
