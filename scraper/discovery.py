"""Sitemap parsing, robots.txt, and link discovery."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from .config import DOC_PATH_PATTERNS, SKIP_PATH_PATTERNS


def parse_sitemap_urls(xml_content: str) -> list[str]:
    """Extract URLs from a sitemap.xml file.

    Handles both <urlset> (page list) and <sitemapindex> (sitemap of sitemaps).
    """
    urls = []

    # Extract <loc> tags
    loc_pattern = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.IGNORECASE)
    for match in loc_pattern.finditer(xml_content):
        url = match.group(1).strip()
        if url:
            urls.append(url)

    return urls


def filter_doc_urls(urls: list[str]) -> list[str]:
    """Filter URLs to keep only documentation-relevant paths."""
    doc_urls = []
    for url in urls:
        path = urlparse(url).path.lower()

        # Skip non-doc paths (match with or without trailing slash)
        path_with_slash = path if path.endswith("/") else path + "/"
        if any(p in path_with_slash for p in SKIP_PATH_PATTERNS):
            continue

        # Keep if it matches doc patterns
        if any(p in path for p in DOC_PATH_PATTERNS):
            doc_urls.append(url)
            continue

        # Keep if it ends with common doc extensions
        if path.endswith((".md", ".html", ".htm", "/")):
            doc_urls.append(url)
            continue

    return doc_urls


def parse_robots_txt(content: str) -> tuple[list[str], list[str]]:
    """Parse robots.txt and return (sitemap_urls, disallowed_paths).

    Only looks at universal rules (User-agent: *) and Sitemap directives.
    """
    sitemaps = []
    disallowed = []
    in_universal = False

    for line in content.split("\n"):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Sitemap directives (global, not agent-specific)
        if line.lower().startswith("sitemap:"):
            sitemap_url = line.split(":", 1)[1].strip()
            if sitemap_url:
                sitemaps.append(sitemap_url)
            continue

        # User-agent detection
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            in_universal = agent == "*"
            continue

        # Disallow rules for universal agent
        if in_universal and line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path:
                disallowed.append(path)

    return sitemaps, disallowed


def is_disallowed(url: str, disallowed_paths: list[str]) -> bool:
    """Check if a URL's path is disallowed by robots.txt rules."""
    path = urlparse(url).path
    for rule in disallowed_paths:
        if rule.endswith("*"):
            if path.startswith(rule[:-1]):
                return True
        elif path.startswith(rule):
            return True
    return False


def extract_doc_links(html: str, base_url: str) -> list[str]:
    """Extract documentation-relevant links from an HTML page.

    Focuses on:
    - Sidebar/navigation links
    - Table of contents links
    - Internal doc links
    """
    base_domain = urlparse(base_url).netloc

    # Find all href attributes
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    all_links = href_pattern.findall(html)

    doc_links = []
    seen = set()

    for href in all_links:
        # Skip anchors, javascript, mailto
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)

        # Only same-domain links
        if urlparse(full_url).netloc != base_domain:
            continue

        # Normalize
        normalized = full_url.split("#")[0].rstrip("/")
        if normalized in seen:
            continue
        seen.add(normalized)

        path = urlparse(full_url).path.lower()

        # Skip non-doc paths (match with or without trailing slash)
        path_with_slash = path if path.endswith("/") else path + "/"
        if any(p in path_with_slash for p in SKIP_PATH_PATTERNS):
            continue

        # Skip file downloads
        if any(path.endswith(ext) for ext in [".zip", ".tar.gz", ".png", ".jpg", ".gif", ".svg", ".ico", ".pdf"]):
            continue

        # Prefer doc-like paths but include any same-domain HTML page
        is_doc = any(p in path for p in DOC_PATH_PATTERNS)
        is_html = path.endswith((".html", ".htm", "/")) or "." not in path.split("/")[-1]
        if is_doc or is_html:
            doc_links.append(full_url)

    return doc_links


def find_sitemap_urls(base_url: str) -> list[str]:
    """Generate candidate sitemap URLs to try for a given base URL."""
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    return [
        f"{origin}/sitemap.xml",
        f"{origin}/sitemap-0.xml",
        f"{origin}/sitemap_index.xml",
        f"{origin}/robots.txt",
    ]


def find_changelog_urls(base_url: str, topic: str) -> list[str]:
    """Generate candidate changelog/release URLs for a library.

    Checks common changelog locations: GitHub releases, CHANGELOG files,
    and common docs paths.
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    candidates = [
        f"{origin}/changelog",
        f"{origin}/CHANGELOG",
        f"{origin}/CHANGELOG.md",
        f"{origin}/releases",
        f"{origin}/docs/changelog",
        f"{origin}/docs/releases",
        f"{origin}/whats-new",
        f"{origin}/blog/releases",
    ]

    # GitHub-specific patterns
    if "github.com" in parsed.netloc:
        # e.g. https://github.com/honojs/hono -> /honojs/hono/releases
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            repo_path = "/".join(path_parts[:2])
            candidates.extend(
                [
                    f"{origin}/{repo_path}/releases",
                    f"{origin}/{repo_path}/blob/main/CHANGELOG.md",
                    f"{origin}/{repo_path}/blob/master/CHANGELOG.md",
                ]
            )

    return candidates


# Common version patterns found in documentation
_VERSION_PATTERNS = [
    # "v1.2.3" or "V1.2.3"
    re.compile(r"\bv(\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)\b", re.IGNORECASE),
    # "version 1.2.3" or "Version: 1.2.3"
    re.compile(r"\bversion[:\s]+(\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)\b", re.IGNORECASE),
    # "@scope/package@1.2.3" (npm)
    re.compile(r"@[\w-]+/[\w-]+@(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE),
    # "package@1.2.3" (npm)
    re.compile(r"[\w-]+@(\d+\.\d+(?:\.\d+)?)\b"),
]


def detect_version(text: str, topic: str = "") -> str | None:
    """Detect the library version from documentation text.

    Scans for version patterns and returns the most likely current version.
    Returns None if no version can be detected.
    """
    if not text:
        return None

    # Collect all version candidates with positions
    candidates: dict[str, int] = {}  # version -> earliest position

    for pattern in _VERSION_PATTERNS:
        for match in pattern.finditer(text):
            version = match.group(1)
            pos = match.start()
            # Keep earliest occurrence (more likely to be the current version)
            if version not in candidates or pos < candidates[version]:
                candidates[version] = pos

    if not candidates:
        return None

    # Sort by frequency (most common first), then by position (earliest first)
    version_counts: dict[str, int] = {}
    for pattern in _VERSION_PATTERNS:
        for match in pattern.finditer(text):
            v = match.group(1)
            version_counts[v] = version_counts.get(v, 0) + 1

    ranked = sorted(
        candidates.keys(),
        key=lambda v: (-version_counts.get(v, 0), candidates[v]),
    )

    return ranked[0] if ranked else None


def extract_changelog_entries(text: str, limit: int = 5) -> list[dict]:
    """Extract recent changelog entries from changelog/release notes text.

    Returns a list of dicts with 'version', 'date', and 'summary' keys.
    """
    entries: list[dict] = []

    # Pattern: "## v1.2.3" or "## 1.2.3 (2024-01-15)" or "# Version 1.2.3"
    heading_pattern = re.compile(
        r"^#{1,3}\s+(?:v(?:ersion)?\s*)?(\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)"
        r"(?:\s*[\(\[]\s*(\d{4}-\d{2}-\d{2})\s*[\)\]])?",
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(heading_pattern.finditer(text))

    for i, match in enumerate(matches[:limit]):
        version = match.group(1)
        date = match.group(2) or ""

        # Extract summary: text between this heading and the next
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else start + 500
        summary_text = text[start:end].strip()

        # Trim to first few lines
        summary_lines = summary_text.split("\n")[:5]
        summary = "\n".join(line.strip() for line in summary_lines if line.strip())

        entries.append(
            {
                "version": version,
                "date": date,
                "summary": summary[:300],
            }
        )

    return entries
