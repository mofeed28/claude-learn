"""Async HTTP fetcher with retry, backoff, rate limiting, and caching."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from .cache import PageCache
from .config import SOFT_FAILURE_SIGNALS, ScrapeConfig

log = logging.getLogger("claude-learn-scraper.fetcher")


def _is_private_url(url: str) -> bool:
    """Check if a URL resolves to a private/loopback IP address (SSRF protection)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return True

    # Block well-known private hostnames
    if hostname in ("localhost", "metadata.google.internal"):
        return True

    # Try parsing as IP address directly
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except ValueError:
        pass

    # Resolve hostname and check all resulting IPs
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for info in infos:
            ip_str = info[4][0]
            addr = ipaddress.ip_address(ip_str)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
                return True
    except (socket.gaierror, OSError):
        pass

    return False


@dataclass
class FetchResult:
    """Result of fetching a single URL."""

    url: str
    content: str
    status_code: int
    success: bool
    error: str = ""
    from_cache: bool = False
    fetch_time_ms: int = 0


class Fetcher:
    """Async HTTP fetcher with retry, rate limiting, and caching.

    Usage:
        config = ScrapeConfig(mode="default")
        fetcher = Fetcher(config)
        results = await fetcher.fetch_batch(["https://...", "https://..."])
        fetcher.close()
    """

    def __init__(self, config: ScrapeConfig) -> None:
        self.config = config
        self.cache = PageCache(
            cache_dir=config.cache_dir,
            ttl=config.cache_ttl,
        )
        self._domain_last_request: dict[str, float] = {}
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.config.user_agent},
                timeout=httpx.Timeout(self.config.request_timeout),
                follow_redirects=True,
                max_redirects=5,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _rate_limit(self, url: str) -> None:
        """Wait if we've hit the same domain too recently (thread-safe)."""
        domain = urlparse(url).netloc
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        async with self._domain_locks[domain]:
            now = time.monotonic()
            last = self._domain_last_request.get(domain, 0)
            wait = self.config.rate_limit_delay - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._domain_last_request[domain] = time.monotonic()

    def _is_soft_failure(self, content: str) -> bool:
        """Check if the content is a soft failure (login wall, empty, boilerplate)."""
        if len(content) < self.config.min_content_length:
            return True

        content_lower = content.lower()
        if any(signal in content_lower for signal in SOFT_FAILURE_SIGNALS):
            # Only flag if the signal appears near the start (first 2000 chars)
            # to avoid flagging pages that mention auth in their docs
            header = content_lower[:2000]
            if any(signal in header for signal in SOFT_FAILURE_SIGNALS):
                return True

        return False

    async def fetch_one(self, url: str) -> FetchResult:
        """Fetch a single URL with retry and caching."""
        # SSRF protection: block private/internal URLs
        if _is_private_url(url):
            log.warning("Blocked private URL: %s", url)
            return FetchResult(
                url=url,
                content="",
                status_code=0,
                success=False,
                error="blocked_private_url",
            )

        # Check cache first
        cached = self.cache.get(url)
        if cached:
            return FetchResult(
                url=url,
                content=cached["content"],
                status_code=cached["status_code"],
                success=True,
                from_cache=True,
            )

        client = await self._get_client()
        last_error = ""

        for attempt in range(self.config.max_retries):
            try:
                await self._rate_limit(url)

                async with self._semaphore:
                    start = time.monotonic()
                    response = await client.get(url)
                    elapsed_ms = int((time.monotonic() - start) * 1000)

                # Don't retry 4xx errors (permanent failures)
                if 400 <= response.status_code < 500:
                    return FetchResult(
                        url=url,
                        content="",
                        status_code=response.status_code,
                        success=False,
                        error=f"HTTP {response.status_code}",
                        fetch_time_ms=elapsed_ms,
                    )

                # Retry 5xx errors
                if response.status_code >= 500:
                    last_error = f"HTTP {response.status_code}"
                    if attempt < self.config.max_retries - 1:
                        backoff = self.config.retry_backoff_base ** (attempt + 1)
                        await asyncio.sleep(backoff)
                        continue
                    return FetchResult(
                        url=url,
                        content="",
                        status_code=response.status_code,
                        success=False,
                        error=last_error,
                        fetch_time_ms=elapsed_ms,
                    )

                content = response.text

                # Check for soft failures
                if self._is_soft_failure(content):
                    return FetchResult(
                        url=url,
                        content=content,
                        status_code=response.status_code,
                        success=False,
                        error="soft_failure",
                        fetch_time_ms=elapsed_ms,
                    )

                # Success — cache it
                self.cache.put(url, content, response.status_code)

                return FetchResult(
                    url=url,
                    content=content,
                    status_code=response.status_code,
                    success=True,
                    fetch_time_ms=elapsed_ms,
                )

            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.retry_backoff_base ** (attempt + 1)
                    await asyncio.sleep(backoff)
                continue

            except Exception as e:
                return FetchResult(
                    url=url,
                    content="",
                    status_code=0,
                    success=False,
                    error=f"Unexpected: {type(e).__name__}: {e}",
                )

        # All retries exhausted
        return FetchResult(
            url=url,
            content="",
            status_code=0,
            success=False,
            error=f"Max retries exceeded: {last_error}",
        )

    async def fetch_batch(self, urls: list[str]) -> list[FetchResult]:
        """Fetch a batch of URLs concurrently."""
        tasks = [self.fetch_one(url) for url in urls]
        return await asyncio.gather(*tasks)
