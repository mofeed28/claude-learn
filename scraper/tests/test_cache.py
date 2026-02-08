"""Tests for the file-based page cache."""

import time

import pytest

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


class TestCacheEviction:
    def test_evict_expired_removes_old_entries(self, tmp_path):
        cache = PageCache(cache_dir=str(tmp_path), ttl=0)
        cache.put("https://a.com", "A")
        cache.put("https://b.com", "B")
        time.sleep(0.01)
        cache.evict_expired()
        assert cache.size == 0

    def test_evict_expired_keeps_fresh_entries(self, tmp_path):
        cache = PageCache(cache_dir=str(tmp_path), ttl=3600)
        cache.put("https://a.com", "A")
        cache.put("https://b.com", "B")
        cache.evict_expired()
        assert cache.size == 2

    def test_evict_expired_handles_corrupt_files(self, tmp_path):
        cache = PageCache(cache_dir=str(tmp_path), ttl=3600)
        # Write a corrupt JSON file
        corrupt_path = tmp_path / "corrupt.json"
        corrupt_path.write_text("not valid json {{{")
        cache.evict_expired()
        # Corrupt file should be removed
        assert not corrupt_path.exists()

    def test_max_entries_evicts_oldest(self, tmp_path):
        cache = PageCache(cache_dir=str(tmp_path), ttl=3600, max_entries=3)
        cache.put("https://a.com", "A")
        time.sleep(0.01)
        cache.put("https://b.com", "B")
        time.sleep(0.01)
        cache.put("https://c.com", "C")
        time.sleep(0.01)
        # This should trigger eviction of the oldest entry
        cache.put("https://d.com", "D")
        assert cache.size == 3
        # Oldest entry (a.com) should have been evicted
        assert cache.get("https://a.com") is None
        assert cache.get("https://d.com") is not None

    def test_evict_oldest_removes_correct_count(self, tmp_path):
        cache = PageCache(cache_dir=str(tmp_path), ttl=3600, max_entries=2)
        cache.put("https://a.com", "A")
        time.sleep(0.01)
        cache.put("https://b.com", "B")
        time.sleep(0.01)
        cache.put("https://c.com", "C")
        assert cache.size == 2
