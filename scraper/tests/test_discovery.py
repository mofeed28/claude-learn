"""Tests for sitemap parsing and link discovery."""

import pytest
from scraper.discovery import (
    parse_sitemap_urls, filter_doc_urls, parse_robots_txt,
    is_disallowed, extract_doc_links, find_sitemap_urls,
)


class TestParseSitemapURLs:
    def test_extracts_loc_tags(self):
        xml = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://docs.example.com/api/charges</loc></url>
            <url><loc>https://docs.example.com/api/customers</loc></url>
            <url><loc>https://docs.example.com/guide/getting-started</loc></url>
        </urlset>"""
        urls = parse_sitemap_urls(xml)
        assert len(urls) == 3
        assert "https://docs.example.com/api/charges" in urls
        assert "https://docs.example.com/api/customers" in urls

    def test_handles_sitemap_index(self):
        xml = """<?xml version="1.0"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap><loc>https://docs.example.com/sitemap-docs.xml</loc></sitemap>
            <sitemap><loc>https://docs.example.com/sitemap-api.xml</loc></sitemap>
        </sitemapindex>"""
        urls = parse_sitemap_urls(xml)
        assert len(urls) == 2

    def test_handles_empty(self):
        assert parse_sitemap_urls("") == []
        assert parse_sitemap_urls("<urlset></urlset>") == []


class TestFilterDocURLs:
    def test_keeps_doc_urls(self):
        urls = [
            "https://example.com/docs/api",
            "https://example.com/guide/quickstart",
            "https://example.com/reference/types",
        ]
        result = filter_doc_urls(urls)
        assert len(result) == 3

    def test_filters_non_doc_urls(self):
        urls = [
            "https://example.com/blog/announcement",
            "https://example.com/pricing",
            "https://example.com/careers",
        ]
        result = filter_doc_urls(urls)
        assert len(result) == 0

    def test_keeps_html_pages(self):
        urls = ["https://example.com/page.html", "https://example.com/section/"]
        result = filter_doc_urls(urls)
        assert len(result) == 2


class TestParseRobotsTxt:
    def test_extracts_sitemaps(self):
        content = """
User-agent: *
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-docs.xml
"""
        sitemaps, disallowed = parse_robots_txt(content)
        assert len(sitemaps) == 2
        assert "https://example.com/sitemap.xml" in sitemaps
        assert "/admin/" in disallowed

    def test_handles_empty(self):
        sitemaps, disallowed = parse_robots_txt("")
        assert sitemaps == []
        assert disallowed == []


class TestIsDisallowed:
    def test_disallowed_path(self):
        assert is_disallowed("https://example.com/admin/panel", ["/admin/"]) is True

    def test_allowed_path(self):
        assert is_disallowed("https://example.com/docs/api", ["/admin/"]) is False

    def test_wildcard_rule(self):
        assert is_disallowed("https://example.com/private/data", ["/private*"]) is True


class TestExtractDocLinks:
    def test_extracts_same_domain_links(self):
        html = """
        <a href="/docs/api">API</a>
        <a href="/docs/guide">Guide</a>
        <a href="https://other.com/docs">External</a>
        """
        links = extract_doc_links(html, "https://docs.example.com")
        assert any("/docs/api" in l for l in links)
        assert any("/docs/guide" in l for l in links)
        assert not any("other.com" in l for l in links)

    def test_skips_anchors_and_javascript(self):
        html = """
        <a href="#section">Anchor</a>
        <a href="javascript:void(0)">JS</a>
        <a href="mailto:test@test.com">Email</a>
        <a href="/docs/real">Real</a>
        """
        links = extract_doc_links(html, "https://example.com")
        assert len(links) == 1
        assert any("real" in l for l in links)

    def test_skips_non_doc_paths(self):
        html = """
        <a href="/blog/post">Blog</a>
        <a href="/pricing">Pricing</a>
        <a href="/docs/api">API</a>
        """
        links = extract_doc_links(html, "https://example.com")
        assert len(links) == 1


class TestFindSitemapURLs:
    def test_generates_candidates(self):
        candidates = find_sitemap_urls("https://docs.stripe.com/api")
        assert "https://docs.stripe.com/sitemap.xml" in candidates
        assert "https://docs.stripe.com/robots.txt" in candidates
        assert len(candidates) == 4
