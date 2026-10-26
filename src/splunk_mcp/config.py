"""Configuration management for Splunk MCP Server using Pydantic Settings."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Splunk MCP Server Configuration loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Splunk Connectivity
    splunk_host: str = Field(
        default="192.168.0.107",
        validation_alias="SPLUNK_HOST",
        description="Splunk Enterprise hostname or IP address",
    )
    splunk_port: int = Field(
        default=8000,
        validation_alias="SPLUNK_PORT",
        description="Splunk port (8000 for Splunk Web, 8089 for direct REST)",
    )
    splunk_scheme: str = Field(
        default="http",
        validation_alias="SPLUNK_SCHEME",
        description="HTTP or HTTPS protocol scheme",
    )
    splunk_username: str | None = Field(
        default=None,
        validation_alias="SPLUNK_USERNAME",
        description="Splunk administrative or service account username",
    )
    splunk_password: SecretStr | None = Field(
        default=None,
        validation_alias="SPLUNK_PASSWORD",
        description="Splunk account password",
    )
    splunk_token: SecretStr | None = Field(
        default=None,
        validation_alias="SPLUNK_TOKEN",
        description="Splunk Bearer or static authentication token",
    )
    splunk_verify_tls: bool = Field(
        default=False,
        validation_alias="SPLUNK_VERIFY_TLS",
        description="Whether to verify SSL/TLS certificates",
    )
    splunk_ca_bundle: str | None = Field(
        default=None,
        validation_alias="SPLUNK_CA_BUNDLE",
        description="Path to custom CA certificate bundle for self-signed certificates",
    )
    splunk_timeout: float = Field(
        default=30.0,
        validation_alias="SPLUNK_TIMEOUT",
        description="HTTP request timeout in seconds",
    )
    splunk_max_results: int = Field(
        default=1000,
        validation_alias="SPLUNK_MAX_RESULTS",
        description="Maximum search result limit per query to protect Splunk performance",
    )
    splunk_max_concurrent_searches: int = Field(
        default=5,
        validation_alias="SPLUNK_MAX_CONCURRENT_SEARCHES",
        description="Maximum concurrent searches the MCP server will execute",
    )
    splunk_default_time_range: str = Field(
        default="-24h@h",
        validation_alias="SPLUNK_DEFAULT_TIME_RANGE",
        description="Default earliest time range if not specified by user",
    )

    # MCP Governance & Security Controls
    mcp_transport: str = Field(
        default="stdio",
        validation_alias="MCP_TRANSPORT",
        description="MCP transport layer: 'stdio', 'sse', or 'streamable-http'",
    )
    mcp_host: str = Field(
        default="0.0.0.0",
        validation_alias="MCP_HOST",
        description="Host to bind for HTTP/SSE transport",
    )
    mcp_port: int = Field(
        default=8001,
        validation_alias="MCP_PORT",
        description="Port to bind for HTTP/SSE transport",
    )
    mcp_auth_mode: str = Field(
        default="none",
        validation_alias="MCP_AUTH_MODE",
        description="MCP authentication mode for remote access: 'none' or 'token'",
    )
    mcp_audit_enabled: bool = Field(
        default=True,
        validation_alias="MCP_AUDIT_ENABLED",
        description="Enable structured audit logging for all tool invocations",
    )
    mcp_log_level: str = Field(
        default="INFO",
        validation_alias="MCP_LOG_LEVEL",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )
    mcp_read_only: bool = Field(
        default=True,
        validation_alias="MCP_READ_ONLY",
        description="Enforce read-only mode by default to prevent unauthorized modifications",
    )

    @property
    def base_url(self) -> str:
        """Construct base URL for Splunk connection."""
        return f"{self.splunk_scheme}://{self.splunk_host}:{self.splunk_port}".rstrip("/")

    @property
    def is_splunk_web_port(self) -> bool:
        """Determine if connection targets Splunk Web interface rather than direct 8089."""
        return self.splunk_port == 8000


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Get or create singleton configuration instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def set_settings(settings: Settings) -> None:
    """Override singleton configuration instance (useful for testing)."""
    global _settings_instance
    _settings_instance = settings
