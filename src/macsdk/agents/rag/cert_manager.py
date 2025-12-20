"""SSL Certificate management for RAG agent.

This module provides utilities for managing SSL certificates when
crawling documentation from internal/corporate URLs that require
custom CA certificates.

Features:
- Download and cache certificates from URLs
- Load certificates from local file paths
- Create combined certificate bundles (system + custom certs)

Note: The combined bundle is necessary for libraries like `requests`
that replace (rather than extend) system certificates when given a custom cert.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

import certifi

from macsdk.core.cert_manager import get_certificate_path

from .config import RAGSourceConfig, get_rag_config

logger = logging.getLogger(__name__)


def _get_cert_cache_dir() -> Path:
    """Get the certificate cache directory for combined certificate bundles.

    Returns:
        Path to the cache directory (creates it if needed).
    """
    config = get_rag_config()
    cache_dir = config.cert_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_certificate_sync(cert_spec: str) -> Path | None:
    """Get a certificate from a URL or local path (synchronous).

    Handles both remote certificate URLs (downloads and caches) and
    local file paths (validates existence).

    Note: Uses asyncio.run() to bridge async core functionality. This is safe
    because the RAG indexer calls this from within a ThreadPoolExecutor,
    not from an active event loop.

    Args:
        cert_spec: Either a URL (http/https) or local file path.

    Returns:
        Path to the certificate file, or None if failed.

    Raises:
        RuntimeError: If called from within an active event loop. This indicates
                      incorrect usage - this function must be called from a
                      synchronous context (e.g., ThreadPoolExecutor).
    """
    try:
        cert_path_str = asyncio.run(get_certificate_path(cert_spec))
        return Path(cert_path_str)
    except RuntimeError as e:
        # Catch event loop conflicts with a clear error message
        if "cannot be called from a running event loop" in str(e):
            logger.error(
                f"Certificate retrieval failed: {e}. "
                "This function cannot be called from an async context. "
                "Ensure RAG indexer runs certificate operations "
                "in a ThreadPoolExecutor."
            )
            raise RuntimeError(
                "Certificate manager cannot be called from an active event loop. "
                "This is a programming error - the RAG indexer must call "
                "certificate operations from a ThreadPoolExecutor, "
                "not from the main event loop."
            ) from e
        # Other RuntimeErrors should be re-raised
        raise
    except (ValueError, FileNotFoundError) as e:
        # Certificate URL invalid or local file not found
        logger.error(f"Certificate error for {cert_spec}: {e}")
        return None
    except Exception as e:
        # Unexpected error (network issues, etc.)
        logger.error(f"Unexpected error getting certificate from {cert_spec}: {e}")
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
    """Get the appropriate certificate bundle for a documentation source.

    Handles both local certificate paths and remote URLs. The certificate
    is combined with system certificates to create a bundle that works with
    both public and internal/corporate sites.

    Configuration precedence (for backward compatibility):
    1. cert_path (local file) takes precedence
    2. cert_url (remote download) is used if cert_path is not set

    Args:
        source: The documentation source configuration.

    Returns:
        Path to the combined certificate bundle, or None if no cert configured.
    """
    # Preserve precedence: local path overrides URL (backward compatibility)
    cert_spec = source.cert_path or source.cert_url
    if not cert_spec:
        # No certificate configured
        return None

    logger.info(f"Getting certificate for source '{source.name}': {cert_spec}")

    # Get certificate (download if URL, validate if local path)
    cert_path = _get_certificate_sync(cert_spec)
    if not cert_path:
        logger.error(f"Failed to get certificate for source '{source.name}'")
        return None

    # Combine with system certificates for compatibility with requests library
    combined_bundle = create_combined_cert_bundle(cert_path)
    if combined_bundle:
        logger.info(
            f"Created combined certificate bundle for '{source.name}': "
            f"{combined_bundle}"
        )
    return combined_bundle


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
