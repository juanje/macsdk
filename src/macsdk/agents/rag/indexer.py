"""Document loading and indexing utilities for RAG agent.

This module provides functionality to:
- Load documents from multiple sources (HTML pages, Markdown files)
- Support for local and remote Markdown files
- Split documents into chunks
- Create embeddings and store in ChromaDB
- Manage document metadata (source, tags)

Supported source types:
- html: Web pages (crawled recursively with BeautifulSoup)
- markdown: Markdown files (local paths or remote URLs)

Optimizations:
- Parallel source loading using ThreadPoolExecutor
- Progress tracking with tqdm
- Batch embedding creation via ChromaDB
"""

from __future__ import annotations

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import bs4
import requests
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr
from tqdm import tqdm

from macsdk.core.cert_manager import get_certificate_path
from macsdk.core.config import config as macsdk_config

from .config import RAGConfig, RAGSourceConfig, get_rag_config
from .recursive_loader import SimpleRecursiveLoader

if TYPE_CHECKING:
    from .recursive_loader import ProgressCallback

logger = logging.getLogger(__name__)


def simple_extractor(html: str) -> str:
    """Extract text from HTML, focusing on main content.

    Tries to find the main content div (common in ReadTheDocs/Sphinx)
    to avoid indexing navigation bars and footers.

    Args:
        html: Raw HTML content.

    Returns:
        Extracted text content.
    """
    soup = bs4.BeautifulSoup(html, "html.parser")

    # Try to find the specific main content div used by Sphinx themes
    main_content = soup.find("div", role="main") or soup.find("article")

    if main_content:
        return str(main_content.get_text(separator=" ", strip=True))

    # Fallback to getting all text if main content structure isn't found
    return str(soup.get_text(separator=" ", strip=True))


def _is_url(path: str) -> bool:
    """Check if a path is a URL.

    Args:
        path: Path or URL string.

    Returns:
        True if it's a URL, False if it's a local path.
    """
    parsed = urlparse(path)
    return parsed.scheme in ("http", "https")


def _resolve_cert_path(source: RAGSourceConfig) -> tuple[Path | None, str | None]:
    """Resolve certificate path from source configuration.

    Helper to avoid duplicating certificate resolution logic.

    Note: This function uses asyncio.run() which is safe here because
    the RAG indexer calls this from within a ThreadPoolExecutor (in
    create_retriever), not from an active event loop.

    Args:
        source: Source configuration with cert_path and/or cert_url.

    Returns:
        Tuple of (cert_path, error_message). If successful, cert_path is set
        and error_message is None. If failed, cert_path is None and
        error_message contains the error.

    Raises:
        RuntimeError: If called from within an active event loop. This would
                      indicate incorrect usage - this function must be called
                      from a synchronous context (ThreadPoolExecutor).
    """
    import asyncio

    cert_spec = source.cert_path or source.cert_url
    if not cert_spec:
        return (None, None)

    try:
        cert_path_str = asyncio.run(get_certificate_path(cert_spec))
        return (Path(cert_path_str), None)
    except RuntimeError as e:
        # Specific handling for event loop conflicts
        if "cannot be called from a running event loop" in str(e):
            error_msg = (
                "Certificate resolution failed: asyncio.run() called from "
                "async context. The RAG indexer must run in a "
                "ThreadPoolExecutor, not from an event loop."
            )
            logger.error(f"{error_msg} Original error: {e}")
            return (None, error_msg)
        # Re-raise other RuntimeErrors
        raise
    except Exception as e:
        error_msg = f"Certificate error: {e}"
        logger.error(f"Failed to get certificate for {cert_spec}: {e}")
        return (None, error_msg)


def _load_markdown_from_url(
    url: str,
    cert_path: Path | None = None,
    verify_ssl: bool = True,
) -> str:
    """Download markdown content from a URL.

    Args:
        url: URL to the markdown file.
        cert_path: Optional path to SSL certificate.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        Markdown content as string.
    """
    verify: bool | str = verify_ssl
    if cert_path:
        verify = str(cert_path)

    response = requests.get(url, timeout=30, verify=verify)
    response.raise_for_status()
    return str(response.text)


def _load_markdown_documents(
    source: RAGSourceConfig,
    config: RAGConfig,
) -> tuple[str, list[Document], str | None]:
    """Load documents from a Markdown source (local or remote).

    Args:
        source: Source configuration.
        config: RAG configuration.

    Returns:
        Tuple of (source_path, docs, error_message).
    """
    path_or_url = source.url
    logger.info(f"[PARALLEL] Loading markdown from {path_or_url}")

    try:
        docs: list[Document] = []
        tags_str = ",".join(source.tags) if source.tags else ""

        if _is_url(path_or_url):
            # Remote markdown file
            cert_path, error = _resolve_cert_path(source)
            if error:
                return (path_or_url, [], error)

            content = _load_markdown_from_url(
                path_or_url, cert_path, verify_ssl=source.verify_ssl
            )

            doc = Document(
                page_content=content,
                metadata={
                    "source": path_or_url,
                    "source_name": source.name,
                    "source_url": path_or_url,
                    "tags": tags_str,
                    "type": "markdown",
                },
            )
            docs.append(doc)
            logger.info(f"[PARALLEL] Loaded remote markdown: {path_or_url}")

        else:
            # Local markdown file or directory
            local_path = Path(path_or_url).expanduser().resolve()

            if not local_path.exists():
                return (path_or_url, [], f"Path does not exist: {local_path}")

            if local_path.is_file():
                # Single file
                if local_path.suffix.lower() in (".md", ".markdown"):
                    content = local_path.read_text(encoding="utf-8")
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(local_path),
                            "source_name": source.name,
                            "source_url": path_or_url,
                            "tags": tags_str,
                            "type": "markdown",
                            "filename": local_path.name,
                        },
                    )
                    docs.append(doc)
                else:
                    return (path_or_url, [], f"Not a markdown file: {local_path}")

            elif local_path.is_dir():
                # Directory - load all .md files recursively
                md_files = list(local_path.rglob("*.md")) + list(
                    local_path.rglob("*.markdown")
                )

                for md_file in md_files:
                    try:
                        content = md_file.read_text(encoding="utf-8")
                        relative_path = md_file.relative_to(local_path)
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": str(md_file),
                                "source_name": source.name,
                                "source_url": path_or_url,
                                "tags": tags_str,
                                "type": "markdown",
                                "filename": md_file.name,
                                "relative_path": str(relative_path),
                            },
                        )
                        docs.append(doc)
                    except Exception as e:
                        logger.warning(f"Failed to load {md_file}: {e}")

                logger.info(
                    f"[PARALLEL] Loaded {len(docs)} markdown files from {local_path}"
                )

        return (path_or_url, docs, None)

    except Exception as e:
        logger.error(f"[PARALLEL] Failed to load markdown from {path_or_url}: {e}")
        return (path_or_url, [], str(e))


def _get_collection_name_for_sources(
    sources: list[RAGSourceConfig],
    config: RAGConfig,
) -> str:
    """Generate a unique collection name based on sources and config.

    Args:
        sources: List of documentation sources.
        config: RAG configuration.

    Returns:
        Unique collection name.
    """
    # Sort URLs to ensure consistent hashing regardless of order
    sorted_urls = sorted([s.url for s in sources])
    urls_str = "|".join(sorted_urls)
    chunk_info = f"{config.chunk_size}_{config.chunk_overlap}_{config.max_depth}"
    content = f"{urls_str}_{chunk_info}"
    # MD5 used only for collection ID generation (not for security)
    url_hash = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:8]
    return f"macsdk-docs-{url_hash}"


def collection_exists(collection_name: str, db_dir: Path) -> bool:
    """Check if a ChromaDB collection already exists.

    Args:
        collection_name: Name of the collection to check.
        db_dir: ChromaDB directory path.

    Returns:
        True if collection exists, False otherwise.
    """
    if not db_dir.exists():
        return False

    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(db_dir))
        collections = client.list_collections()
        return any(col.name == collection_name for col in collections)
    except Exception as e:
        logger.debug(f"Error checking collection existence: {e}")
        return False


def load_existing_retriever(
    collection_name: str,
    config: RAGConfig,
) -> VectorStoreRetriever | None:
    """Load a retriever from an existing ChromaDB collection.

    Args:
        collection_name: Name of the collection to load.
        config: RAG configuration.

    Returns:
        VectorStoreRetriever if successful, None otherwise.
    """
    try:
        api_key = (
            SecretStr(macsdk_config.google_api_key)
            if macsdk_config.google_api_key
            else None
        )
        embeddings = GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
            model=config.embedding_model,
            google_api_key=api_key,
        )

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(config.chroma_db_dir),
        )

        # Verify the collection has documents
        if vectorstore._collection.count() == 0:
            logger.warning("Collection exists but is empty")
            return None

        logger.info(
            f"Loaded existing collection '{collection_name}' with "
            f"{vectorstore._collection.count()} documents"
        )
        retriever: VectorStoreRetriever = vectorstore.as_retriever(
            search_kwargs={"k": config.retriever_k}
        )
        return retriever

    except Exception as e:
        logger.error(f"Error loading existing collection: {e}")
        return None


def _load_html_documents(
    source: RAGSourceConfig,
    config: RAGConfig,
    progress_callback: "ProgressCallback | None" = None,
) -> tuple[str, list[Document], str | None]:
    """Load documents from a web URL (HTML).

    Args:
        source: Source configuration.
        config: RAG configuration.
        progress_callback: Optional callback for progress updates per page.

    Returns:
        Tuple of (url, docs, error_message).
    """
    url = source.url
    logger.info(f"[PARALLEL] Starting to load HTML from {url}")

    try:
        # Determine SSL verification setting
        verify: bool | str = True

        if not source.verify_ssl:
            # Disable SSL verification
            logger.warning(f"SSL verification disabled for {url}")
            verify = False
        else:
            # Use custom certificate if configured
            cert_path, error = _resolve_cert_path(source)
            if error:
                return (url, [], error)
            if cert_path:
                verify = str(cert_path)
                logger.info(f"Using certificate: {verify}")

        # Load documents using SimpleRecursiveLoader
        loader = SimpleRecursiveLoader(
            url=url,
            max_depth=config.max_depth,
            extractor=simple_extractor,
            verify=verify,
            timeout=30,
            progress_callback=progress_callback,
        )
        docs = loader.load()

        # Add metadata to documents
        # ChromaDB only accepts primitive types, so convert tags list to string
        tags_str = ",".join(source.tags) if source.tags else ""
        for doc in docs:
            doc.metadata["source_name"] = source.name
            doc.metadata["source_url"] = url
            doc.metadata["tags"] = tags_str
            doc.metadata["type"] = "html"

        logger.info(f"[PARALLEL] Completed loading {url} - {len(docs)} docs")
        return (url, docs, None)

    except Exception as e:
        logger.error(f"[PARALLEL] Failed to load {url}: {e}")
        return (url, [], str(e))


def _load_source_documents(
    source: RAGSourceConfig,
    config: RAGConfig,
    progress_callback: "ProgressCallback | None" = None,
) -> tuple[str, list[Document], str | None]:
    """Load documents from a source based on its type.

    Args:
        source: Source configuration.
        config: RAG configuration.
        progress_callback: Optional callback for progress updates.

    Returns:
        Tuple of (source_path, docs, error_message).
    """

    source_type = source.type.lower()

    if source_type == "markdown":
        return _load_markdown_documents(source, config)
    else:
        # Default to HTML
        return _load_html_documents(source, config, progress_callback)


def create_retriever(
    sources: list[RAGSourceConfig] | None = None,
    config: RAGConfig | None = None,
    force_reindex: bool = False,
) -> VectorStoreRetriever:
    """Create a retriever by loading and indexing documentation.

    This function will check if the documents are already indexed and reuse
    them unless force_reindex is True. Supports multiple URLs to create
    a combined knowledge base.

    Args:
        sources: Documentation sources to index. If None, uses config sources.
        config: RAG configuration. If None, loads from config.yml.
        force_reindex: If True, reindex even if collection exists.

    Returns:
        VectorStoreRetriever for semantic search.

    Raises:
        ValueError: If no documents could be loaded.
    """
    if config is None:
        config = get_rag_config()

    if sources is None:
        sources = config.sources

    # Ensure chroma_db_dir exists
    config.chroma_db_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique collection name for these sources and config
    collection_name = _get_collection_name_for_sources(sources, config)

    # Check if collection already exists
    if not force_reindex and collection_exists(collection_name, config.chroma_db_dir):
        logger.info(f"Found existing index for {len(sources)} source(s)")
        print("\n📚 Loading existing documentation index...")
        retriever = load_existing_retriever(collection_name, config)
        if retriever:
            print("✅ Documentation loaded successfully!\n")
            return retriever
        logger.warning("Failed to load existing index, will reindex")
        print("⚠️  Could not load existing index, re-indexing...\n")

    # Index documents from all sources in parallel
    logger.info(f"Indexing documents from {len(sources)} source(s)")
    print("\n📚 Indexing documentation...")
    all_docs: list["Document"] = []

    # Load URLs in parallel using ThreadPoolExecutor
    print(f"\n⚡ Starting parallel loading ({min(len(sources), 4)} workers)")
    print("📥 Submitting all URLs simultaneously...")
    for i, source in enumerate(sources, 1):
        print(f"   {i}. {source.url}")
    print("\n⏳ Crawling web pages (progress shown per page)...\n")

    logger.info(
        f"Starting parallel loading of {len(sources)} sources "
        f"with {min(len(sources), 4)} workers"
    )

    # Create a thread-safe progress callback
    import threading

    progress_lock = threading.Lock()

    def page_progress_callback(url: str, docs_count: int) -> None:
        """Thread-safe callback to update progress bar per page."""
        with progress_lock:
            # Update the progress bar
            page_pbar.update(1)
            # Extract domain from URL for cleaner display
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                path = parsed.path
                if len(path) > 40:
                    path = path[:37] + "..."
                page_pbar.set_postfix_str(f"{domain}{path}")
            except Exception:  # nosec B110
                pass  # Progress bar display failure is non-critical

    try:
        # We don't know total pages in advance, so use unknown total
        # Progress bar will just show count
        with tqdm(
            total=None,
            desc="Loading pages",
            unit="page",
            ncols=100,
        ) as page_pbar:
            with ThreadPoolExecutor(max_workers=min(len(sources), 4)) as executor:
                # Submit all source loading tasks with progress callback
                future_to_source = {
                    executor.submit(
                        _load_source_documents, source, config, page_progress_callback
                    ): source
                    for source in sources
                }
                logger.info(f"All {len(sources)} tasks submitted")

                # Process results as they complete
                try:
                    for future in as_completed(future_to_source):
                        url, docs, error = future.result()
                        # Extract domain using urlparse for robustness
                        short_url = urlparse(url).netloc
                        if error:
                            logger.error(f"Error loading {url}: {error}")
                            page_pbar.write(f"⚠️  FAILED: {short_url} - {error[:60]}...")
                        else:
                            if len(docs) == 0:
                                logger.warning(f"No documents loaded from {url}")
                                page_pbar.write(
                                    f"⚠️  EMPTY:  {short_url} - No documents found"
                                )
                            else:
                                logger.info(
                                    f"Successfully loaded {len(docs)} documents "
                                    f"from {url}"
                                )
                                all_docs.extend(docs)
                                page_pbar.write(
                                    f"✅ SUCCESS: {short_url} - {len(docs):3d} docs"
                                )
                except KeyboardInterrupt:
                    logger.warning("Keyboard interrupt, cancelling remaining tasks")
                    page_pbar.write("\n⚠️  Cancelling parallel loading...")
                    for future in future_to_source:
                        future.cancel()
                    raise
    except KeyboardInterrupt:
        logger.warning("Parallel loading interrupted by user")
        raise ValueError("Document loading cancelled by user") from None

    if not all_docs:
        raise ValueError("No documents could be loaded from any source")

    print("\n📊 Parallel loading complete!")
    print(f"   • Total documents loaded: {len(all_docs)}")
    print()

    logger.info(f"Total: {len(all_docs)} documents from all sources")

    # Split text into chunks
    logger.info("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    doc_splits = text_splitter.split_documents(all_docs)
    logger.info(f"Split into {len(doc_splits)} chunks")

    # Create embeddings
    logger.info("Creating embeddings and vector store...")
    api_key = (
        SecretStr(macsdk_config.google_api_key)
        if macsdk_config.google_api_key
        else None
    )
    embeddings = GoogleGenerativeAIEmbeddings(  # type: ignore[call-arg]
        model=config.embedding_model,
        google_api_key=api_key,
    )

    # Add to ChromaDB
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name=collection_name,
        embedding=embeddings,
        persist_directory=str(config.chroma_db_dir),
    )

    logger.info("Documents indexed successfully")
    print("✅ Documentation indexed successfully!\n")
    result_retriever: VectorStoreRetriever = vectorstore.as_retriever(
        search_kwargs={"k": config.retriever_k}
    )
    return result_retriever
