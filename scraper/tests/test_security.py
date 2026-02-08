"""Tests for security features: SSRF protection and path traversal prevention."""

import pytest

from scraper.cli import _validate_output_path, _validate_urls
from scraper.fetcher import _is_private_url


class TestSSRFProtection:
    """Test _is_private_url blocks internal/private addresses."""

    @pytest.mark.security
    def test_blocks_localhost(self):
        assert _is_private_url("http://localhost/secret") is True

    @pytest.mark.security
    def test_blocks_localhost_with_port(self):
        assert _is_private_url("http://localhost:8080/admin") is True

    @pytest.mark.security
    def test_blocks_127_0_0_1(self):
        assert _is_private_url("http://127.0.0.1/") is True

    @pytest.mark.security
    def test_blocks_ipv6_loopback(self):
        assert _is_private_url("http://[::1]/") is True

    @pytest.mark.security
    def test_blocks_10_x_private(self):
        assert _is_private_url("http://10.0.0.1/internal") is True

    @pytest.mark.security
    def test_blocks_172_16_private(self):
        assert _is_private_url("http://172.16.0.1/") is True

    @pytest.mark.security
    def test_blocks_192_168_private(self):
        assert _is_private_url("http://192.168.1.1/") is True

    @pytest.mark.security
    def test_blocks_metadata_endpoint(self):
        assert _is_private_url("http://169.254.169.254/latest/meta-data/") is True

    @pytest.mark.security
    def test_blocks_cloud_metadata_hostname(self):
        assert _is_private_url("http://metadata.google.internal/") is True

    @pytest.mark.security
    def test_blocks_empty_hostname(self):
        assert _is_private_url("http:///secret") is True

    @pytest.mark.security
    def test_allows_public_url(self):
        assert _is_private_url("https://docs.stripe.com/api") is False

    @pytest.mark.security
    def test_allows_public_ip(self):
        assert _is_private_url("http://8.8.8.8/") is False


class TestPathTraversalProtection:
    """Test _validate_output_path rejects dangerous paths."""

    @pytest.mark.security
    def test_accepts_relative_path_in_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _validate_output_path("output.json")
        assert result.name == "output.json"

    @pytest.mark.security
    def test_accepts_subdirectory_in_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        subdir = tmp_path / "results"
        subdir.mkdir()
        result = _validate_output_path("results/output.json")
        assert "results" in str(result)

    @pytest.mark.security
    def test_rejects_path_outside_cwd_and_home(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="resolves outside"):
            _validate_output_path("/etc/passwd")


class TestURLValidation:
    """Test _validate_urls rejects non-HTTP schemes."""

    @pytest.mark.security
    def test_accepts_https(self):
        _validate_urls(["https://example.com"])  # should not raise

    @pytest.mark.security
    def test_accepts_http(self):
        _validate_urls(["http://example.com"])  # should not raise

    @pytest.mark.security
    def test_rejects_ftp(self):
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            _validate_urls(["ftp://evil.com/file"])

    @pytest.mark.security
    def test_rejects_file_scheme(self):
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            _validate_urls(["file:///etc/passwd"])

    @pytest.mark.security
    def test_rejects_javascript_scheme(self):
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            _validate_urls(["javascript:alert(1)"])

    @pytest.mark.security
    def test_empty_list_passes(self):
        _validate_urls([])  # should not raise
