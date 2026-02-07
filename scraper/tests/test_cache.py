"""Tests for the file-based page cache."""

import json
import time
import pytest
from pathlib import Path

from scraper.cache import PageCache


@pytest.fixture
def cache(tmp_path):
    """Create a cache in a temporary directory."""
    return PageCache(cache_dir=str(tmp_path), ttl=3600)


class TestPageCache:
    def test_put_and_get(self, cache):
        cache.put("https://example.com", "Hello World", 200)
        result = cache.get("https://example.com")
        assert result is not None
        assert result["content"] == "Hello World"
        assert result["status_code"] == 200

    def test_miss_returns_none(self, cache):
        assert cache.get("https://nonexistent.com") is None

    def test_expired_returns_none(self, tmp_path):
        cache = PageCache(cache_dir=str(tmp_path), ttl=0)  # expires immediately
        cache.put("https://example.com", "Hello")
        # Need to actually wait a tiny bit for time to advance
        import time
        time.sleep(0.01)
        assert cache.get("https://example.com") is None

    def test_has(self, cache):
        assert cache.has("https://example.com") is False
        cache.put("https://example.com", "Hello")
        assert cache.has("https://example.com") is True

    def test_clear(self, cache):
        cache.put("https://a.com", "A")
        cache.put("https://b.com", "B")
        assert cache.size == 2
        cache.clear()
        assert cache.size == 0

    def test_different_urls_different_keys(self, cache):
        cache.put("https://a.com/docs", "Doc A")
        cache.put("https://b.com/docs", "Doc B")
        assert cache.get("https://a.com/docs")["content"] == "Doc A"
        assert cache.get("https://b.com/docs")["content"] == "Doc B"

    def test_overwrite(self, cache):
        cache.put("https://example.com", "Old content")
        cache.put("https://example.com", "New content")
        result = cache.get("https://example.com")
        assert result["content"] == "New content"

    def test_size(self, cache):
        assert cache.size == 0
        cache.put("https://a.com", "A")
        assert cache.size == 1
        cache.put("https://b.com", "B")
        assert cache.size == 2
