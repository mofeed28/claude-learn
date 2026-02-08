"""Tests for CLI entry point — argument parsing, config wiring, output format."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.cli import build_parser, main, run_scraper
from scraper.config import ScrapeConfig


class TestBuildParser:
    def test_requires_topic(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_topic(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.topic == "hono"

    def test_default_mode_is_default(self):
        parser = build_parser()
        args = parser.parse_args(["stripe"])
        assert args.mode == "default"

    def test_accepts_quick_mode(self):
        parser = build_parser()
        args = parser.parse_args(["stripe", "--mode", "quick"])
        assert args.mode == "quick"

    def test_accepts_deep_mode(self):
        parser = build_parser()
        args = parser.parse_args(["stripe", "--mode", "deep"])
        assert args.mode == "deep"

    def test_rejects_invalid_mode(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["stripe", "--mode", "invalid"])

    def test_parses_urls(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "--urls", "https://a.com", "https://b.com"])
        assert args.urls == ["https://a.com", "https://b.com"]

    def test_default_urls_empty(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.urls == []

    def test_parses_cache_dir(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "--cache-dir", "/tmp/cache"])
        assert args.cache_dir == "/tmp/cache"

    def test_default_cache_dir(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.cache_dir == "~/.cache/claude-learn"

    def test_no_cache_flag(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "--no-cache"])
        assert args.no_cache is True

    def test_no_cache_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.no_cache is False

    def test_parses_timeout(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "--timeout", "30"])
        assert args.timeout == 30.0

    def test_default_timeout(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.timeout == 15.0

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "--verbose"])
        assert args.verbose is True

    def test_verbose_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "-v"])
        assert args.verbose is True

    def test_verbose_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.verbose is False

    def test_output_flag(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "--output", "result.json"])
        assert args.output == "result.json"

    def test_output_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["hono", "-o", "out.json"])
        assert args.output == "out.json"

    def test_output_default_none(self):
        parser = build_parser()
        args = parser.parse_args(["hono"])
        assert args.output is None


class TestMainWiring:
    """Test that main() correctly wires args to ScrapeConfig and run_scraper."""

    @patch("scraper.cli.asyncio")
    @patch("scraper.cli.json")
    @patch("scraper.cli.sys")
    def test_main_creates_config_from_args(self, mock_sys, mock_json, mock_asyncio):
        """main() should create a ScrapeConfig matching CLI args."""

        # Consume the coroutine to avoid RuntimeWarning
        def consume_coro(coro):
            coro.close()
            return {"topic": "hono", "pages": [], "stats": {}, "urls_fetched": []}

        mock_asyncio.run.side_effect = consume_coro

        with patch("scraper.cli.build_parser") as mock_parser_fn:
            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = MagicMock(
                topic="hono",
                mode="deep",
                urls=["https://hono.dev"],
                cache_dir="/tmp/test",
                no_cache=False,
                timeout=20.0,
                verbose=False,
                output=None,
            )
            mock_parser_fn.return_value = mock_parser
            main()

        # asyncio.run was called with a coroutine
        mock_asyncio.run.assert_called_once()

    @patch("scraper.cli.asyncio")
    @patch("scraper.cli.json")
    @patch("scraper.cli.sys")
    def test_main_disables_cache_when_flagged(self, mock_sys, mock_json, mock_asyncio):
        mock_asyncio.run.return_value = {"topic": "t", "pages": [], "stats": {}, "urls_fetched": []}

        with patch("scraper.cli.build_parser") as mock_parser_fn:
            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = MagicMock(
                topic="t",
                mode="default",
                urls=[],
                cache_dir="~/.cache/test",
                no_cache=True,
                timeout=15.0,
                verbose=False,
                output=None,
            )
            mock_parser_fn.return_value = mock_parser

            # Capture the config that gets created
            captured_configs = []

            async def mock_run(topic, config, initial_urls=None, verbose=False):
                captured_configs.append(config)
                return {"topic": topic, "pages": [], "stats": {}, "urls_fetched": [], "version": None, "changelog": []}

            with patch("scraper.cli.run_scraper", side_effect=mock_run):
                # asyncio.run should call the coroutine
                def run_coro(coro):
                    import asyncio

                    loop = asyncio.new_event_loop()
                    try:
                        return loop.run_until_complete(coro)
                    finally:
                        loop.close()

                mock_asyncio.run.side_effect = run_coro
                main()

            assert len(captured_configs) == 1
            assert captured_configs[0].cache_ttl == 0

    @patch("scraper.cli.asyncio")
    @patch("scraper.cli.sys")
    def test_main_outputs_json_to_stdout(self, mock_sys, mock_asyncio):
        result_data = {
            "topic": "test",
            "pages": [{"url": "https://test.com"}],
            "stats": {"pages_extracted": 1},
            "urls_fetched": ["https://test.com"],
        }

        def consume_coro(coro):
            coro.close()
            return result_data

        mock_asyncio.run.side_effect = consume_coro
        mock_sys.stdout = MagicMock()

        with patch("scraper.cli.build_parser") as mock_parser_fn:
            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = MagicMock(
                topic="test",
                mode="default",
                urls=[],
                cache_dir="~/.cache/test",
                no_cache=False,
                timeout=15.0,
                verbose=False,
                output=None,
            )
            mock_parser_fn.return_value = mock_parser
            main()

        # json.dump was called with result to stdout
        mock_sys.stdout.write.assert_called()


class TestRunScraper:
    """Test the async run_scraper pipeline."""

    @pytest.mark.asyncio
    async def test_returns_correct_structure(self):
        """run_scraper should return dict with topic, mode, pages, stats, urls_fetched."""
        config = ScrapeConfig(mode="quick", cache_dir="/tmp/test-cli-scraper")
        config.max_retries = 1
        config.request_timeout = 2.0

        with patch("scraper.cli.Fetcher") as MockFetcher:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch_batch.return_value = []
            mock_fetcher.close = AsyncMock()
            MockFetcher.return_value = mock_fetcher

            result = await run_scraper("test-lib", config, initial_urls=[])

        assert result["topic"] == "test-lib"
        assert result["mode"] == "quick"
        assert isinstance(result["pages"], list)
        assert isinstance(result["stats"], dict)
        assert isinstance(result["urls_fetched"], list)
        assert "version" in result
        assert "changelog" in result

    @pytest.mark.asyncio
    async def test_empty_run_has_zero_stats(self):
        """With no URLs, stats should show zero pages."""
        config = ScrapeConfig(mode="quick", cache_dir="/tmp/test-cli-empty")
        config.max_retries = 1

        with patch("scraper.cli.Fetcher") as MockFetcher:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch_batch.return_value = []
            mock_fetcher.close = AsyncMock()
            MockFetcher.return_value = mock_fetcher

            result = await run_scraper("nothing", config, initial_urls=[])

        assert result["stats"]["pages_extracted"] == 0
        assert len(result["pages"]) == 0

    @pytest.mark.asyncio
    async def test_fetcher_close_called_on_success(self):
        """Fetcher.close() should be called even on normal completion."""
        config = ScrapeConfig(mode="quick", cache_dir="/tmp/test-cli-close")
        config.max_retries = 1

        with patch("scraper.cli.Fetcher") as MockFetcher:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch_batch.return_value = []
            mock_fetcher.close = AsyncMock()
            MockFetcher.return_value = mock_fetcher

            await run_scraper("test", config, initial_urls=[])

        mock_fetcher.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fetcher_close_called_on_error(self):
        """Fetcher.close() should be called even when pipeline errors."""
        config = ScrapeConfig(mode="quick", cache_dir="/tmp/test-cli-err")
        config.max_retries = 1

        with patch("scraper.cli.Fetcher") as MockFetcher:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch_batch.side_effect = RuntimeError("boom")
            mock_fetcher.close = AsyncMock()
            MockFetcher.return_value = mock_fetcher

            with pytest.raises(RuntimeError, match="boom"):
                await run_scraper("test", config, initial_urls=["https://example.com/docs/"])

        mock_fetcher.close.assert_awaited_once()
