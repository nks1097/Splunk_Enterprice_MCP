"""Integration tests verifying communication against a real live Splunk Enterprise instance.

Requires a reachable Splunk Enterprise instance configured in .env or environment variables.
"""

import pytest

from splunk_mcp.client import SplunkClient, set_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.tools import (
    splunk_get_server_health,
    splunk_get_server_info,
    splunk_list_indexes,
    splunk_search,
    splunk_test_connection,
)


@pytest.fixture(autouse=True)
def setup_live_client():
    """Ensure live client uses actual environment settings."""
    settings = get_settings()
    client = SplunkClient(settings)
    set_splunk_client(client)
    yield
    set_splunk_client(None)


@pytest.mark.asyncio
async def test_live_splunk_connection():
    """Verify live connectivity and handshake with the Splunk instance."""
    result = await splunk_test_connection()
    assert result.success is True, f"Connection failed: {result.error}"
    assert result.data["status"] == "CONNECTED"
    assert result.data["splunk_version"] != "unknown"
    print(f"\n[LIVE TEST] Connected to {result.data['server_name']} (Splunk v{result.data['splunk_version']})")


@pytest.mark.asyncio
async def test_live_splunk_server_info():
    """Verify retrieving server information from live Splunk."""
    result = await splunk_get_server_info()
    assert result.success is True, f"Failed: {result.error}"
    assert result.data["version"] is not None
    assert result.data["license_state"] in ("OK", "EXPIRED", "WARN", None)


@pytest.mark.asyncio
async def test_live_splunk_server_health():
    """Verify health report from live Splunk."""
    result = await splunk_get_server_health()
    assert result.success is True, f"Failed: {result.error}"
    assert result.data["overall_health"] in ("GREEN", "YELLOW", "RED")


@pytest.mark.asyncio
async def test_live_splunk_search():
    """Execute a real SPL query on the live instance."""
    spl = '| makeresults count=3 | eval test_status="LIVE_SEARCH_SUCCESS", agent="Splunk_MCP"'
    result = await splunk_search(spl=spl, count=5)
    assert result.success is True, f"Search failed: {result.error}"
    assert result.data is not None
    assert "records" in result.data
    records = result.data["records"]
    assert len(records) > 0
    assert records[0]["test_status"] == "LIVE_SEARCH_SUCCESS"
    print(f"[LIVE TEST] Executed SPL search. SID: {result.data.get('sid')}, Records: {len(records)}")


@pytest.mark.asyncio
async def test_live_splunk_list_indexes():
    """List actual indexes configured on the live Splunk instance."""
    result = await splunk_list_indexes(count=20)
    assert result.success is True, f"Failed: {result.error}"
    indexes = result.data["indexes"]
    assert len(indexes) > 0
    index_names = [idx["name"] for idx in indexes]
    assert "main" in index_names or "_internal" in index_names
    print(f"[LIVE TEST] Found {len(indexes)} indexes on target host: {index_names[:5]}")
