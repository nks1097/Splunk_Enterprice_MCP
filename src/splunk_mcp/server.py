"""Model Context Protocol (MCP) Server for Splunk Enterprise.

Provides 100 typed, audited, and secure tools spanning 10 operational domains.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from mcp.server.mcpserver import MCPServer

from splunk_mcp import __version__
from splunk_mcp.config import Settings, get_settings, set_settings
from splunk_mcp.tools import ALL_TOOLS

logger = logging.getLogger("splunk_mcp.server")


def create_server(settings: Settings | None = None) -> MCPServer:
    """Create and configure the Splunk Enterprise MCP server with all 100 tools."""
    settings or get_settings()
    server = MCPServer(
        name="splunk-enterprise-mcp",
        version=__version__,
        instructions=(
            "Enterprise MCP Server for Splunk Enterprise. "
            "Enables AI agents to query SPL, investigate security alerts, discover data catalogs, "
            "audit ingestion health, and manage knowledge objects under strict governance and audit."
        ),
    )

    # Register all 100 tools
    for tool_fn in ALL_TOOLS:
        server.add_tool(tool_fn)

    return server


async def async_main() -> None:
    """Asynchronous entry point for Splunk MCP Server."""
    parser = argparse.ArgumentParser(description="Splunk Enterprise Model Context Protocol (MCP) Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
        help="MCP transport protocol (default from MCP_TRANSPORT or 'stdio')",
    )
    parser.add_argument("--host", default=None, help="Host to bind for HTTP/SSE transport")
    parser.add_argument("--port", type=int, default=None, help="Port to bind for HTTP/SSE transport")
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=None,
        help="Enforce read-only mode (overrides MCP_READ_ONLY)",
    )
    parser.add_argument(
        "--read-write",
        action="store_true",
        help="Enable read-write mode (disables read-only restriction)",
    )
    args = parser.parse_args()

    settings = get_settings()

    if args.read_write:
        settings.mcp_read_only = False
    elif args.read_only is not None:
        settings.mcp_read_only = args.read_only

    transport = args.transport or settings.mcp_transport
    host = args.host or settings.mcp_host
    port = args.port or settings.mcp_port

    set_settings(settings)

    # Configure root logging to stderr
    logging.basicConfig(
        level=getattr(logging, settings.mcp_log_level.upper(), logging.INFO),
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        stream=sys.stderr,
    )

    server = create_server(settings)
    tools = await server.list_tools()
    logger.info(f"Initialized Splunk Enterprise MCP Server v{__version__} with {len(tools)} tools.")
    logger.info(f"Splunk Target: {settings.base_url} (Read-Only: {settings.mcp_read_only}, Transport: {transport})")

    if transport == "stdio":
        await server.run_stdio_async()
    elif transport == "sse":
        await server.run_sse_async(host=host, port=port)
    elif transport == "streamable-http":
        await server.run_streamable_http_async(host=host, port=port)
    else:
        logger.error(f"Unsupported transport protocol: {transport}")
        sys.exit(1)


def main() -> None:
    """Synchronous entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Splunk MCP Server interrupted by user. Exiting cleanly.")
    except Exception as e:
        logger.error(f"Fatal error starting Splunk MCP Server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
