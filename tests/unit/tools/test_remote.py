"""Unit tests for remote file tools.

Tests focus on redirect handling and error cases.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.tools import ToolException

from macsdk.tools.remote import fetch_and_save, fetch_file, fetch_json


class TestFetchFileRedirects:
    """Tests for fetch_file with HTTP redirects."""

    @pytest.mark.asyncio
    async def test_fetch_file_with_301_redirect(self):
        """Test that fetch_file fails when redirects are not followed.

        This test verifies the bug scenario where a 301 redirect
        without follow_redirects=True causes a failure.
        """
        url = "https://example.com/logs/app.log"
        expected_content = "Log line 1\nLog line 2\nLog line 3"

        # Mock httpx response with 301 redirect (not followed)
        mock_response = MagicMock()
        mock_response.status_code = 301  # Redirect not followed
        mock_response.text = expected_content
        mock_response.headers = {
            "Location": "https://example.com/logs/new-location/app.log"
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            # Should raise ToolException (any message)
            with pytest.raises(ToolException):
                await fetch_file.ainvoke({"url": url})

    @pytest.mark.asyncio
    async def test_fetch_file_with_302_redirect(self):
        """Test that fetch_file fails when redirects are not followed.

        This test verifies the bug scenario where a 302 redirect
        without follow_redirects=True causes a failure.
        """
        url = "https://example.com/report.txt"
        expected_content = "Report content"

        # Mock httpx response with 302 redirect (not followed)
        mock_response = MagicMock()
        mock_response.status_code = 302  # Redirect not followed
        mock_response.text = expected_content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            # Should raise ToolException (any message)
            with pytest.raises(ToolException):
                await fetch_file.ainvoke({"url": url})

    @pytest.mark.asyncio
    async def test_fetch_file_redirect_success_after_fix(self):
        """Test that fetch_file works correctly after enabling follow_redirects.

        This test verifies that follow_redirects=True is passed to AsyncClient.
        """
        url = "https://example.com/logs/app.log"
        expected_content = "Log line 1\nLog line 2\nLog line 3"

        # Mock httpx response after following redirect (status_code=200)
        mock_response = MagicMock()
        mock_response.status_code = 200  # Final response after redirect
        mock_response.text = expected_content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = mock_client

            result = await fetch_file.ainvoke({"url": url})
            assert result == expected_content

            # Verify follow_redirects=True is passed
            mock_client_cls.assert_called_once_with(
                verify=True, timeout=30, follow_redirects=True
            )


class TestFetchAndSaveRedirects:
    """Tests for fetch_and_save with HTTP redirects."""

    @pytest.mark.asyncio
    async def test_fetch_and_save_with_redirect(self, tmp_path):
        """Test that fetch_and_save fails when redirects are not followed.

        This test verifies the bug scenario where a 301 redirect
        without follow_redirects=True causes a failure.
        """
        url = "https://example.com/report.pdf"
        save_path = str(tmp_path / "report.pdf")
        content = b"PDF content here"

        # Mock httpx response with 301 redirect (not followed)
        mock_response = MagicMock()
        mock_response.status_code = 301
        mock_response.content = content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            # Should raise ToolException (any message)
            with pytest.raises(ToolException):
                await fetch_and_save.ainvoke({"url": url, "save_path": save_path})

    @pytest.mark.asyncio
    async def test_fetch_and_save_redirect_success_after_fix(self, tmp_path):
        """Test that fetch_and_save works after enabling follow_redirects.

        This test verifies that follow_redirects=True is passed to AsyncClient.
        """
        url = "https://example.com/report.pdf"
        save_path = str(tmp_path / "report.pdf")
        content = b"PDF content here"

        # Mock httpx response after following redirect
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = mock_client

            result = await fetch_and_save.ainvoke({"url": url, "save_path": save_path})
            assert "Successfully saved" in result
            assert str(len(content)) in result

            # Verify follow_redirects=True is passed
            mock_client_cls.assert_called_once_with(
                verify=True, timeout=60, follow_redirects=True
            )


class TestFetchJsonRedirects:
    """Tests for fetch_json with HTTP redirects."""

    @pytest.mark.asyncio
    async def test_fetch_json_redirect_success_after_fix(self):
        """Test that fetch_json works after enabling follow_redirects.

        This test verifies that follow_redirects=True is passed to AsyncClient.
        """
        url = "https://api.example.com/data"
        expected_data = {"status": "ok", "data": [1, 2, 3]}

        # Mock httpx response after following redirect
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=expected_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value = mock_client

            result = await fetch_json.ainvoke({"url": url})
            assert "ok" in result
            assert "data" in result

            # Verify follow_redirects=True is passed
            mock_client_cls.assert_called_once_with(
                verify=True, timeout=30, follow_redirects=True
            )


class TestFetchFileBasicFunctionality:
    """Tests for basic fetch_file functionality."""

    @pytest.mark.asyncio
    async def test_fetch_file_success(self):
        """Test basic successful file fetch."""
        url = "https://example.com/file.txt"
        content = "File content here"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_file.ainvoke({"url": url})
            assert result == content

    @pytest.mark.asyncio
    async def test_fetch_file_with_grep(self):
        """Test file fetch with grep pattern."""
        url = "https://example.com/logs/app.log"
        content = "ERROR: Something failed\nINFO: All good\nERROR: Another issue"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_file.ainvoke({"url": url, "grep_pattern": "ERROR"})
            assert "ERROR: Something failed" in result
            assert "ERROR: Another issue" in result
            assert "INFO: All good" not in result

    @pytest.mark.asyncio
    async def test_fetch_file_with_tail(self):
        """Test file fetch with tail_lines."""
        url = "https://example.com/file.txt"
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = content

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_file.ainvoke({"url": url, "tail_lines": 2})
            assert result == "Line 4\nLine 5"

    @pytest.mark.asyncio
    async def test_fetch_file_404_error(self):
        """Test fetch_file with 404 error."""
        url = "https://example.com/nonexistent.txt"

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        with patch("macsdk.tools.remote.httpx.AsyncClient", return_value=mock_client):
            # Should raise ToolException (any message)
            with pytest.raises(ToolException):
                await fetch_file.ainvoke({"url": url})
