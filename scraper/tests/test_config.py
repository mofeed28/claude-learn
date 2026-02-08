"""Tests for ScrapeConfig validation and mode adjustments."""

import pytest

from scraper import __version__
from scraper.config import ScrapeConfig


class TestModeAdjustments:
    def test_quick_mode_sets_max_urls_5(self):
        config = ScrapeConfig(mode="quick")
        assert config.max_urls == 5

    def test_quick_mode_sets_concurrency_3(self):
        config = ScrapeConfig(mode="quick")
        assert config.concurrency == 3

    def test_default_mode_keeps_defaults(self):
        config = ScrapeConfig(mode="default")
        assert config.max_urls == 12
        assert config.concurrency == 5

    def test_deep_mode_sets_max_urls_25(self):
        config = ScrapeConfig(mode="deep")
        assert config.max_urls == 25

    def test_deep_mode_sets_concurrency_8(self):
        config = ScrapeConfig(mode="deep")
        assert config.concurrency == 8


class TestValidation:
    def test_rejects_invalid_mode(self):
        with pytest.raises(ValueError, match="Invalid mode"):
            ScrapeConfig(mode="turbo")

    def test_rejects_zero_timeout(self):
        with pytest.raises(ValueError, match="Invalid timeout"):
            ScrapeConfig(request_timeout=0)

    def test_rejects_negative_timeout(self):
        with pytest.raises(ValueError, match="Invalid timeout"):
            ScrapeConfig(request_timeout=-5)

    def test_rejects_timeout_over_300(self):
        with pytest.raises(ValueError, match="Invalid timeout"):
            ScrapeConfig(request_timeout=301)

    def test_accepts_timeout_at_300(self):
        config = ScrapeConfig(request_timeout=300)
        assert config.request_timeout == 300

    def test_rejects_zero_concurrency(self):
        with pytest.raises(ValueError, match="Invalid concurrency"):
            ScrapeConfig(concurrency=0)

    def test_rejects_concurrency_over_50(self):
        with pytest.raises(ValueError, match="Invalid concurrency"):
            ScrapeConfig(concurrency=51)

    def test_rejects_zero_max_retries(self):
        with pytest.raises(ValueError, match="Invalid max_retries"):
            ScrapeConfig(max_retries=0)

    def test_rejects_max_retries_over_10(self):
        with pytest.raises(ValueError, match="Invalid max_retries"):
            ScrapeConfig(max_retries=11)


class TestUserAgent:
    def test_default_user_agent_includes_version(self):
        config = ScrapeConfig()
        assert __version__ in config.user_agent

    def test_default_user_agent_format(self):
        config = ScrapeConfig()
        assert config.user_agent == f"claude-learn-scraper/{__version__}"

    def test_custom_user_agent_preserved(self):
        config = ScrapeConfig(user_agent="my-custom-agent/1.0")
        assert config.user_agent == "my-custom-agent/1.0"
