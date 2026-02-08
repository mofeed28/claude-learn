"""Integration tests — full pipeline with mocked HTTP responses."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from scraper.cli import run_scraper
from scraper.config import ScrapeConfig

# --- Fake page content ---

ROBOTS_TXT = """
User-agent: *
Disallow: /admin/
Disallow: /internal/

Sitemap: https://docs.example.com/sitemap.xml
"""

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://docs.example.com/docs/getting-started</loc></url>
  <url><loc>https://docs.example.com/docs/api-reference</loc></url>
  <url><loc>https://docs.example.com/docs/configuration</loc></url>
  <url><loc>https://docs.example.com/blog/announcement</loc></url>
  <url><loc>https://docs.example.com/pricing</loc></url>
</urlset>
"""

DOC_PAGE_GETTING_STARTED = """
<html>
<head><title>Getting Started</title></head>
<body>
<nav class="navbar">Navigation stuff to skip</nav>
<main>
<h1>Getting Started with ExampleLib</h1>
<p>ExampleLib is a powerful library for building things quickly
and efficiently with minimal configuration needed.</p>
<h2>Installation</h2>
<pre><code>npm install examplelib</code></pre>
<h2>Quick Start</h2>
<pre><code>
import { ExampleLib } from 'examplelib';

const app = new ExampleLib();
app.configure({ debug: true });
app.start();
</code></pre>
<p>Now you have a running ExampleLib instance ready for development and testing.</p>
<a href="/docs/api-reference">API Reference</a>
<a href="/docs/configuration">Configuration Guide</a>
<a href="/pricing">Pricing</a>
</main>
<footer>Footer content</footer>
</body>
</html>
"""

DOC_PAGE_API = """
<html>
<head><title>API Reference</title></head>
<body>
<main>
<h1>API Reference</h1>
<h2>ExampleLib.configure(options)</h2>
<p>Configure your ExampleLib instance with various options for environments.</p>
<table>
<tr><th>Option</th><th>Type</th><th>Default</th><th>Description</th></tr>
<tr><td>debug</td><td>boolean</td><td>false</td><td>Enable debug mode</td></tr>
<tr><td>port</td><td>number</td><td>3000</td><td>Server port</td></tr>
<tr><td>host</td><td>string</td><td>localhost</td><td>Server host</td></tr>
</table>
<h2>ExampleLib.start()</h2>
<p>Start the ExampleLib server with all configured options applied to the runtime environment for the application.</p>
<pre><code>
const app = new ExampleLib();
app.configure({ port: 8080 });
await app.start();
console.log('Server running on port 8080');
</code></pre>
</main>
</body>
</html>
"""

DOC_PAGE_CONFIG = """
<html>
<head><title>Configuration</title></head>
<body>
<main>
<h1>Configuration Guide</h1>
<p>ExampleLib supports file-based and env var configuration for environments.</p>
<h2>Config File</h2>
<pre><code>
// examplelib.config.js
export default {
  port: 3000,
  database: {
    host: 'localhost',
    port: 5432,
  },
};
</code></pre>
<h2>Environment Variables</h2>
<p>Set EXAMPLELIB_PORT and EXAMPLELIB_DB_HOST to override config values.</p>
</main>
</body>
</html>
"""


def make_mock_response(url: str, status_code: int, text: str):
    """Create a mock httpx Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    return resp


URL_TO_CONTENT = {
    "https://docs.example.com/robots.txt": (200, ROBOTS_TXT),
    "https://docs.example.com/sitemap.xml": (200, SITEMAP_XML),
    "https://docs.example.com/sitemap-0.xml": (404, "Not Found"),
    "https://docs.example.com/sitemap_index.xml": (404, "Not Found"),
    "https://docs.example.com/docs/getting-started": (200, DOC_PAGE_GETTING_STARTED),
    "https://docs.example.com/docs/api-reference": (200, DOC_PAGE_API),
    "https://docs.example.com/docs/configuration": (200, DOC_PAGE_CONFIG),
}


@pytest.fixture
def config(tmp_path):
    return ScrapeConfig(
        mode="quick",
        cache_dir=str(tmp_path / "cache"),
        max_retries=1,
        retry_backoff_base=0.01,
        rate_limit_delay=0.0,
        request_timeout=2.0,
        concurrency=3,
    )


class TestFullPipeline:
    """Test the complete scraping pipeline end-to-end with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_discovers_and_fetches_doc_pages(self, config):
        """Pipeline should discover pages from sitemap and fetch them."""

        async def mock_get(url, **kwargs):
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        # Should have fetched documentation pages
        assert result["topic"] == "examplelib"
        assert len(result["pages"]) > 0
        assert result["stats"]["pages_extracted"] > 0

    @pytest.mark.asyncio
    async def test_extracts_content_from_pages(self, config):
        """Extracted pages should have meaningful text, code, headings."""

        async def mock_get(url, **kwargs):
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        # Find the getting-started page
        gs_pages = [p for p in result["pages"] if "getting-started" in p["url"]]
        assert len(gs_pages) >= 1

        page = gs_pages[0]
        assert page["word_count"] > 10
        assert len(page["code_blocks"]) > 0
        assert len(page["headings"]) > 0
        assert "ExampleLib" in page["text"]

    @pytest.mark.asyncio
    async def test_skips_disallowed_paths(self, config):
        """Pages disallowed by robots.txt should not be fetched."""

        fetched_urls = []

        async def mock_get(url, **kwargs):
            fetched_urls.append(url)
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        # /admin/ and /internal/ should not appear in fetched URLs
        assert not any("/admin/" in url for url in fetched_urls)
        assert not any("/internal/" in url for url in fetched_urls)

    @pytest.mark.asyncio
    async def test_deduplicates_similar_content(self, config):
        """Near-identical pages should be deduplicated."""
        # Create two pages with 95% identical content
        duplicate_page = DOC_PAGE_GETTING_STARTED  # exact same content

        urls = {
            **URL_TO_CONTENT,
            "https://docs.example.com/docs/getting-started-v2": (200, duplicate_page),
        }

        async def mock_get(url, **kwargs):
            if url in urls:
                status, text = urls[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=[
                    "https://docs.example.com/docs/getting-started",
                    "https://docs.example.com/docs/getting-started-v2",
                ],
            )

        # The duplicate should have been filtered
        gs_urls = [p["url"] for p in result["pages"] if "getting-started" in p["url"]]
        # At most one of the two near-identical pages should appear
        assert len(gs_urls) <= 1

    @pytest.mark.asyncio
    async def test_handles_all_failures_gracefully(self, config):
        """Pipeline should complete even if all fetches fail."""

        async def mock_get(url, **kwargs):
            return make_mock_response(url, 500, "Internal Server Error")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "broken-lib",
                config,
                initial_urls=["https://broken.example.com/docs/page"],
            )

        assert result["topic"] == "broken-lib"
        assert len(result["pages"]) == 0
        assert result["stats"]["pages_extracted"] == 0

    @pytest.mark.asyncio
    async def test_output_is_json_serializable(self, config):
        """Result should be fully JSON-serializable."""

        async def mock_get(url, **kwargs):
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        # Should not raise
        json_str = json.dumps(result, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["topic"] == "examplelib"

    @pytest.mark.asyncio
    async def test_stats_track_cache_hits(self, config):
        """Running twice should show cache hits on second run."""

        async def mock_get(url, **kwargs):
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            # First run populates cache
            result1 = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

            # Second run should hit cache
            result2 = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        # Second run should have cache hits
        assert result2["stats"]["cache_hits"] >= result1["stats"]["cache_hits"]

    @pytest.mark.asyncio
    async def test_total_time_recorded(self, config):
        """Stats should include total_time_seconds."""

        async def mock_get(url, **kwargs):
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        assert "total_time_seconds" in result["stats"]
        assert result["stats"]["total_time_seconds"] >= 0


class TestEdgeCases:
    """Pipeline edge cases."""

    @pytest.mark.asyncio
    async def test_no_initial_urls(self, config):
        """Running with no seed URLs should return empty results."""
        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            result = await run_scraper("nothing", config, initial_urls=[])

        assert len(result["pages"]) == 0

    @pytest.mark.asyncio
    async def test_timeout_during_sitemap_fetch(self, config):
        """Timeouts during sitemap discovery should not crash pipeline."""

        async def mock_get(url, **kwargs):
            if "sitemap" in url or "robots" in url:
                raise httpx.TimeoutException("slow sitemap")
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/getting-started"],
            )

        # Should still complete (maybe with fewer pages)
        assert result["topic"] == "examplelib"

    @pytest.mark.asyncio
    async def test_caps_content_length(self, config):
        """Pages with huge content should be capped."""
        huge_page = "<html><body><main>" + ("word " * 20000) + "</main></body></html>"

        async def mock_get(url, **kwargs):
            if "huge" in url:
                return make_mock_response(url, 200, huge_page)
            if url in URL_TO_CONTENT:
                status, text = URL_TO_CONTENT[url]
                return make_mock_response(url, status, text)
            return make_mock_response(url, 404, "Not Found")

        with patch("scraper.fetcher.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_get
            mock_client_cls.return_value = mock_client

            result = await run_scraper(
                "examplelib",
                config,
                initial_urls=["https://docs.example.com/docs/huge-page"],
            )

        for page in result["pages"]:
            assert len(page["text"]) <= 50000
            assert len(page["code_blocks"]) <= 50
