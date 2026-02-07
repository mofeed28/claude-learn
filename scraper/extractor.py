"""Content extraction from HTML — strips boilerplate, extracts documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class ExtractedContent:
    """Extracted content from a page."""
    title: str = ""
    text: str = ""
    code_blocks: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    word_count: int = 0


class _TagStripper(HTMLParser):
    """Simple HTML to text converter that preserves structure."""

    # Tags that typically contain navigation/boilerplate
    SKIP_TAGS = {
        "nav", "header", "footer", "aside", "script", "style",
        "noscript", "svg", "iframe", "form",
    }
    # Tags whose classes suggest navigation
    SKIP_CLASSES = {
        "nav", "navbar", "sidebar", "footer", "header",
        "menu", "breadcrumb", "pagination", "cookie",
        "banner", "ad", "advertisement",
    }
    BLOCK_TAGS = {
        "p", "div", "section", "article", "main", "h1", "h2", "h3",
        "h4", "h5", "h6", "li", "tr", "blockquote", "pre", "br", "hr",
    }

    def __init__(self):
        super().__init__()
        self.output: list[str] = []
        self.headings: list[str] = []
        self.code_blocks: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0
        self._skip_stack: list[str] = []  # tracks which tags triggered skipping
        self._in_code = False
        self._code_buffer: list[str] = []
        self._current_tag = ""
        self._heading_buffer: list[str] = []
        self._in_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_dict = dict(attrs)
        classes = (attr_dict.get("class") or "").lower().split()

        # Skip navigation/boilerplate elements (by tag name or CSS class)
        if tag in self.SKIP_TAGS or any(c in self.SKIP_CLASSES for c in classes):
            self._skip_depth += 1
            self._skip_stack.append(tag)
            return

        if self._skip_depth > 0:
            return

        self._current_tag = tag

        # Track code blocks
        if tag in ("pre", "code"):
            self._in_code = True
            self._code_buffer = []

        # Track headings
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = True
            self._heading_buffer = []

        # Extract links
        if tag == "a":
            href = attr_dict.get("href", "")
            if href and not href.startswith(("#", "javascript:", "mailto:")):
                self.links.append(href)

        # Add line breaks for block elements
        if tag in self.BLOCK_TAGS:
            self.output.append("\n")

    def handle_endtag(self, tag: str):
        # Check if this closing tag matches a skip-triggering open tag
        if self._skip_stack and tag == self._skip_stack[-1]:
            self._skip_stack.pop()
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if self._skip_depth > 0:
            return

        if tag in ("pre", "code") and self._in_code:
            self._in_code = False
            code = "".join(self._code_buffer).strip()
            if code and len(code) > 20:  # skip tiny inline code
                self.code_blocks.append(code)

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._in_heading:
            self._in_heading = False
            heading = "".join(self._heading_buffer).strip()
            if heading:
                self.headings.append(heading)

        if tag in self.BLOCK_TAGS:
            self.output.append("\n")

    def handle_data(self, data: str):
        if self._skip_depth > 0:
            return

        if self._in_code:
            self._code_buffer.append(data)

        if self._in_heading:
            self._heading_buffer.append(data)

        self.output.append(data)

    def get_text(self) -> str:
        text = "".join(self.output)
        # Collapse multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()


def extract_content(html: str, base_url: str = "") -> ExtractedContent:
    """Extract structured content from HTML.

    Strips navigation, headers, footers, ads, and other boilerplate.
    Preserves code blocks, headings, tables, and documentation text.
    """
    stripper = _TagStripper()
    try:
        stripper.feed(html)
    except Exception:
        # If HTML parsing fails, fall back to regex stripping
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return ExtractedContent(text=text, word_count=len(text.split()))

    text = stripper.get_text()

    # Resolve relative links
    if base_url:
        from urllib.parse import urljoin
        links = [urljoin(base_url, link) for link in stripper.links]
    else:
        links = stripper.links

    # Extract tables from HTML (simple regex approach)
    tables = _extract_tables(html)

    return ExtractedContent(
        title=stripper.headings[0] if stripper.headings else "",
        text=text,
        code_blocks=stripper.code_blocks,
        headings=stripper.headings,
        links=links,
        tables=tables,
        word_count=len(text.split()),
    )


def _extract_tables(html: str) -> list[str]:
    """Extract markdown-like representations of HTML tables."""
    tables = []
    table_pattern = re.compile(r"<table[^>]*>(.*?)</table>", re.DOTALL | re.IGNORECASE)
    row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)

    for table_match in table_pattern.finditer(html):
        rows = []
        for row_match in row_pattern.finditer(table_match.group(1)):
            cells = []
            for cell_match in cell_pattern.finditer(row_match.group(1)):
                cell_text = re.sub(r"<[^>]+>", "", cell_match.group(1)).strip()
                cells.append(cell_text)
            if cells:
                rows.append(cells)

        if rows:
            # Convert to markdown table
            md_rows = []
            for i, row in enumerate(rows):
                md_rows.append("| " + " | ".join(row) + " |")
                if i == 0:
                    md_rows.append("| " + " | ".join("---" for _ in row) + " |")
            tables.append("\n".join(md_rows))

    return tables


def content_similarity(text1: str, text2: str) -> float:
    """Estimate similarity between two texts (0.0 to 1.0).

    Uses word-level Jaccard similarity for speed.
    """
    if not text1 or not text2:
        return 0.0

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0
