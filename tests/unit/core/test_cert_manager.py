"""Unit tests for certificate manager."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from macsdk.core.cert_manager import (
    _get_cache_path,
    _is_url,
    _validate_cert_content,
    clear_certificate_cache,
    download_certificate,
    get_certificate_path,
    set_cache_directory,
)

# Sample certificate content for testing
VALID_CERT = """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAKHHCgVZU6KyMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBnRl
c3RjYTAeFw0yMTAxMDEwMDAwMDBaFw0yMjAxMDEwMDAwMDBaMBExDzANBgNVBAMM
BnRlc3RjYTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAw0Dm4sBN8KZQxzQR
-----END CERTIFICATE-----"""

INVALID_CERT = """This is not a certificate"""


class TestIsUrl:
    """Tests for URL detection."""

    def test_http_url(self):
        """Test HTTP URL detection."""
        assert _is_url("http://example.com/cert.pem")

    def test_https_url(self):
        """Test HTTPS URL detection."""
        assert _is_url("https://example.com/cert.pem")

    def test_local_path(self):
        """Test local path is not detected as URL."""
        assert not _is_url("/path/to/cert.pem")

    def test_relative_path(self):
        """Test relative path is not detected as URL."""
        assert not _is_url("./cert.pem")

    def test_ftp_url(self):
        """Test FTP URL is not considered valid."""
        assert not _is_url("ftp://example.com/cert.pem")


class TestValidateCertContent:
    """Tests for certificate content validation."""

    def test_valid_certificate(self):
        """Test valid PEM certificate."""
        assert _validate_cert_content(VALID_CERT)

    def test_valid_trusted_certificate(self):
        """Test valid trusted certificate format."""
        trusted_cert = """-----BEGIN TRUSTED CERTIFICATE-----
MIIBkTCB+wIJAKHHCgVZU6KyMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBnRl
-----END TRUSTED CERTIFICATE-----"""
        assert _validate_cert_content(trusted_cert)

    def test_invalid_content(self):
        """Test invalid certificate content."""
        assert not _validate_cert_content(INVALID_CERT)

    def test_empty_content(self):
        """Test empty content."""
        assert not _validate_cert_content("")


class TestGetCachePath:
    """Tests for cache path generation."""

    def test_cache_path_generation(self):
        """Test cache path is generated correctly."""
        url = "https://certs.example.com/ca.pem"
        cache_path = _get_cache_path(url)

        assert isinstance(cache_path, Path)
        assert cache_path.name.startswith("certs.example.com_")
        assert cache_path.name.endswith(".pem")

    def test_same_url_same_path(self):
        """Test same URL generates same cache path."""
        url = "https://certs.example.com/ca.pem"
        path1 = _get_cache_path(url)
        path2 = _get_cache_path(url)

        assert path1 == path2

    def test_different_url_different_path(self):
        """Test different URLs generate different cache paths."""
        url1 = "https://certs.example.com/ca1.pem"
        url2 = "https://certs.example.com/ca2.pem"
        path1 = _get_cache_path(url1)
        path2 = _get_cache_path(url2)

        assert path1 != path2


class TestDownloadCertificate:
    """Tests for certificate downloading."""

    @pytest.mark.asyncio
    async def test_download_valid_certificate(self, tmp_path):
        """Test downloading a valid certificate."""
        # Setup
        set_cache_directory(tmp_path)
        url = "https://certs.example.com/ca.pem"

        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=VALID_CERT)
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            cert_path = await download_certificate(url)

        # Verify
        assert cert_path.exists()
        assert cert_path.read_text() == VALID_CERT
        assert cert_path.parent == tmp_path

    @pytest.mark.asyncio
    async def test_download_invalid_url(self):
        """Test downloading with invalid URL raises error."""
        with pytest.raises(ValueError, match="Invalid URL"):
            await download_certificate("/not/a/url")

    @pytest.mark.asyncio
    async def test_download_invalid_certificate(self, tmp_path):
        """Test downloading invalid certificate content raises error."""
        set_cache_directory(tmp_path)
        url = "https://certs.example.com/not-a-cert.txt"

        # Mock aiohttp response with invalid content
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=INVALID_CERT)
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(ValueError, match="does not appear to be a valid"):
                await download_certificate(url)

    @pytest.mark.asyncio
    async def test_download_uses_cache(self, tmp_path):
        """Test that cached certificate is used without re-download."""
        set_cache_directory(tmp_path)
        url = "https://certs.example.com/ca.pem"
        cache_path = _get_cache_path(url)

        # Pre-populate cache
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(VALID_CERT)

        # Should not make HTTP request
        with patch("aiohttp.ClientSession") as mock_session:
            result_path = await download_certificate(url)
            mock_session.assert_not_called()

        assert result_path == cache_path

    @pytest.mark.asyncio
    async def test_download_force_refresh(self, tmp_path):
        """Test force refresh re-downloads certificate."""
        set_cache_directory(tmp_path)
        url = "https://certs.example.com/ca.pem"
        cache_path = _get_cache_path(url)

        # Pre-populate cache with old content
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("OLD CERTIFICATE")

        # Mock new certificate download
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=VALID_CERT)
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result_path = await download_certificate(url, force_refresh=True)

        # Verify new content was downloaded
        assert result_path.read_text() == VALID_CERT


class TestGetCertificatePath:
    """Tests for get_certificate_path function."""

    @pytest.mark.asyncio
    async def test_url_certificate(self, tmp_path):
        """Test getting certificate from URL."""
        set_cache_directory(tmp_path)
        url = "https://certs.example.com/ca.pem"

        # Mock download
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=VALID_CERT)
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            cert_path = await get_certificate_path(url)

        assert Path(cert_path).exists()
        assert Path(cert_path).parent == tmp_path

    @pytest.mark.asyncio
    async def test_local_certificate(self, tmp_path):
        """Test getting local certificate path."""
        # Create a test certificate file
        cert_file = tmp_path / "test-ca.pem"
        cert_file.write_text(VALID_CERT)

        cert_path = await get_certificate_path(str(cert_file))
        assert cert_path == str(cert_file)

    @pytest.mark.asyncio
    async def test_local_certificate_not_found(self):
        """Test error when local certificate doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Certificate file not found"):
            await get_certificate_path("/nonexistent/cert.pem")


class TestClearCertificateCache:
    """Tests for cache clearing."""

    def test_clear_cache(self, tmp_path):
        """Test clearing certificate cache."""
        set_cache_directory(tmp_path)

        # Create some cached certificates
        (tmp_path / "cert1.pem").write_text(VALID_CERT)
        (tmp_path / "cert2.pem").write_text(VALID_CERT)

        # Clear cache
        clear_certificate_cache()

        # Verify cache is empty
        assert not (tmp_path / "cert1.pem").exists()
        assert not (tmp_path / "cert2.pem").exists()

    def test_clear_empty_cache(self, tmp_path):
        """Test clearing empty cache doesn't raise error."""
        # Set non-existent directory
        non_existent = tmp_path / "non_existent"
        set_cache_directory(non_existent)

        # Should not raise error
        clear_certificate_cache()


class TestSetCacheDirectory:
    """Tests for setting cache directory."""

    def test_set_cache_directory_string(self, tmp_path):
        """Test setting cache directory with string."""
        test_dir = tmp_path / "custom_cache"
        set_cache_directory(str(test_dir))

        # Verify new directory is used
        url = "https://example.com/cert.pem"
        cache_path = _get_cache_path(url)
        assert cache_path.parent == test_dir

    def test_set_cache_directory_path(self, tmp_path):
        """Test setting cache directory with Path object."""
        test_dir = tmp_path / "custom_cache"
        set_cache_directory(test_dir)

        # Verify new directory is used
        url = "https://example.com/cert.pem"
        cache_path = _get_cache_path(url)
        assert cache_path.parent == test_dir
