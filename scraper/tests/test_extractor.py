"""Tests for HTML content extraction."""

import pytest
from scraper.extractor import extract_content, content_similarity


class TestExtractContent:
    def test_extracts_text(self):
        html = "<html><body><p>Hello world</p></body></html>"
        result = extract_content(html)
        assert "Hello world" in result.text

    def test_strips_nav(self):
        html = """
        <html><body>
            <nav><a href="/home">Home</a><a href="/about">About</a></nav>
            <main><p>Real documentation content here</p></main>
        </body></html>
        """
        result = extract_content(html)
        assert "Real documentation content" in result.text
        # Nav content might still appear but should be less prominent

    def test_strips_script_and_style(self):
        html = """
        <html>
        <style>.foo { color: red; }</style>
        <script>console.log('hidden')</script>
        <body><p>Visible text</p></body>
        </html>
        """
        result = extract_content(html)
        assert "console.log" not in result.text
        assert "color: red" not in result.text
        assert "Visible text" in result.text

    def test_extracts_code_blocks(self):
        html = """
        <html><body>
            <pre><code>const x = 42;\nconsole.log(x);</code></pre>
            <p>Some text</p>
        </body></html>
        """
        result = extract_content(html)
        assert len(result.code_blocks) >= 1
        assert "const x = 42" in result.code_blocks[0]

    def test_extracts_headings(self):
        html = """
        <html><body>
            <h1>Main Title</h1>
            <h2>Section One</h2>
            <p>Content</p>
            <h2>Section Two</h2>
        </body></html>
        """
        result = extract_content(html)
        assert "Main Title" in result.headings
        assert "Section One" in result.headings
        assert "Section Two" in result.headings

    def test_extracts_links(self):
        html = """
        <html><body>
            <a href="/docs/api">API Docs</a>
            <a href="https://example.com/guide">Guide</a>
            <a href="#section">Anchor</a>
        </body></html>
        """
        result = extract_content(html, base_url="https://docs.stripe.com")
        assert "https://docs.stripe.com/docs/api" in result.links
        assert "https://example.com/guide" in result.links
        # Anchors should be filtered
        assert "#section" not in result.links

    def test_word_count(self):
        html = "<p>one two three four five</p>"
        result = extract_content(html)
        assert result.word_count == 5

    def test_handles_malformed_html(self):
        html = "<p>Unclosed tag <b>bold text <p>Another"
        result = extract_content(html)
        assert "Unclosed tag" in result.text

    def test_extracts_tables(self):
        html = """
        <table>
            <tr><th>Name</th><th>Type</th></tr>
            <tr><td>id</td><td>string</td></tr>
            <tr><td>amount</td><td>number</td></tr>
        </table>
        """
        result = extract_content(html)
        assert len(result.tables) >= 1
        assert "Name" in result.tables[0]
        assert "id" in result.tables[0]


class TestContentSimilarity:
    def test_identical_texts(self):
        assert content_similarity("hello world foo bar", "hello world foo bar") == 1.0

    def test_completely_different(self):
        sim = content_similarity("hello world", "foo bar baz qux")
        assert sim < 0.1

    def test_partial_overlap(self):
        sim = content_similarity(
            "stripe payment api integration guide",
            "stripe payment api reference documentation",
        )
        assert 0.3 < sim < 0.8

    def test_empty_strings(self):
        assert content_similarity("", "hello") == 0.0
        assert content_similarity("hello", "") == 0.0
        assert content_similarity("", "") == 0.0

    def test_high_similarity(self):
        text1 = "the quick brown fox jumps over the lazy dog"
        text2 = "the quick brown fox leaps over the lazy dog"
        sim = content_similarity(text1, text2)
        assert sim > 0.7
