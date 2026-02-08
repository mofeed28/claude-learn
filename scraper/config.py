"""Configuration and constants for the scraper."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScrapeConfig:
    """Scraping configuration, adjustable by depth mode."""

    # Depth mode: "quick", "default", "deep"
    mode: str = "default"

    # Maximum URLs to fetch
    max_urls: int = 12

    # Concurrent fetch limit
    concurrency: int = 5

    # Retry settings
    max_retries: int = 3
    retry_backoff_base: float = 2.0  # seconds: 2, 4, 8

    # Rate limiting (seconds between requests to same domain)
    rate_limit_delay: float = 0.5

    # Cache TTL in seconds (6 hours)
    cache_ttl: int = 21600

    # Request timeout in seconds
    request_timeout: float = 15.0

    # User agent
    user_agent: str = "claude-learn-scraper/0.1"

    # Soft failure detection
    min_content_length: int = 500

    # Cache directory
    cache_dir: str = "~/.cache/claude-learn"

    # Playwright (JS rendering) settings
    use_playwright: bool = False
    playwright_timeout: int = 15000  # ms

    def __post_init__(self) -> None:
        # Validate configuration
        if self.mode not in ("quick", "default", "deep"):
            raise ValueError(f"Invalid mode: {self.mode!r}. Must be 'quick', 'default', or 'deep'.")
        if self.request_timeout <= 0 or self.request_timeout > 300:
            raise ValueError(f"Invalid timeout: {self.request_timeout}. Must be between 0 and 300.")
        if self.concurrency < 1 or self.concurrency > 50:
            raise ValueError(f"Invalid concurrency: {self.concurrency}. Must be between 1 and 50.")
        if self.max_retries < 1 or self.max_retries > 10:
            raise ValueError(f"Invalid max_retries: {self.max_retries}. Must be between 1 and 10.")

        # Set version-aware user agent
        from scraper import __version__

        if self.user_agent == "claude-learn-scraper/0.1":
            self.user_agent = f"claude-learn-scraper/{__version__}"

        # Mode-based adjustments
        if self.mode == "quick":
            self.max_urls = 5
            self.concurrency = 3
        elif self.mode == "deep":
            self.max_urls = 25
            self.concurrency = 8


# URL score constants
SCORE_OFFICIAL_API = 5
SCORE_SITEMAP_DOC = 5
SCORE_OFFICIAL_GUIDE = 4
SCORE_GITHUB_README = 4
SCORE_REGISTRY = 3
SCORE_WIKI = 3
SCORE_BLOG = 2
SCORE_STACKOVERFLOW = 2
SCORE_WAYBACK = 1
SCORE_UNKNOWN = 1

# Patterns for doc URLs
DOC_PATH_PATTERNS = [
    "/docs/",
    "/api/",
    "/guide/",
    "/reference/",
    "/tutorial/",
    "/getting-started/",
    "/handbook/",
    "/manual/",
    "/learn/",
    "/quickstart/",
]

# Patterns to skip
SKIP_PATH_PATTERNS = [
    "/blog/",
    "/pricing/",
    "/login/",
    "/signup/",
    "/careers/",
    "/about/",
    "/contact/",
    "/legal/",
    "/privacy/",
    "/terms/",
    "/press/",
    "/news/",
]

# Soft failure signals
SOFT_FAILURE_SIGNALS = [
    "sign in",
    "access denied",
    "log in to continue",
    "enable javascript",
    "403 forbidden",
    "404 not found",
    "page not found",
    "unauthorized",
    "please log in",
]
