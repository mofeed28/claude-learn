# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-08

### Added

- SSRF protection: blocks requests to private/loopback IP ranges
- Output path validation: prevents path traversal attacks
- Input validation for URLs, timeouts, and configuration values
- Per-domain locking for race-condition-free rate limiting
- Cache size limits with LRU eviction (max 1000 entries)
- Structured logging throughout the codebase
- GitHub Actions CI with matrix testing (Python 3.10-3.13, 3 OS)
- Ruff linting and formatting configuration
- Mypy type checking configuration
- Security tests for SSRF and path traversal
- Config validation tests
- Shared test fixtures via conftest.py
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
- GitHub issue templates and PR template
- PEP 561 py.typed marker

### Changed

- Semaphore released between retry backoff sleeps (no longer held during wait)
- User agent now uses dynamic version from `__version__`
- URL normalization strips default ports (:443 for https, :80 for http)
- `run_scraper()` refactored into focused helper functions
- Cache write failures now logged instead of silently ignored
- Version bumped to 0.2.0

### Fixed

- Rate limiter race condition with concurrent requests to same domain
- Hardcoded user agent version string

## [0.1.0] - 2025-01-15

### Added

- Initial release
- Async HTTP fetcher with retry, backoff, rate limiting, and caching
- URL queue with scoring, deduplication, and priority sorting
- HTML content extraction with boilerplate stripping
- Sitemap and robots.txt discovery
- CLI with mode selection (quick/default/deep)
- File-based page cache with TTL
- Content deduplication via Jaccard similarity
- Version detection and changelog extraction
