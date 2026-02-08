"""Shared test fixtures for the scraper test suite."""

import pytest

from scraper.cache import PageCache
from scraper.config import ScrapeConfig


@pytest.fixture
def config():
    """Create a default ScrapeConfig for tests."""
    return ScrapeConfig(mode="default")


@pytest.fixture
def quick_config():
    """Create a quick-mode ScrapeConfig for tests."""
    return ScrapeConfig(mode="quick")


@pytest.fixture
def deep_config():
    """Create a deep-mode ScrapeConfig for tests."""
    return ScrapeConfig(mode="deep")


@pytest.fixture
def cache(tmp_path):
    """Create a cache in a temporary directory."""
    return PageCache(cache_dir=str(tmp_path), ttl=3600)


@pytest.fixture
def no_cache_config(tmp_path):
    """Create a ScrapeConfig with cache disabled."""
    cfg = ScrapeConfig(mode="quick", cache_dir=str(tmp_path))
    cfg.cache_ttl = 0
    return cfg
