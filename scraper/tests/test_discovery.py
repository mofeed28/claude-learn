"""Tests for sitemap parsing and link discovery."""

import pytest
from scraper.discovery import (
    parse_sitemap_urls, filter_doc_urls, parse_robots_txt,
    is_disallowed, extract_doc_links, find_sitemap_urls,
    find_changelog_urls, detect_version, extract_changelog_entries,
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


class TestDiscoveryEdgeCases:
    """Edge cases for discovery functions."""

    def test_sitemap_with_whitespace_in_loc(self):
        xml = """<urlset>
            <url><loc>
                https://example.com/docs/api
            </loc></url>
        </urlset>"""
        urls = parse_sitemap_urls(xml)
        assert len(urls) == 1
        assert urls[0] == "https://example.com/docs/api"

    def test_sitemap_case_insensitive_tags(self):
        xml = """<urlset>
            <URL><LOC>https://example.com/docs/api</LOC></URL>
        </urlset>"""
        urls = parse_sitemap_urls(xml)
        assert len(urls) == 1

    def test_robots_comments_ignored(self):
        content = """
# This is a comment
User-agent: *
Disallow: /admin/
# Another comment
Sitemap: https://example.com/sitemap.xml
"""
        sitemaps, disallowed = parse_robots_txt(content)
        assert len(sitemaps) == 1
        assert len(disallowed) == 1

    def test_robots_non_universal_agent_ignored(self):
        content = """
User-agent: Googlebot
Disallow: /google-only/

User-agent: *
Disallow: /private/
"""
        sitemaps, disallowed = parse_robots_txt(content)
        # Should only include /private/ (from User-agent: *)
        assert "/private/" in disallowed
        assert "/google-only/" not in disallowed

    def test_is_disallowed_exact_prefix(self):
        assert is_disallowed("https://example.com/api/v1", ["/api/"]) is True
        assert is_disallowed("https://example.com/api2/v1", ["/api/"]) is False

    def test_is_disallowed_empty_rules(self):
        assert is_disallowed("https://example.com/anything", []) is False

    def test_filter_doc_urls_mixed(self):
        urls = [
            "https://example.com/docs/intro",
            "https://example.com/blog/news",
            "https://example.com/pricing",
            "https://example.com/api/users",
            "https://example.com/page.html",
            "https://example.com/random-file.zip",
        ]
        result = filter_doc_urls(urls)
        assert "https://example.com/docs/intro" in result
        assert "https://example.com/api/users" in result
        assert "https://example.com/page.html" in result
        assert "https://example.com/blog/news" not in result
        assert "https://example.com/pricing" not in result

    def test_extract_doc_links_deduplicates(self):
        html = """
        <a href="/docs/api">Link 1</a>
        <a href="/docs/api">Link 2</a>
        <a href="/docs/api#section">Link 3</a>
        """
        links = extract_doc_links(html, "https://example.com")
        api_links = [l for l in links if "api" in l]
        assert len(api_links) == 1  # deduped

    def test_extract_doc_links_skips_downloads(self):
        html = """
        <a href="/files/doc.zip">Download</a>
        <a href="/images/logo.png">Logo</a>
        <a href="/docs/guide">Guide</a>
        """
        links = extract_doc_links(html, "https://example.com")
        assert not any(".zip" in l for l in links)
        assert not any(".png" in l for l in links)
        assert any("guide" in l for l in links)

    def test_find_sitemap_uses_origin_only(self):
        """Sitemap URLs should be at the origin, ignoring path."""
        candidates = find_sitemap_urls("https://docs.stripe.com/api/v2/charges")
        for url in candidates:
            assert url.startswith("https://docs.stripe.com/")
            # Should not include /api/v2/charges
            assert "/api/" not in url


class TestFindChangelogURLs:
    def test_generates_candidates(self):
        candidates = find_changelog_urls("https://docs.stripe.com/api", "stripe")
        assert any("changelog" in url.lower() for url in candidates)
        assert any("releases" in url for url in candidates)

    def test_github_urls_include_repo_releases(self):
        candidates = find_changelog_urls("https://github.com/honojs/hono", "hono")
        assert "https://github.com/honojs/hono/releases" in candidates
        assert any("CHANGELOG.md" in url for url in candidates)

    def test_non_github_has_no_repo_paths(self):
        candidates = find_changelog_urls("https://docs.stripe.com", "stripe")
        assert not any("blob/main" in url for url in candidates)


class TestDetectVersion:
    def test_detects_v_prefix(self):
        text = "This documentation covers v4.3.2 of the library."
        assert detect_version(text) == "4.3.2"

    def test_detects_version_keyword(self):
        text = "Current version: 2.1.0. See release notes for details."
        assert detect_version(text) == "2.1.0"

    def test_detects_npm_at_version(self):
        text = "Install with npm install stripe@14.2.0"
        assert detect_version(text) == "14.2.0"

    def test_detects_scoped_npm(self):
        text = "Install @hono/node-server@1.5.0 for Node.js support"
        assert detect_version(text) == "1.5.0"

    def test_returns_none_for_no_version(self):
        text = "Welcome to the documentation. Here is how to get started."
        assert detect_version(text) is None

    def test_returns_none_for_empty(self):
        assert detect_version("") is None
        assert detect_version(None) is None

    def test_picks_most_common_version(self):
        text = "v4.3.2 is the latest. Install v4.3.2. Upgrade to v4.3.2 from v3.0.0."
        result = detect_version(text)
        assert result == "4.3.2"

    def test_handles_prerelease_versions(self):
        text = "Now available: v5.0.0-beta.1"
        result = detect_version(text)
        assert result == "5.0.0-beta.1"

    def test_two_digit_version(self):
        text = "API version 2.0 is now stable."
        assert detect_version(text) == "2.0"


class TestExtractChangelogEntries:
    def test_extracts_markdown_changelog(self):
        text = """# Changelog

## 4.3.2 (2024-12-15)
- Fixed authentication bug
- Updated dependencies

## 4.3.1 (2024-11-20)
- Minor patch release
- Fixed typo in docs

## 4.3.0 (2024-10-01)
- New middleware system
- Breaking: removed legacy API
"""
        entries = extract_changelog_entries(text)
        assert len(entries) == 3
        assert entries[0]["version"] == "4.3.2"
        assert entries[0]["date"] == "2024-12-15"
        assert "authentication" in entries[0]["summary"]
        assert entries[1]["version"] == "4.3.1"

    def test_extracts_v_prefix_headings(self):
        text = """## v2.0.0 (2024-06-01)
Major rewrite with new API.

## v1.9.0
Minor improvements.
"""
        entries = extract_changelog_entries(text)
        assert len(entries) == 2
        assert entries[0]["version"] == "2.0.0"
        assert entries[0]["date"] == "2024-06-01"
        assert entries[1]["version"] == "1.9.0"
        assert entries[1]["date"] == ""

    def test_limits_entries(self):
        text = "\n".join(f"## {i}.0.0\nRelease {i}" for i in range(20, 0, -1))
        entries = extract_changelog_entries(text, limit=3)
        assert len(entries) == 3

    def test_empty_text(self):
        assert extract_changelog_entries("") == []

    def test_no_matching_headings(self):
        text = "# Introduction\nThis is not a changelog."
        assert extract_changelog_entries(text) == []
