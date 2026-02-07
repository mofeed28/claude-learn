"""Tests for URL queue with scoring and deduplication."""

import pytest
from scraper.queue import URLQueue, normalize_url, score_url, should_skip_url


class TestNormalizeURL:
    def test_strips_trailing_slash(self):
        assert normalize_url("https://docs.stripe.com/api/") == "https://docs.stripe.com/api"

    def test_keeps_root_slash(self):
        result = normalize_url("https://docs.stripe.com/")
        assert result == "https://docs.stripe.com/"

    def test_lowercases_domain(self):
        assert normalize_url("https://Docs.Stripe.COM/api") == "https://docs.stripe.com/api"

    def test_strips_fragments(self):
        assert normalize_url("https://docs.stripe.com/api#section") == "https://docs.stripe.com/api"

    def test_strips_tracking_params(self):
        url = "https://docs.stripe.com/api?utm_source=google&utm_medium=cpc&page=1"
        result = normalize_url(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "page=1" in result

    def test_preserves_meaningful_params(self):
        url = "https://docs.stripe.com/api?version=2024&lang=python"
        result = normalize_url(url)
        assert "version" in result
        assert "lang" in result


class TestScoreURL:
    def test_api_reference_scores_5(self):
        assert score_url("https://docs.stripe.com/api/charges") == 5

    def test_guide_scores_4(self):
        assert score_url("https://docs.stripe.com/docs/getting-started") == 4

    def test_github_raw_scores_4(self):
        assert score_url("https://raw.githubusercontent.com/stripe/stripe-node/main/README.md") == 4

    def test_npm_scores_3(self):
        assert score_url("https://www.npmjs.com/package/stripe") == 3

    def test_stackoverflow_scores_2(self):
        assert score_url("https://stackoverflow.com/questions/12345") == 2

    def test_wayback_scores_1(self):
        assert score_url("https://web.archive.org/web/2024/https://docs.stripe.com") == 1

    def test_blog_scores_2(self):
        assert score_url("https://dev.to/stripe/getting-started") == 2


class TestShouldSkipURL:
    def test_skips_blog_paths(self):
        assert should_skip_url("https://stripe.com/blog/new-feature") is True

    def test_skips_pricing(self):
        assert should_skip_url("https://stripe.com/pricing") is True

    def test_skips_images(self):
        assert should_skip_url("https://stripe.com/logo.png") is True

    def test_keeps_doc_paths(self):
        assert should_skip_url("https://docs.stripe.com/api/charges") is False

    def test_keeps_normal_pages(self):
        assert should_skip_url("https://docs.stripe.com/getting-started") is False

    def test_skips_non_http(self):
        assert should_skip_url("ftp://example.com/file") is True


class TestURLQueue:
    def test_add_and_get_batch(self):
        q = URLQueue(max_size=10)
        q.add("https://docs.stripe.com/api", score=5, source="search")
        q.add("https://dev.to/stripe-guide", score=2, source="search")
        q.add("https://docs.stripe.com/docs/guide", score=4, source="search")

        batch = q.get_batch(size=2)
        assert len(batch) == 2
        assert batch[0].score >= batch[1].score  # sorted by score

    def test_dedup_same_url(self):
        q = URLQueue()
        assert q.add("https://docs.stripe.com/api") is True
        assert q.add("https://docs.stripe.com/api") is False

    def test_dedup_normalized(self):
        q = URLQueue()
        q.add("https://docs.stripe.com/api/")
        assert q.add("https://docs.stripe.com/api") is False

    def test_dedup_keeps_higher_score(self):
        q = URLQueue()
        q.add("https://docs.stripe.com/api", score=2)
        q.add("https://docs.stripe.com/api", score=5)

        batch = q.get_batch(1)
        assert batch[0].score == 5

    def test_mark_fetched(self):
        q = URLQueue()
        q.add("https://docs.stripe.com/api", score=5)
        q.mark_fetched("https://docs.stripe.com/api")

        batch = q.get_batch(1)
        assert len(batch) == 0
        assert q.fetched_count == 1

    def test_skip_urls_not_added(self):
        q = URLQueue()
        assert q.add("https://stripe.com/blog/post") is False
        assert q.add("https://stripe.com/logo.png") is False

    def test_pending_count(self):
        q = URLQueue()
        q.add("https://a.com/docs", score=5)
        q.add("https://b.com/docs", score=4)
        assert q.pending_count == 2

        q.mark_fetched("https://a.com/docs")
        assert q.pending_count == 1

    def test_add_many(self):
        q = URLQueue()
        count = q.add_many([
            "https://a.com/docs",
            "https://b.com/docs",
            "https://a.com/docs",  # dup
            "https://c.com/blog/post",  # skip
        ], score=4)
        assert count == 2
