"""SSL Certificate management for RAG agent.

This module provides utilities for managing SSL certificates when
crawling documentation from internal/corporate URLs that require
custom CA certificates.

Certificates can be:
- Downloaded from a URL and cached locally
- Loaded from a local file path
- Combined with system certificates for use with requests
"""

from __future__ import annotations

import hashlib
import logging
import ssl
from pathlib import Path
from urllib.parse import urlparse

import certifi

from .config import RAGSourceConfig, get_rag_config

logger = logging.getLogger(__name__)


def _get_cert_cache_dir() -> Path:
    """Get the certificate cache directory, creating it if needed."""
    config = get_rag_config()
    cache_dir = config.cert_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cert_filename(url: str) -> str:
    """Generate a unique filename for a certificate URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"cert_{url_hash}.pem"


def download_certificate(cert_url: str) -> Path | None:
    """Download a certificate from a URL and cache it locally.

    Args:
        cert_url: URL to download the certificate from.

    Returns:
        Path to the cached certificate file, or None if download failed.
    """
    import urllib.request

    cache_dir = _get_cert_cache_dir()
    cert_filename = _get_cert_filename(cert_url)
    cert_path = cache_dir / cert_filename

    # Return cached certificate if it exists
    if cert_path.exists():
        logger.debug(f"Using cached certificate: {cert_path}")
        return cert_path

    logger.info(f"Downloading certificate from {cert_url}")

    try:
        # Create SSL context that doesn't verify (for initial download)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(cert_url, context=ctx) as response:
            cert_data = response.read()

        cert_path.write_bytes(cert_data)
        logger.info(f"Certificate cached at {cert_path}")
        return cert_path

    except Exception as e:
        logger.error(f"Failed to download certificate from {cert_url}: {e}")
        return None


def create_combined_cert_bundle(custom_cert_path: Path) -> Path | None:
    """Create a combined certificate bundle with system + custom certs.

    This is needed because some libraries only accept a single CA bundle file.

    Args:
        custom_cert_path: Path to the custom certificate to add.

    Returns:
        Path to the combined certificate bundle, or None if failed.
    """
    try:
        # Get system certificates
        system_certs = Path(certifi.where()).read_text()

        # Read custom certificate
        custom_cert = custom_cert_path.read_text()

        # Create combined bundle in cache directory
        cache_dir = _get_cert_cache_dir()
        combined_filename = f"combined_{custom_cert_path.stem}.pem"
        combined_path = cache_dir / combined_filename

        combined_path.write_text(system_certs + "\n" + custom_cert)
        logger.debug(f"Created combined cert bundle at {combined_path}")
        return combined_path

    except Exception as e:
        logger.error(f"Failed to create combined cert bundle: {e}")
        return None


def get_cert_for_source(source: RAGSourceConfig) -> Path | None:
    """Get the appropriate certificate for a documentation source.

    This function handles:
    - No certificate (returns None)
    - Local certificate path
    - Remote certificate URL (downloads and caches)

    Args:
        source: The documentation source configuration.

    Returns:
        Path to the certificate file (or combined bundle), or None.
    """
    # No certificate configured
    if not source.cert_url and not source.cert_path:
        return None

    # Local certificate path
    if source.cert_path:
        cert_path = Path(source.cert_path)
        if not cert_path.exists():
            logger.warning(f"Certificate not found: {source.cert_path}")
            return None
        logger.debug(f"Using local certificate: {cert_path}")
        return create_combined_cert_bundle(cert_path)

    # Remote certificate URL
    if source.cert_url:
        downloaded_cert = download_certificate(source.cert_url)
        if downloaded_cert:
            return create_combined_cert_bundle(downloaded_cert)
        return None

    return None


def needs_custom_cert(url: str) -> bool:
    """Check if a URL requires a custom certificate.

    This is a simple heuristic based on the URL domain.
    Internal/corporate domains typically need custom certificates.

    Args:
        url: The URL to check.

    Returns:
        True if the URL likely needs a custom certificate.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Common internal domain patterns
        internal_patterns = [
            ".internal.",
            ".corp.",
            ".local",
            ".intranet",
        ]

        return any(pattern in domain for pattern in internal_patterns)

    except Exception:
        return False
