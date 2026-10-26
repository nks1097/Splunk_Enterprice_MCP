"""Pytest configuration and test fixtures."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from splunk_mcp.client import SplunkClient, set_splunk_client
from splunk_mcp.config import Settings, set_settings
from splunk_mcp.models import SearchJobInfo, ServerInfo
from tests.fixtures.mock_responses import (
    MOCK_APPS,
    MOCK_INDEXES,
    MOCK_ROLES,
    MOCK_SAVED_SEARCHES,
    MOCK_SEARCH_RESULTS,
    MOCK_SERVER_HEALTH,
    MOCK_SERVER_INFO,
    MOCK_USERS,
    MOCK_VIEWS,
)


@pytest.fixture(autouse=True)
def reset_globals(request):
    """Reset configuration and client instances between tests."""
    if "integration" not in request.node.nodeid:
        settings = Settings(
            splunk_host="test-splunk.local",
            splunk_port=8089,
            splunk_scheme="https",
            mcp_read_only=True,
        )
        set_settings(settings)
    else:
        # For integration tests, use actual .env configuration
        set_settings(Settings())
    yield
    set_splunk_client(None)


@pytest.fixture
def mock_client():
    """Create a fully mocked SplunkClient returning valid fixtures."""
    client = MagicMock(spec=SplunkClient)
    client.settings = Settings(mcp_read_only=True)

    client.get_server_info = AsyncMock(
        return_value=ServerInfo(
            server_name="splunk-test-host",
            version="10.6.1.1",
            build="b2ae2962645c",
            os_name="Linux",
            cpu_arch="x86_64",
            license_state="OK",
            server_roles=["indexer", "search_head"],
            mode="normal",
        )
    )

    client.create_search_job = AsyncMock(return_value="mock_sid_1710000000.1")
    client.get_job_status = AsyncMock(
        return_value=SearchJobInfo(
            sid="mock_sid_1710000000.1",
            is_done=True,
            is_failed=False,
            is_paused=False,
            dispatch_state="DONE",
            done_progress=1.0,
            event_count=2,
            result_count=2,
            scan_count=10,
            run_duration=0.25,
        )
    )
    client.get_job_results = AsyncMock(return_value=MOCK_SEARCH_RESULTS["results"])
    client.get_job_events = AsyncMock(return_value=MOCK_SEARCH_RESULTS["results"])
    client.get_job_preview = AsyncMock(return_value=MOCK_SEARCH_RESULTS["results"])
    client.run_search_sync = AsyncMock(return_value=MOCK_SEARCH_RESULTS["results"])
    client.export_search_results = AsyncMock(return_value=MOCK_SEARCH_RESULTS["results"])
    client.cancel_job = AsyncMock(return_value=True)

    async def mock_get(endpoint, params=None):
        if "server/info" in endpoint:
            return MOCK_SERVER_INFO
        elif "server/health" in endpoint:
            return MOCK_SERVER_HEALTH
        elif "data/indexes" in endpoint:
            return MOCK_INDEXES
        elif "saved/searches" in endpoint:
            return MOCK_SAVED_SEARCHES
        elif "data/ui/views" in endpoint:
            return MOCK_VIEWS
        elif "apps/local" in endpoint:
            return MOCK_APPS
        elif "authentication/users" in endpoint:
            return MOCK_USERS
        elif "authorization/roles" in endpoint:
            return MOCK_ROLES
        elif "alerts/fired_alerts" in endpoint:
            return {"entry": [{"name": "Alert1", "content": {"severity": "high", "digest": "spike"}}]}
        elif "data/inputs" in endpoint:
            return {"entry": [{"name": "9997", "content": {"index": "main", "disabled": False}}]}
        elif "properties" in endpoint:
            return {"entry": [{"name": "props"}, {"name": "server"}]}
        elif "configs/conf-" in endpoint:
            return {"entry": [{"name": "default", "content": {"max_size": "500"}}]}
        elif "licenser/pools" in endpoint:
            return {"entry": [{"name": "pool1", "content": {"quota": 1000000, "used_bytes": 500000}}]}
        return {"entry": []}

    client.get = AsyncMock(side_effect=mock_get)
    client.post = AsyncMock(return_value={"sid": "mock_sid_post_1", "success": True})
    client.delete = AsyncMock(return_value={"success": True})

    set_splunk_client(client)
    return client
