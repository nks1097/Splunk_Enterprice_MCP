"""Unit tests for configuration management."""

from splunk_mcp.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.splunk_host is not None
    assert settings.splunk_port in (8000, 8089)
    assert settings.mcp_read_only is True
    assert settings.splunk_max_results == 1000


def test_base_url_generation():
    settings = Settings(
        splunk_host="splunk.example.com",
        splunk_port=8089,
        splunk_scheme="https",
    )
    assert settings.base_url == "https://splunk.example.com:8089"
    assert settings.is_splunk_web_port is False


def test_splunk_web_detection():
    settings = Settings(
        splunk_host="192.168.0.107",
        splunk_port=8000,
        splunk_scheme="http",
    )
    assert settings.is_splunk_web_port is True
