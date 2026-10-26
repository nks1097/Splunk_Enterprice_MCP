"""Domain D: Dashboards and Knowledge Objects Tools (Tools 31 - 40)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.pagination import extract_entry_content, paginate_list
from splunk_mcp.security import check_human_confirmation, check_write_permission


async def splunk_list_dashboards(
    app: str | None = None,
    count: int = 100,
    offset: int = 0,
) -> ToolResult[dict[str, Any]]:
    """List dashboards (Simple XML or Dashboard Studio) in the Splunk instance.

    Args:
        app: Optional Splunk app filter.
        count: Number of dashboards to retrieve.
        offset: Pagination offset.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        params: dict[str, Any] = {"count": count, "offset": offset}
        user = settings.splunk_username or "admin"
        app_name = app or "-"
        endpoint = f"servicesNS/{user}/{app_name}/data/ui/views"
        res = await client.get(endpoint, params=params)
        if not isinstance(res, dict) or "entry" not in res:
            res = await client.get("data/ui/views", params=params)
        dashboards = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                acl = item.get("acl", {})
                dashboards.append(
                    {
                        "name": item.get("name"),
                        "label": c.get("label") or item.get("name"),
                        "app": acl.get("app", "search"),
                        "owner": acl.get("owner", "nobody"),
                        "is_dashboard": c.get("isDashboard", True),
                        "root_node": c.get("rootNode"),
                    }
                )

        paginated, is_truncated, next_offset = paginate_list(dashboards, offset=0, count=count)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"dashboards": paginated, "count": len(paginated)},
            start_time=start_time,
            truncated=is_truncated,
            next_offset=next_offset,
            total_count=len(dashboards),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_dashboard(
    name: str,
    app: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Retrieve full XML or JSON definition of a dashboard.

    Args:
        name: Dashboard view name/id.
        app: Optional app namespace.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        user = settings.splunk_username or "admin"
        app_name = app or "search"
        endpoint = f"servicesNS/{user}/{app_name}/data/ui/views/{name}"
        res = await client.get(endpoint)
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            # Fallback to general endpoint
            endpoint_fallback = f"data/ui/views/{name}"
            res = await client.get(endpoint_fallback, params={"app": app} if app else None)
            if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
                return ToolResult.fail(
                    f"Dashboard '{name}' not found.", start_time=start_time, read_only=settings.mcp_read_only
                )

        item = res["entry"][0]
        content = extract_entry_content(item)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=content,
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_create_dashboard(
    name: str,
    label: str,
    xml_data: str,
    app: str = "search",
) -> ToolResult[dict[str, Any]]:
    """Create a new Simple XML or Dashboard Studio dashboard (requires write mode).

    Args:
        name: Unique dashboard view ID.
        label: Display title of dashboard.
        xml_data: XML or JSON dashboard definition.
        app: App namespace (default 'search').
    """
    start_time = time.perf_counter()
    tool_name = "splunk_create_dashboard"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        data = {
            "name": name,
            "eai:data": xml_data,
        }
        user = settings.splunk_username or "admin"
        app_name = app or "search"
        endpoint = f"servicesNS/{user}/{app_name}/data/ui/views"
        res = await client.post(endpoint, data=data)
        if isinstance(res, dict) and "messages" in res:
            for msg in res["messages"]:
                if msg.get("type") in ("ERROR", "FATAL"):
                    return ToolResult.fail(
                        f"Splunk error: {msg.get('text')}", start_time=start_time, read_only=settings.mcp_read_only
                    )
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "created": True, "app": app_name},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_update_dashboard(
    name: str,
    xml_data: str,
    label: str | None = None,
    app: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Update an existing dashboard definition (requires write mode).

    Args:
        name: Name of dashboard to update.
        xml_data: Updated XML/JSON definition.
        label: Optional new display title.
        app: Optional app namespace.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_update_dashboard"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        data: dict[str, Any] = {"eai:data": xml_data}
        if label:
            data["label"] = label

        user = settings.splunk_username or "admin"
        app_name = app or "search"
        endpoint = f"servicesNS/{user}/{app_name}/data/ui/views/{name}"
        await client.post(endpoint, data=data)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "updated": True},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_delete_dashboard(
    name: str,
    app: str | None = None,
    confirm: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Delete a dashboard (requires write mode and human confirmation).

    Args:
        name: Name of dashboard to delete.
        app: Optional app namespace.
        confirm: Confirmation flag.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_delete_dashboard"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        check_human_confirmation(tool_name, resource_id=name, action="delete_dashboard", confirm=confirm)

        user = settings.splunk_username or "admin"
        app_name = app or "search"
        endpoint = f"servicesNS/{user}/{app_name}/data/ui/views/{name}"
        await client.delete(endpoint)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "deleted": True, "message": f"Dashboard '{name}' was deleted."},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_reports(
    app: str | None = None,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """List scheduled and ad-hoc reports in the environment.

    Args:
        app: Optional app filter.
        count: Maximum number of reports to retrieve.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        params = {"count": count, "search": "is_visible=1"}
        if app:
            params["app"] = app

        res = await client.get("saved/searches", params=params)
        reports = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                reports.append(
                    {
                        "name": item.get("name"),
                        "search": c.get("search"),
                        "description": c.get("description"),
                        "is_scheduled": c.get("is_scheduled", False),
                        "cron_schedule": c.get("cron_schedule"),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"reports": reports, "count": len(reports)},
            start_time=start_time,
            total_count=len(reports),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_run_report(
    name: str,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Execute a named report and retrieve its generated results.

    Args:
        name: Name of the report/saved search.
        count: Maximum results to return.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        # Dispatch report
        res = await client.post(f"saved/searches/{name}/dispatch", data={})
        sid = res.get("sid") if isinstance(res, dict) else str(res).strip()

        # Wait briefly for execution or fetch results
        results = await client.get_job_results(sid=sid, offset=0, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"name": name, "sid": sid, "results": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_eventtypes(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List eventtypes, classifications, and search patterns.

    Args:
        count: Maximum number of eventtypes.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("saved/eventtypes", params={"count": count})
        items = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                items.append(
                    {
                        "name": item.get("name"),
                        "search": c.get("search"),
                        "priority": c.get("priority"),
                        "tags": c.get("tags", []),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"eventtypes": items, "count": len(items)},
            start_time=start_time,
            total_count=len(items),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_tags(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List tags assigned to fields and event classifications.

    Args:
        count: Maximum number of tags.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = "| rest /services/configs/conf-tags | fields title eai:acl.app eai:acl.owner | head " + str(count)
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"tags": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_macros(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List configured search macros, arguments, and definition strings.

    Args:
        count: Maximum number of macros.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("data/macros", params={"count": count})
        macros = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                macros.append(
                    {
                        "name": item.get("name"),
                        "definition": c.get("definition"),
                        "args": c.get("args"),
                        "description": c.get("description"),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"macros": macros, "count": len(macros)},
            start_time=start_time,
            total_count=len(macros),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
