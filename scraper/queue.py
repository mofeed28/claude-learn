"""URL queue with scoring, deduplication, and priority sorting."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from .config import (
    SCORE_OFFICIAL_API, SCORE_SITEMAP_DOC, SCORE_OFFICIAL_GUIDE,
    SCORE_GITHUB_README, SCORE_REGISTRY, SCORE_WIKI, SCORE_BLOG,
    SCORE_STACKOVERFLOW, SCORE_WAYBACK, SCORE_UNKNOWN,
    DOC_PATH_PATTERNS, SKIP_PATH_PATTERNS,
)


@dataclass
class ScoredURL:
    """A URL with a priority score and metadata."""
    url: str
    score: int
    source: str = ""  # where we found this URL
    depth: int = 0    # 0 = from search, 1 = from link crawling

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, ScoredURL):
            return self.url == other.url
        return False


# Tracking params to strip during normalization
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "source", "fbclid", "gclid", "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication.

    - Lowercase the scheme and domain
    - Strip trailing slashes
    - Remove fragments
    - Remove tracking parameters
    """
    parsed = urlparse(url)

    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip trailing slash from path (but keep root /)
    path = parsed.path.rstrip("/") or "/"

    # Remove tracking params
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {k: v for k, v in params.items() if k.lower() not in _TRACKING_PARAMS}
        query = urlencode(filtered, doseq=True) if filtered else ""
    else:
        query = ""

    # Drop fragment entirely
    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def score_url(url: str) -> int:
    """Auto-score a URL based on its domain and path patterns."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    # Official API reference pages
    if any(p in path for p in ["/api/", "/reference/"]):
        return SCORE_OFFICIAL_API

    # Sitemap-discovered doc pages
    if any(p in path for p in DOC_PATH_PATTERNS):
        return SCORE_OFFICIAL_GUIDE

    # GitHub raw / docs
    if "raw.githubusercontent.com" in domain:
        return SCORE_GITHUB_README
    if "github.com" in domain and ("/wiki/" in path or "/blob/" in path):
        return SCORE_WIKI

    # Package registries
    if any(reg in domain for reg in [
        "npmjs.com", "pypi.org", "crates.io", "pkg.go.dev",
        "rubygems.org", "hex.pm",
    ]):
        return SCORE_REGISTRY

    # Blog/tutorial sources
    if any(blog in domain for blog in ["dev.to", "medium.com", "hashnode.dev"]):
        return SCORE_BLOG

    # StackOverflow
    if "stackoverflow.com" in domain:
        return SCORE_STACKOVERFLOW

    # Wayback Machine
    if "web.archive.org" in domain:
        return SCORE_WAYBACK

    # Default: could be official docs (scored higher) or random
    if any(p in path for p in DOC_PATH_PATTERNS):
        return SCORE_OFFICIAL_GUIDE

    return SCORE_UNKNOWN


def should_skip_url(url: str) -> bool:
    """Check if a URL should be skipped (non-doc paths, anchors only, etc.)."""
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Skip anchor-only URLs
    if not path or path == "/":
        return bool(parsed.fragment and not parsed.query)

    # Skip non-doc paths (match with or without trailing slash)
    path_with_slash = path if path.endswith("/") else path + "/"
    if any(p in path_with_slash for p in SKIP_PATH_PATTERNS):
        return True

    # Skip non-HTTP schemes
    if parsed.scheme not in ("http", "https", ""):
        return True

    # Skip file downloads
    if any(path.endswith(ext) for ext in [".zip", ".tar.gz", ".exe", ".dmg", ".png", ".jpg", ".gif", ".svg", ".ico"]):
        return True

    return False


class URLQueue:
    """Priority queue of URLs to fetch, with deduplication."""

    def __init__(self, max_size: int = 25):
        self.max_size = max_size
        self._urls: dict[str, ScoredURL] = {}  # normalized_url -> ScoredURL
        self._fetched: set[str] = set()

    def add(self, url: str, score: int | None = None, source: str = "", depth: int = 0) -> bool:
        """Add a URL to the queue. Returns True if added (not duplicate)."""
        if should_skip_url(url):
            return False

        normalized = normalize_url(url)

        # Skip if already fetched
        if normalized in self._fetched:
            return False

        # Auto-score if not provided
        if score is None:
            score = score_url(url)

        entry = ScoredURL(url=url, score=score, source=source, depth=depth)

        # If we already have this URL, keep the higher score
        if normalized in self._urls:
            if score > self._urls[normalized].score:
                self._urls[normalized] = entry
            return False

        self._urls[normalized] = entry
        return True

    def add_many(self, urls: list[str], score: int | None = None, source: str = "", depth: int = 0) -> int:
        """Add multiple URLs. Returns count of new URLs added."""
        return sum(1 for url in urls if self.add(url, score, source, depth))

    def mark_fetched(self, url: str):
        """Mark a URL as fetched so it won't be re-added."""
        normalized = normalize_url(url)
        self._fetched.add(normalized)
        self._urls.pop(normalized, None)

    def get_batch(self, size: int = 5) -> list[ScoredURL]:
        """Get the next batch of highest-priority URLs to fetch.

        Returns up to `size` URLs, sorted by score (highest first),
        then by path length (shorter = more important).
        """
        remaining = [
            entry for norm_url, entry in self._urls.items()
            if norm_url not in self._fetched
        ]

        # Sort: highest score first, then shortest path
        remaining.sort(key=lambda e: (-e.score, len(urlparse(e.url).path)))

        batch = remaining[:size]

        return batch

    def mark_batch_fetched(self, batch: list[ScoredURL]):
        """Mark all URLs in a batch as fetched."""
        for entry in batch:
            self.mark_fetched(entry.url)

    @property
    def pending_count(self) -> int:
        """Number of URLs not yet fetched."""
        return len([
            u for u in self._urls
            if u not in self._fetched
        ])

    @property
    def fetched_count(self) -> int:
        return len(self._fetched)

    @property
    def total_count(self) -> int:
        return len(self._urls) + len(self._fetched)

    def get_all_sorted(self) -> list[ScoredURL]:
        """Get all pending URLs sorted by priority."""
        remaining = [
            entry for norm_url, entry in self._urls.items()
            if norm_url not in self._fetched
        ]
        remaining.sort(key=lambda e: (-e.score, len(urlparse(e.url).path)))
        return remaining[:self.max_size]
