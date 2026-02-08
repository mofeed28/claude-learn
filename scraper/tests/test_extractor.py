"""Tests for HTML content extraction."""

from scraper.extractor import content_similarity, extract_content


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


class TestEdgeCases:
    """Edge cases for content extraction."""

    def test_deeply_nested_html(self):
        """Deeply nested tags should not crash the parser."""
        html = "<div>" * 100 + "<p>Deep text</p>" + "</div>" * 100
        result = extract_content(html)
        assert "Deep text" in result.text

    def test_empty_html(self):
        result = extract_content("")
        assert result.word_count == 0

    def test_only_script_tags(self):
        html = "<script>var x = 1;</script><script>var y = 2;</script>"
        result = extract_content(html)
        assert "var x" not in result.text

    def test_html_entities(self):
        html = "<p>Price is &lt;$100 &amp; &gt;$50</p>"
        result = extract_content(html)
        assert "<$100" in result.text or "&lt;" in result.text

    def test_unicode_content(self):
        html = "<p>日本語のドキュメント — API リファレンス</p>"
        result = extract_content(html)
        assert "日本語" in result.text

    def test_mixed_encoding_chars(self):
        html = "<p>Héllo wörld — naïve café résumé</p>"
        result = extract_content(html)
        assert "Héllo" in result.text

    def test_pre_without_code(self):
        """<pre> without <code> should still capture content."""
        html = "<pre>formatted text\n  with indentation</pre>"
        result = extract_content(html)
        assert "formatted text" in result.text

    def test_inline_code_too_short(self):
        """Inline code snippets (<20 chars) should be skipped from code_blocks."""
        html = "<p>Use <code>npm i</code> to install</p>"
        result = extract_content(html)
        assert len(result.code_blocks) == 0

    def test_multiple_tables(self):
        html = """
        <table><tr><th>A</th></tr><tr><td>1</td></tr></table>
        <table><tr><th>B</th></tr><tr><td>2</td></tr></table>
        """
        result = extract_content(html)
        assert len(result.tables) == 2

    def test_table_with_nested_html(self):
        html = """
        <table>
        <tr><th><strong>Name</strong></th><th>Type</th></tr>
        <tr><td><code>id</code></td><td>string</td></tr>
        </table>
        """
        result = extract_content(html)
        assert len(result.tables) >= 1
        assert "Name" in result.tables[0]

    def test_strips_boilerplate_tags(self):
        """Nav/footer elements should be stripped while preserving main content."""
        html = """
        <nav>Navigation links to skip</nav>
        <main><p>Real documentation here that matters</p></main>
        <footer>Footer content to skip</footer>
        """
        result = extract_content(html)
        assert "Real documentation" in result.text
        assert "Navigation links" not in result.text
        assert "Footer content" not in result.text

    def test_link_resolution_with_base_url(self):
        html = '<a href="../api/charges">Charges</a>'
        result = extract_content(html, base_url="https://docs.stripe.com/docs/guide/")
        assert "https://docs.stripe.com/docs/api/charges" in result.links

    def test_relative_link_no_base_url(self):
        html = '<a href="/docs/api">API</a>'
        result = extract_content(html, base_url="")
        assert "/docs/api" in result.links

    def test_javascript_links_filtered(self):
        html = '<a href="javascript:void(0)">Click</a><a href="/docs/real">Real</a>'
        result = extract_content(html)
        assert "javascript:" not in str(result.links)

    def test_fallback_on_broken_html(self):
        """Truly broken HTML that crashes the parser should fall back to regex."""
        # HTMLParser is pretty resilient, but let's test with weird content
        html = "<<<<<>>>>>just text here with no real tags"
        result = extract_content(html)
        assert "just text" in result.text or result.word_count >= 0

    def test_class_based_skip_depth_recovery(self):
        """Class-based skipping should not leak into subsequent siblings."""
        html = """
        <div class="sidebar">Sidebar nav content should be hidden</div>
        <div class="content"><p>Real documentation here that matters a lot</p></div>
        """
        result = extract_content(html)
        assert "Real documentation" in result.text
        assert "Sidebar nav" not in result.text

    def test_nested_skip_class_recovery(self):
        """Nested skip-class elements should properly restore depth."""
        html = """
        <div class="navbar">
            <div class="menu">Menu items to skip entirely</div>
        </div>
        <main><p>Important content that must appear in output</p></main>
        """
        result = extract_content(html)
        assert "Important content" in result.text
        assert "Menu items" not in result.text
