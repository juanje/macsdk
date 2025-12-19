"""Certificate manager for handling local and remote SSL certificates.

This module provides utilities to download, cache, and manage SSL certificates
from remote URLs, making it easier to work with corporate certificate servers.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import httpx

logger = logging.getLogger(__name__)

# Default cache directory for downloaded certificates
_CACHE_DIR = Path.home() / ".cache" / "macsdk" / "certs"

# Lock dictionary to prevent concurrent downloads of the same certificate
_download_locks: dict[str, asyncio.Lock] = {}


def _is_url(path: str) -> bool:
    """Check if a path is a URL (http or https).

    Args:
        path: Path or URL string to check.

    Returns:
        True if path is a URL, False otherwise.
    """
    try:
        result = urlparse(path)
        return result.scheme in ("http", "https")
    except Exception:
        return False


def _get_cache_path(url: str) -> Path:
    """Get the cache path for a certificate URL.

    Uses SHA256 hash of URL to create a unique filename.

    Args:
        url: Certificate URL.

    Returns:
        Path to cached certificate file.
    """
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    # Extract hostname for readability
    parsed = urlparse(url)
    hostname = parsed.hostname or "unknown"
    filename = f"{hostname}_{url_hash}.pem"
    return _CACHE_DIR / filename


def _validate_cert_content(content: str) -> bool:
    """Validate that content looks like a PEM certificate.

    Args:
        content: Certificate content to validate.

    Returns:
        True if content looks like a valid PEM certificate.
    """
    content = content.strip()
    return (
        "-----BEGIN CERTIFICATE-----" in content
        and "-----END CERTIFICATE-----" in content
    ) or (
        "-----BEGIN TRUSTED CERTIFICATE-----" in content
        and "-----END TRUSTED CERTIFICATE-----" in content
    )


async def download_certificate(url: str, force_refresh: bool = False) -> Path:
    """Download a certificate from a URL and cache it locally.

    The certificate is downloaded using the system's default SSL context
    (trusted CAs), so the server hosting the certificate must have a
    valid SSL certificate.

    This function uses per-URL locking to prevent race conditions when
    multiple concurrent requests attempt to download the same certificate.

    Args:
        url: URL to download the certificate from.
        force_refresh: If True, re-download even if cached.

    Returns:
        Path to the cached certificate file.

    Raises:
        ValueError: If the URL is invalid or content is not a certificate.
        httpx.HTTPError: If download fails.

    Example:
        >>> # Download corporate CA certificate
        >>> cert_path = await download_certificate(
        ...     "https://certs.company.com/corporate-ca.pem"
        ... )
        >>> # Use with API service
        >>> register_api_service(
        ...     "internal_api",
        ...     "https://api.internal.company.com",
        ...     ssl_cert=str(cert_path),
        ... )
    """
    if not _is_url(url):
        raise ValueError(f"Invalid URL: {url}")

    cache_path = _get_cache_path(url)

    # Get or create a lock for this URL to prevent concurrent downloads
    if url not in _download_locks:
        _download_locks[url] = asyncio.Lock()

    async with _download_locks[url]:
        # Check again if cached after acquiring lock
        # (another task may have downloaded it)
        # Use to_thread to avoid blocking event loop
        cache_exists = await asyncio.to_thread(cache_path.exists)
        if cache_exists and not force_refresh:
            logger.debug(f"Using cached certificate from {cache_path}")
            return cache_path

        logger.info(f"Downloading certificate from {url}")

        # Ensure cache directory exists (non-blocking)
        await asyncio.to_thread(_CACHE_DIR.mkdir, parents=True, exist_ok=True)

        # Download certificate using system SSL context
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text

        # Validate content
        if not _validate_cert_content(content):
            raise ValueError(
                f"Downloaded content from {url} does not appear to be a "
                "valid certificate"
            )

        # Save to cache asynchronously
        async with aiofiles.open(cache_path, mode="w", encoding="utf-8") as f:
            await f.write(content)

        logger.info(f"Certificate cached at {cache_path}")

        return cache_path


async def get_certificate_path(cert_spec: str, force_refresh: bool = False) -> str:
    """Get the path to a certificate, downloading if it's a URL.

    This is the main entry point for handling both local paths and URLs.

    Args:
        cert_spec: Either a local file path or a URL (http/https).
        force_refresh: If cert_spec is a URL, force re-download.

    Returns:
        Local file path to the certificate.

    Raises:
        ValueError: If URL is invalid or content is not a certificate.
        httpx.HTTPError: If download fails.
        FileNotFoundError: If local path doesn't exist.

    Example:
        >>> # URL - will download and cache
        >>> path = await get_certificate_path(
        ...     "https://certs.company.com/ca.pem"
        ... )
        >>> # Local path - returns as-is after validation
        >>> path = await get_certificate_path("/etc/ssl/certs/my-ca.pem")
    """
    if _is_url(cert_spec):
        # Download and cache
        cache_path = await download_certificate(cert_spec, force_refresh=force_refresh)
        return str(cache_path)
    else:
        # Local path - verify it exists (non-blocking)
        cert_path = Path(cert_spec)
        path_exists = await asyncio.to_thread(cert_path.exists)
        if not path_exists:
            raise FileNotFoundError(f"Certificate file not found: {cert_spec}")
        return cert_spec


def clear_certificate_cache() -> None:
    """Clear all cached certificates.

    Useful for testing or forcing certificate refresh.
    """
    if _CACHE_DIR.exists():
        for cert_file in _CACHE_DIR.glob("*.pem"):
            cert_file.unlink()
        logger.info(f"Cleared certificate cache at {_CACHE_DIR}")


def set_cache_directory(path: Path | str) -> None:
    """Set custom cache directory for certificates.

    Args:
        path: Path to cache directory.
    """
    global _CACHE_DIR
    _CACHE_DIR = Path(path)
    logger.info(f"Certificate cache directory set to {_CACHE_DIR}")
