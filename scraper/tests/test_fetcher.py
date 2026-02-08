"""Tests for async HTTP fetcher — retry, cache, rate limiting, soft failures."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from scraper.config import ScrapeConfig
from scraper.fetcher import Fetcher


@pytest.fixture
def config(tmp_path):
    """Config with fast timeouts for testing."""
    return ScrapeConfig(
        mode="quick",
        cache_dir=str(tmp_path / "cache"),
        request_timeout=2.0,
        max_retries=3,
        retry_backoff_base=0.01,  # near-instant for tests
        rate_limit_delay=0.0,
        cache_ttl=3600,
    )


@pytest.fixture
def config_no_cache(tmp_path):
    """Config with cache disabled."""
    c = ScrapeConfig(
        mode="quick",
        cache_dir=str(tmp_path / "cache"),
        request_timeout=2.0,
        max_retries=2,
        retry_backoff_base=0.01,
        rate_limit_delay=0.0,
    )
    c.cache_ttl = 0
    return c


def make_response(status_code=200, text="<html><body>Hello world content here that is long enough</body></html>"):
    """Create a mock httpx Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    return resp


class TestFetchOne:
    @pytest.mark.asyncio
    async def test_successful_fetch(self, config):
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(200, "x" * 600)
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/docs/page")
        assert result.success is True
        assert result.status_code == 200
        assert result.from_cache is False
        assert result.url == "https://example.com/docs/page"
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_returns_cached_content(self, config):
        fetcher = Fetcher(config)
        # Pre-populate cache
        fetcher.cache.put("https://example.com/docs/page", "cached content", 200)

        result = await fetcher.fetch_one("https://example.com/docs/page")
        assert result.success is True
        assert result.from_cache is True
        assert result.content == "cached content"
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_4xx_no_retry(self, config):
        """4xx errors should NOT be retried."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(404, "")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/missing")
        assert result.success is False
        assert result.status_code == 404
        assert result.error == "HTTP 404"
        # Should only call once (no retry)
        assert mock_client.get.call_count == 1
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_403_no_retry(self, config):
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(403, "")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/private")
        assert result.success is False
        assert result.status_code == 403
        assert mock_client.get.call_count == 1
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_5xx_retries(self, config):
        """5xx errors should trigger retries."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(500, "")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/error")
        assert result.success is False
        assert result.status_code == 500
        # Should have retried max_retries times
        assert mock_client.get.call_count == config.max_retries
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_5xx_then_success(self, config):
        """If a 5xx is followed by 200, should succeed."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            make_response(503, ""),
            make_response(200, "x" * 600),
        ]
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/flaky")
        assert result.success is True
        assert result.status_code == 200
        assert mock_client.get.call_count == 2
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_timeout_retries(self, config):
        """Timeout exceptions should trigger retries."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timed out")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/slow")
        assert result.success is False
        assert "Max retries" in result.error
        assert mock_client.get.call_count == config.max_retries
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_connect_error_retries(self, config):
        """Connection errors should trigger retries."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("connection refused")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/down")
        assert result.success is False
        assert mock_client.get.call_count == config.max_retries
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_unexpected_error_no_retry(self, config):
        """Non-network exceptions should NOT be retried."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.side_effect = ValueError("unexpected")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/weird")
        assert result.success is False
        assert "Unexpected" in result.error
        assert mock_client.get.call_count == 1
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_soft_failure_detected(self, config):
        """Pages with login walls should be flagged as soft failures."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        # Content starts with soft failure signal
        soft_content = "Please sign in to continue. " + "x" * 600
        mock_client.get.return_value = make_response(200, soft_content)
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/gated")
        assert result.success is False
        assert result.error == "soft_failure"
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_short_content_soft_failure(self, config):
        """Content shorter than min_content_length is a soft failure."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(200, "tiny")
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/tiny")
        assert result.success is False
        assert result.error == "soft_failure"
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_success_gets_cached(self, config):
        """Successful fetches should be stored in cache."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        content = "x" * 600
        mock_client.get.return_value = make_response(200, content)
        fetcher._client = mock_client

        await fetcher.fetch_one("https://example.com/docs/cache-me")

        # Verify it's now in cache
        cached = fetcher.cache.get("https://example.com/docs/cache-me")
        assert cached is not None
        assert cached["content"] == content
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_failed_fetch_not_cached(self, config):
        """Failed fetches should NOT be cached."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(404, "")
        fetcher._client = mock_client

        await fetcher.fetch_one("https://example.com/missing")

        cached = fetcher.cache.get("https://example.com/missing")
        assert cached is None
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_time_recorded(self, config):
        """fetch_time_ms should be a positive number."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(200, "x" * 600)
        fetcher._client = mock_client

        result = await fetcher.fetch_one("https://example.com/docs/timed")
        assert result.fetch_time_ms >= 0
        await fetcher.close()


class TestFetchBatch:
    @pytest.mark.asyncio
    async def test_fetches_multiple_urls(self, config):
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(200, "x" * 600)
        fetcher._client = mock_client

        results = await fetcher.fetch_batch(
            [
                "https://example.com/docs/a",
                "https://example.com/docs/b",
                "https://example.com/docs/c",
            ]
        )
        assert len(results) == 3
        assert all(r.success for r in results)
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_empty_batch(self, config):
        fetcher = Fetcher(config)
        results = await fetcher.fetch_batch([])
        assert results == []
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_mixed_results(self, config):
        """Batch with some successes and some failures."""
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            make_response(200, "x" * 600),
            make_response(404, ""),
            make_response(200, "y" * 600),
        ]
        fetcher._client = mock_client

        results = await fetcher.fetch_batch(
            [
                "https://example.com/docs/ok1",
                "https://example.com/missing",
                "https://example.com/docs/ok2",
            ]
        )
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        assert len(successes) == 2
        assert len(failures) == 1
        await fetcher.close()


class TestSoftFailureDetection:
    @pytest.mark.asyncio
    async def test_access_denied_detected(self, config):
        fetcher = Fetcher(config)
        assert fetcher._is_soft_failure("access denied please login" + "x" * 600) is True
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_enable_javascript_detected(self, config):
        fetcher = Fetcher(config)
        assert fetcher._is_soft_failure("Please enable javascript to view this page" + "x" * 600) is True
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_normal_content_not_flagged(self, config):
        fetcher = Fetcher(config)
        content = "Welcome to the API documentation. Here's how to authenticate your requests. " + "x" * 600
        assert fetcher._is_soft_failure(content) is False
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_auth_in_body_not_flagged(self, config):
        """Auth keywords deep in the body (not header) should not trigger."""
        fetcher = Fetcher(config)
        # "sign in" appears after the first 2000 chars
        content = "A" * 2500 + " sign in to your account " + "B" * 600
        assert fetcher._is_soft_failure(content) is False
        await fetcher.close()


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, tmp_path):
        """Sequential requests to same domain should be delayed."""
        config = ScrapeConfig(
            mode="quick",
            cache_dir=str(tmp_path / "cache"),
            rate_limit_delay=0.1,
            max_retries=1,
            retry_backoff_base=0.01,
            request_timeout=2.0,
        )
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(200, "x" * 600)
        fetcher._client = mock_client

        import time

        start = time.monotonic()
        await fetcher.fetch_one("https://example.com/docs/a")
        await fetcher.fetch_one("https://example.com/docs/b")
        elapsed = time.monotonic() - start

        # Second request should have been delayed by at least rate_limit_delay
        assert elapsed >= 0.08  # allow small tolerance
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_different_domains_no_delay(self, tmp_path):
        """Requests to different domains should NOT be delayed."""
        config = ScrapeConfig(
            mode="quick",
            cache_dir=str(tmp_path / "cache"),
            rate_limit_delay=0.5,
            max_retries=1,
            retry_backoff_base=0.01,
            request_timeout=2.0,
        )
        fetcher = Fetcher(config)
        mock_client = AsyncMock()
        mock_client.get.return_value = make_response(200, "x" * 600)
        fetcher._client = mock_client

        import time

        start = time.monotonic()
        await fetcher.fetch_one("https://a.com/docs/page")
        await fetcher.fetch_one("https://b.com/docs/page")
        elapsed = time.monotonic() - start

        # Should be fast since different domains
        assert elapsed < 0.4
        await fetcher.close()
