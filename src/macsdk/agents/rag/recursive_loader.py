"""Simple recursive URL loader using httpx (MACSDK internal).

This is a simplified alternative to langchain_community.RecursiveUrlLoader
optimized for MACSDK's needs with better SSL certificate handling via httpx.

Features:
- Uses httpx for consistent SSL/certificate handling
- Real-time progress callbacks for each page loaded
- Simpler API focused on actual MACSDK usage patterns
- No complex filtering (regex, exclude_dirs) - kept simple

This implementation is deliberately minimal, covering only the features
actually used in MACSDK's RAG agent.
"""

from __future__ import annotations

import logging
from typing import Callable, Protocol
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class ProgressCallback(Protocol):
    """Protocol for progress callbacks during crawling."""

    def __call__(self, url: str, docs_count: int) -> None:
        """Called when a page is successfully loaded.

        Args:
            url: URL that was loaded
            docs_count: Number of documents extracted from this page
        """
        ...


class SimpleRecursiveLoader:
    """Recursively load and extract content from web pages.

    This loader crawls web pages recursively starting from a root URL,
    extracting content using a provided extractor function.

    Args:
        url: Starting URL to crawl
        max_depth: Maximum recursion depth (default: 2)
        extractor: Function to extract text from HTML (default: identity)
        verify: SSL verification - can be bool, str (cert path), or SSLContext
        timeout: Request timeout in seconds (default: 10)
        progress_callback: Optional callback called for each page loaded

    Example:
        >>> def extract_text(html: str) -> str:
        ...     soup = BeautifulSoup(html, "html.parser")
        ...     return soup.get_text()
        >>>
        >>> loader = SimpleRecursiveLoader(
        ...     url="https://docs.example.com",
        ...     max_depth=2,
        ...     extractor=extract_text,
        ... )
        >>> docs = loader.load()
    """

    def __init__(
        self,
        url: str,
        max_depth: int = 2,
        extractor: Callable[[str], str] | None = None,
        verify: bool | str = True,
        timeout: int = 10,
        progress_callback: ProgressCallback | None = None,
    ):
        self.url = url
        self.max_depth = max_depth
        self.extractor = extractor or (lambda x: x)
        self.verify = verify
        self.timeout = timeout
        self.progress_callback = progress_callback
        self.base_url = self._parse_base_url(url)

    def _parse_base_url(self, url: str) -> str:
        """Extract base URL (scheme + netloc).

        Args:
            url: Full URL to parse.

        Returns:
            Base URL with scheme and netloc only.
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _extract_links(self, html: str, current_url: str) -> list[str]:
        """Extract all valid links from HTML.

        Only returns links from the same domain as base_url to prevent
        crawling external sites.

        Args:
            html: HTML content to parse.
            current_url: Current page URL (for resolving relative links).

        Returns:
            List of absolute URLs to follow.
        """
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)

            # Only follow links from same domain
            if absolute_url.startswith(self.base_url):
                # Remove fragments
                absolute_url = absolute_url.split("#")[0]
                links.append(absolute_url)

        return list(set(links))  # Deduplicate

    def _crawl_recursive(
        self,
        url: str,
        visited: set[str],
        depth: int = 0,
    ) -> list[Document]:
        """Recursively crawl pages starting from given URL.

        Args:
            url: URL to crawl.
            visited: Set of already visited URLs.
            depth: Current recursion depth.

        Returns:
            List of Document objects from this URL and its children.
        """
        if depth >= self.max_depth or url in visited:
            return []

        visited.add(url)
        documents = []

        try:
            # Make HTTP request with httpx
            with httpx.Client(verify=self.verify, timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                html = response.text

            # Extract content using provided extractor
            content = self.extractor(html)
            if content:
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": url,
                        "content_type": response.headers.get("Content-Type", ""),
                    },
                )
                documents.append(doc)

            # Report progress after each successful page load
            if self.progress_callback:
                self.progress_callback(url, len(documents))

            # Extract and follow links if not at max depth
            if depth < self.max_depth - 1:
                links = self._extract_links(html, url)
                for link in links:
                    documents.extend(self._crawl_recursive(link, visited, depth + 1))

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error loading {url}: {e.response.status_code}")
            # Still report progress even on error
            if self.progress_callback:
                self.progress_callback(url, 0)
        except httpx.RequestError as e:
            logger.warning(f"Request error loading {url}: {e}")
            # Still report progress even on error
            if self.progress_callback:
                self.progress_callback(url, 0)
        except Exception as e:
            logger.warning(f"Unexpected error loading {url}: {e}")
            # Still report progress even on error
            if self.progress_callback:
                self.progress_callback(url, 0)

        return documents

    def load(self) -> list[Document]:
        """Load all documents by crawling recursively from root URL.

        Returns:
            List of Document objects from all crawled pages.
        """
        visited: set[str] = set()
        return self._crawl_recursive(self.url, visited)
