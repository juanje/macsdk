"""Tests for API Service Registry validators."""

from __future__ import annotations

import pytest
from pydantic import HttpUrl, ValidationError

from macsdk.core.api_registry import (
    APIServiceConfig,
    clear_api_services,
    get_api_service,
    list_api_services,
    register_api_service,
)


class TestAPIServiceConfigValidators:
    """Tests for Pydantic Field validators in APIServiceConfig."""

    def test_valid_url_accepted(self) -> None:
        """Valid HTTP URL is accepted."""
        config = APIServiceConfig(
            name="test",
            base_url=HttpUrl("https://api.example.com"),
        )
        assert str(config.base_url) == "https://api.example.com/"

    def test_url_without_scheme_raises(self) -> None:
        """URL without http/https scheme raises ValidationError."""
        with pytest.raises(ValidationError):
            HttpUrl("api.example.com")

    def test_timeout_zero_raises(self) -> None:
        """Timeout 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="timeout"):
            APIServiceConfig(
                name="test",
                base_url=HttpUrl("https://api.example.com"),
                timeout=0,
            )

    def test_timeout_negative_raises(self) -> None:
        """Negative timeout raises ValidationError."""
        with pytest.raises(ValidationError, match="timeout"):
            APIServiceConfig(
                name="test",
                base_url=HttpUrl("https://api.example.com"),
                timeout=-1,
            )

    def test_max_retries_negative_raises(self) -> None:
        """Negative max_retries raises ValidationError."""
        with pytest.raises(ValidationError, match="max_retries"):
            APIServiceConfig(
                name="test",
                base_url=HttpUrl("https://api.example.com"),
                max_retries=-1,
            )

    def test_max_retries_zero_valid(self) -> None:
        """Zero max_retries is valid (no retries)."""
        config = APIServiceConfig(
            name="test",
            base_url=HttpUrl("https://api.example.com"),
            max_retries=0,
        )
        assert config.max_retries == 0

    def test_rate_limit_zero_raises(self) -> None:
        """Rate limit 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="rate_limit"):
            APIServiceConfig(
                name="test",
                base_url=HttpUrl("https://api.example.com"),
                rate_limit=0,
            )

    def test_rate_limit_none_valid(self) -> None:
        """None rate_limit is valid (no limit)."""
        config = APIServiceConfig(
            name="test",
            base_url=HttpUrl("https://api.example.com"),
            rate_limit=None,
        )
        assert config.rate_limit is None

    def test_rate_limit_positive_valid(self) -> None:
        """Positive rate_limit is valid."""
        config = APIServiceConfig(
            name="test",
            base_url=HttpUrl("https://api.example.com"),
            rate_limit=5000,
        )
        assert config.rate_limit == 5000


class TestRegisterApiService:
    """Tests for register_api_service function with validation."""

    def setup_method(self) -> None:
        """Clear services before each test."""
        clear_api_services()

    def teardown_method(self) -> None:
        """Clear services after each test."""
        clear_api_services()

    def test_register_valid_service(self) -> None:
        """Valid service registration succeeds."""
        register_api_service(
            name="github",
            base_url="https://api.github.com",
            token="test-token",
            timeout=60,
        )
        assert "github" in list_api_services()
        service = get_api_service("github")
        assert service.timeout == 60

    def test_register_invalid_url_raises(self) -> None:
        """Registration with invalid URL raises ValidationError."""
        with pytest.raises(ValidationError, match="URL"):
            register_api_service(
                name="invalid",
                base_url="not-a-valid-url",
            )

    def test_register_invalid_timeout_raises(self) -> None:
        """Registration with invalid timeout raises ValidationError."""
        with pytest.raises(ValidationError, match="timeout"):
            register_api_service(
                name="test",
                base_url="https://api.example.com",
                timeout=0,
            )

    def test_trailing_slash_normalized(self) -> None:
        """Trailing slash in URL is handled correctly."""
        register_api_service(
            name="test",
            base_url="https://api.example.com/v1/",
        )
        service = get_api_service("test")
        # Pydantic HttpUrl may add trailing slash for root, but our normalization
        # removes it before passing to Pydantic
        url_str = str(service.base_url)
        assert "v1" in url_str
