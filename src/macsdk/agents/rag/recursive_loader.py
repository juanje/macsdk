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
        # Cache netloc and path to avoid re-parsing on every link extraction
        parsed = urlparse(url)
        self.base_netloc = parsed.netloc
        # Store base path to ensure we only crawl under the initial URL's path
        self.base_path = parsed.path.rstrip("/")

    def _parse_base_url(self, url: str) -> str:
        """Extract base URL (scheme + netloc).

        Args:
            url: Full URL to parse.

        Returns:
            Base URL with scheme and netloc only.
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates.

        Removes fragments for consistent comparison. For deduplication purposes,
        treats URLs with/without trailing slash as the same, but preserves the
        original form to avoid 404s on servers that require specific format.

        Args:
            url: URL to normalize.

        Returns:
            Normalized URL (for deduplication key).
        """
        # Remove fragments
        url = url.split("#")[0]
        # For deduplication, remove trailing slash if present (but we'll visit
        # using the original URL form provided by the website)
        return url.rstrip("/") if url.count("/") > 2 else url

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> list[str]:
        """Extract all valid links from HTML.

        Only returns links from the same domain and under the base path to prevent
        crawling external sites or unrelated sections of the same domain.

        Uses strict path matching: a link's path must exactly match base_path or
        start with base_path + "/" to prevent partial matches (e.g., /doc should
        not match /documentation).

        Args:
            soup: Parsed BeautifulSoup object.
            current_url: Current page URL (for resolving relative links).

        Returns:
            List of normalized absolute URLs to follow.
        """
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = str(a_tag["href"])  # Convert to str for type safety

            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)

            # Only follow links from same domain and under base path
            parsed = urlparse(absolute_url)
            # Strict path matching: exact match or under subdirectory
            # Prevents /doc from matching /documentation
            path_match = parsed.path == self.base_path or parsed.path.startswith(
                self.base_path + "/"
            )
            if parsed.netloc == self.base_netloc and path_match:
                # Remove fragments but keep URL as provided by the website
                # (preserving trailing slashes to avoid 404s)
                clean_url = absolute_url.split("#")[0]
                links.append(clean_url)

        return list(set(links))  # Deduplicate

    def _crawl_recursive(
        self,
        url: str,
        visited: set[str],
        client: httpx.Client,
        depth: int = 0,
    ) -> list[Document]:
        """Recursively crawl pages starting from given URL.

        Args:
            url: URL to crawl.
            visited: Set of already visited URLs (normalized for deduplication).
            client: Reusable httpx.Client for connection pooling.
            depth: Current recursion depth.

        Returns:
            List of Document objects from this URL and its children.
        """
        # Normalize URL for deduplication check
        # (treats URLs with/without trailing slash as same)
        normalized = self._normalize_url(url)

        if depth >= self.max_depth or normalized in visited:
            return []

        visited.add(normalized)
        documents = []

        try:
            # Make HTTP request with shared client (enables connection pooling)
            response = client.get(url)
            response.raise_for_status()

            # Check Content-Type to avoid processing binary files
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(
                html_type in content_type
                for html_type in ["text/html", "application/xhtml", "text/plain"]
            ):
                logger.debug(f"Skipping non-HTML content at {url}: {content_type}")
                if self.progress_callback:
                    self.progress_callback(url, 0)
                return []

            html = response.text

            # Parse HTML once to avoid redundant parsing
            soup = BeautifulSoup(html, "html.parser")

            # Extract content using provided extractor
            content = self.extractor(html)
            if content:
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": url,
                        "content_type": content_type,
                    },
                )
                documents.append(doc)

            # Report progress after each successful page load
            if self.progress_callback:
                self.progress_callback(url, len(documents))

            # Extract and follow links if not at max depth
            # Reuse parsed soup to avoid redundant parsing
            if depth < self.max_depth - 1:
                links = self._extract_links(soup, url)
                for link in links:
                    documents.extend(
                        self._crawl_recursive(link, visited, client, depth + 1)
                    )

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

        Uses a single httpx.Client instance for all requests to enable
        connection pooling and Keep-Alive, significantly improving performance
        when crawling multiple pages from the same domain.

        Returns:
            List of Document objects from all crawled pages.
        """
        visited: set[str] = set()
        # Use URL as-is (normalization happens in _crawl_recursive)
        with httpx.Client(
            verify=self.verify, timeout=self.timeout, follow_redirects=True
        ) as client:
            return self._crawl_recursive(self.url, visited, client)
