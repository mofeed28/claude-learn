"""File-based cache for scraped pages."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

log = logging.getLogger("claude-learn-scraper.cache")


class PageCache:
    """Simple file-based cache with TTL support.

    Cache entries are stored as JSON files in a directory, keyed by URL hash.
    Each entry includes the content, headers, status code, and expiry time.
    """

    def __init__(self, cache_dir: str = "~/.cache/claude-learn", ttl: int = 21600, max_entries: int = 1000):
        self.cache_dir = Path(os.path.expanduser(cache_dir))
        self.ttl = ttl  # seconds
        self.max_entries = max_entries
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _path(self, url: str) -> Path:
        return self.cache_dir / f"{self._key(url)}.json"

    def get(self, url: str) -> dict | None:
        """Get a cached page. Returns None if not cached or expired."""
        path = self._path(url)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

        # Check TTL
        if time.time() > data.get("expires_at", 0):
            path.unlink(missing_ok=True)
            return None

        return dict(data)

    def put(self, url: str, content: str, status_code: int = 200, headers: dict | None = None) -> None:
        """Cache a page. Evicts old entries if over max_entries."""
        # Evict if over limit
        if self.size >= self.max_entries:
            self.evict_expired()
            # If still over limit, evict oldest entries
            if self.size >= self.max_entries:
                self._evict_oldest(self.size - self.max_entries + 1)

        data = {
            "url": url,
            "content": content,
            "status_code": status_code,
            "headers": headers or {},
            "cached_at": time.time(),
            "expires_at": time.time() + self.ttl,
        }
        path = self._path(url)
        try:
            path.write_text(json.dumps(data, ensure_ascii=False))
        except OSError as e:
            log.warning("Cache write failed for %s: %s", url, e)

    def _evict_oldest(self, count: int) -> None:
        """Evict the oldest `count` cache entries."""
        entries = []
        for path in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                entries.append((data.get("cached_at", 0), path))
            except (json.JSONDecodeError, OSError):
                path.unlink(missing_ok=True)

        entries.sort(key=lambda x: x[0])
        for _, path in entries[:count]:
            path.unlink(missing_ok=True)

    def has(self, url: str) -> bool:
        """Check if a URL is cached and not expired."""
        return self.get(url) is not None

    def clear(self) -> None:
        """Clear all cached entries."""
        for path in self.cache_dir.glob("*.json"):
            path.unlink(missing_ok=True)

    def evict_expired(self) -> None:
        """Remove all expired entries."""
        now = time.time()
        for path in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                if now > data.get("expires_at", 0):
                    path.unlink(missing_ok=True)
            except (json.JSONDecodeError, OSError):
                path.unlink(missing_ok=True)

    @property
    def size(self) -> int:
        """Number of cached entries (including expired)."""
        return len(list(self.cache_dir.glob("*.json")))
