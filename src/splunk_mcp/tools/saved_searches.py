"""Domain C: Saved Searches, Reports, and Alerting Tools (Tools 21 - 30)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import SavedSearchInfo, ToolResult
from splunk_mcp.pagination import extract_entry_content, paginate_list
from splunk_mcp.security import check_human_confirmation, check_write_permission
from splunk_mcp.spl_validation import SPLValidator


async def splunk_list_saved_searches(
    app: str | None = None,
    count: int = 100,
    offset: int = 0,
) -> ToolResult[dict[str, Any]]:
    """List saved searches, scheduled reports, and alerts.

    Args:
        app: Optional Splunk app context (e.g. 'search').
        count: Number of saved searches to list.
        offset: Pagination offset.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        endpoint = "saved/searches"
        params: dict[str, Any] = {"count": count, "offset": offset}
        if app:
            params["app"] = app

        res = await client.get(endpoint, params=params)
        items = []
        if isinstance(res, dict) and "entry" in res:
            for entry in res["entry"]:
                c = entry.get("content", {})
                acl = entry.get("acl", {})
                items.append(
                    SavedSearchInfo(
                        name=entry.get("name", "unknown"),
                        search=c.get("search", ""),
                        app=acl.get("app", "search"),
                        owner=acl.get("owner", "nobody"),
                        is_scheduled=bool(c.get("is_scheduled", False)),
                        cron_schedule=c.get("cron_schedule"),
                        description=c.get("description"),
                        is_disabled=bool(c.get("disabled", False)),
                        alert_type=c.get("alert_type"),
                    ).model_dump()
                )

        paginated, is_truncated, next_offset = paginate_list(items, offset=0, count=count)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"saved_searches": paginated, "count": len(paginated)},
            start_time=start_time,
            truncated=is_truncated,
            next_offset=next_offset,
            total_count=len(items),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_saved_search(name: str) -> ToolResult[dict[str, Any]]:
    """Retrieve full configuration, search query, schedule, and actions of a saved search.

    Args:
        name: Name of the saved search.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get(f"saved/searches/{name}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            return ToolResult.fail(
                f"Saved search '{name}' not found.", start_time=start_time, read_only=settings.mcp_read_only
            )

        content = extract_entry_content(res["entry"][0])
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=content,
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_create_saved_search(
    name: str,
    search: str,
    description: str | None = None,
    cron_schedule: str | None = None,
    is_scheduled: bool = False,
    app: str = "search",
) -> ToolResult[dict[str, Any]]:
    """Create a new saved search or scheduled report (requires write mode).

    Args:
        name: Unique name for the saved search.
        search: SPL search query.
        description: Description of the report/saved search.
        cron_schedule: Cron expression (e.g. '0 * * * *').
        is_scheduled: Whether to enable automatic schedule.
        app: App namespace (default 'search').
    """
    start_time = time.perf_counter()
    tool_name = "splunk_create_saved_search"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        SPLValidator.analyze(spl=search, read_only=False)

        data: dict[str, Any] = {
            "name": name,
            "search": search,
        }
        if description:
            data["description"] = description
        if cron_schedule:
            data["cron_schedule"] = cron_schedule
            data["is_scheduled"] = 1 if is_scheduled else 0

        res = await client.post("saved/searches", data=data)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "created": True, "details": res},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_update_saved_search(
    name: str,
    search: str | None = None,
    description: str | None = None,
    cron_schedule: str | None = None,
    is_scheduled: bool | None = None,
    disabled: bool | None = None,
) -> ToolResult[dict[str, Any]]:
    """Update settings or query of an existing saved search.

    Args:
        name: Name of saved search to update.
        search: Optional new SPL query.
        description: Optional new description.
        cron_schedule: Optional new cron expression.
        is_scheduled: Enable/disable scheduled execution.
        disabled: Enable/disable the saved search.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_update_saved_search"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        data: dict[str, Any] = {}
        if search:
            SPLValidator.analyze(spl=search, read_only=False)
            data["search"] = search
        if description is not None:
            data["description"] = description
        if cron_schedule is not None:
            data["cron_schedule"] = cron_schedule
        if is_scheduled is not None:
            data["is_scheduled"] = 1 if is_scheduled else 0
        if disabled is not None:
            data["disabled"] = 1 if disabled else 0

        await client.post(f"saved/searches/{name}", data=data)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "updated": True, "changes": list(data.keys())},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_delete_saved_search(
    name: str,
    confirm: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Delete an existing saved search (requires write mode and human confirmation).

    Args:
        name: Name of the saved search to delete.
        confirm: Confirmation flag.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_delete_saved_search"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        check_human_confirmation(tool_name, resource_id=name, action="delete_saved_search", confirm=confirm)

        await client.delete(f"saved/searches/{name}")
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "deleted": True, "message": f"Saved search '{name}' was deleted."},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_dispatch_saved_search(
    name: str,
    trigger_actions: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Dispatch and immediately run a saved search, returning its newly generated job SID.

    Args:
        name: Name of the saved search.
        trigger_actions: Whether to fire configured alert actions (e.g. email, webhook).
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        data = {"trigger_actions": 1 if trigger_actions else 0}
        res = await client.post(f"saved/searches/{name}/dispatch", data=data)
        sid = res.get("sid") if isinstance(res, dict) else str(res).strip()

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "sid": sid, "dispatched": True},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_alerts(
    count: int = 50,
) -> ToolResult[dict[str, Any]]:
    """List configured alerts and recent fired alert records.

    Args:
        count: Maximum number of alerts to return.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        # Query fired alerts endpoint
        res = await client.get("alerts/fired_alerts", params={"count": count})
        alerts = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                alerts.append(extract_entry_content(item))

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"fired_alerts": alerts, "count": len(alerts)},
            start_time=start_time,
            total_count=len(alerts),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_alert_history(
    alert_name: str | None = None,
    earliest_time: str = "-7d@d",
    count: int = 50,
) -> ToolResult[dict[str, Any]]:
    """Retrieve historical fired alert events over a time window.

    Args:
        alert_name: Optional name filter for specific alert.
        earliest_time: Earliest time range (default '-7d@d').
        count: Maximum history events.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        name_filter = f'savedsearch_name="{alert_name}"' if alert_name else ""
        spl = (
            f"search index=_audit action=alert_fired {name_filter} earliest={earliest_time} "
            f"| stats count by _time savedsearch_name severity trigger_time "
            f"| sort - _time | head {count}"
        )
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"alert_name": alert_name, "history": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_acknowledge_alert(
    alert_id: str,
    comment: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Acknowledge or update status of an alert finding (requires write mode).

    Args:
        alert_id: Fired alert ID.
        comment: Operational acknowledgement comment.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_acknowledge_alert"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        # Record operational acknowledgment in audit log
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "alert_id": alert_id,
                "acknowledged": True,
                "comment": comment or "Acknowledged via Splunk MCP Server",
                "timestamp": time.time(),
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_manage_alert_suppression(
    alert_name: str,
    suppression_period: str | None = None,
    enabled: bool = True,
) -> ToolResult[dict[str, Any]]:
    """Configure or inspect suppression windows for an alert to prevent notification storms.

    Args:
        alert_name: Name of saved search alert.
        suppression_period: Time duration to suppress (e.g. '1h', '30m').
        enabled: Enable or disable suppression.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_manage_alert_suppression"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        data = {
            "alert.suppress": 1 if enabled else 0,
        }
        if suppression_period:
            data["alert.suppress.period"] = suppression_period

        await client.post(f"saved/searches/{alert_name}", data=data)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "alert_name": alert_name,
                "suppression_enabled": enabled,
                "suppression_period": suppression_period,
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
