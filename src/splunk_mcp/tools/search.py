"""Domain A: SPL Search and Execution Tools (Tools 1 - 10)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.audit import get_audit_store
from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.pagination import paginate_list
from splunk_mcp.security import check_human_confirmation, check_write_permission, wrap_untrusted_content
from splunk_mcp.spl_validation import SPLValidator


async def splunk_search(
    spl: str,
    earliest_time: str | None = None,
    latest_time: str | None = None,
    count: int = 100,
    offset: int = 0,
) -> ToolResult[dict[str, Any]]:
    """Execute a synchronous blocking SPL search within an explicit time window.

    Args:
        spl: SPL search string (e.g. 'index=_internal | stats count by sourcetype').
        earliest_time: Earliest time bound (e.g. '-24h@h', '-15m', '1710000000').
        latest_time: Latest time bound (e.g. 'now', '@h').
        count: Maximum number of results to retrieve (capped by SPLUNK_MAX_RESULTS).
        offset: Offset index for pagination.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_search"
    settings = get_settings()
    audit_store = get_audit_store()
    client = get_splunk_client()

    earliest = earliest_time or settings.splunk_default_time_range
    effective_count = min(count, settings.splunk_max_results)

    try:
        analysis = SPLValidator.analyze(
            spl=spl,
            read_only=settings.mcp_read_only,
            earliest_time=earliest,
            latest_time=latest_time,
        )

        sid = await client.create_search_job(
            spl=spl,
            earliest_time=earliest,
            latest_time=latest_time,
            exec_mode="blocking",
            max_count=effective_count,
        )

        results = await client.get_job_results(sid, offset=offset, count=effective_count)
        paginated_items, is_truncated, next_offset = paginate_list(results, offset=0, count=effective_count)

        wrapped = wrap_untrusted_content(paginated_items)
        wrapped["sid"] = sid

        audit_store.record(
            request_id=sid,
            tool_name=tool_name,
            parameters={"spl": spl, "earliest": earliest, "count": effective_count},
            success=True,
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=wrapped,
            start_time=start_time,
            warnings=analysis.warnings,
            truncated=is_truncated,
            total_count=len(results),
            next_offset=next_offset,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        audit_store.record(
            request_id="",
            tool_name=tool_name,
            parameters={"spl": spl},
            success=False,
            error=str(e),
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_stream(
    spl: str,
    earliest_time: str | None = None,
    latest_time: str | None = None,
    count: int = 500,
) -> ToolResult[dict[str, Any]]:
    """Stream search results progressively via the Splunk export endpoint.

    Args:
        spl: SPL search string.
        earliest_time: Earliest time bound.
        latest_time: Latest time bound.
        count: Maximum number of events to stream.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_search_stream"
    settings = get_settings()
    audit_store = get_audit_store()
    client = get_splunk_client()

    earliest = earliest_time or settings.splunk_default_time_range
    effective_count = min(count, settings.splunk_max_results)

    try:
        analysis = SPLValidator.analyze(spl=spl, read_only=settings.mcp_read_only, earliest_time=earliest)
        results = await client.export_search_results(
            spl=spl,
            earliest_time=earliest,
            latest_time=latest_time,
            count=effective_count,
        )

        wrapped = wrap_untrusted_content(results)
        audit_store.record(
            request_id="",
            tool_name=tool_name,
            parameters={"spl": spl, "count": effective_count},
            success=True,
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=wrapped,
            start_time=start_time,
            warnings=analysis.warnings,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_async(
    spl: str,
    earliest_time: str | None = None,
    latest_time: str | None = None,
    max_count: int | None = None,
) -> ToolResult[dict[str, Any]]:
    """Initiate an asynchronous search job in the background and return its Job SID immediately.

    Args:
        spl: SPL query.
        earliest_time: Earliest time bound.
        latest_time: Latest time bound.
        max_count: Optional maximum count limit.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()
    earliest = earliest_time or settings.splunk_default_time_range

    try:
        analysis = SPLValidator.analyze(spl=spl, read_only=settings.mcp_read_only, earliest_time=earliest)
        sid = await client.create_search_job(
            spl=spl,
            earliest_time=earliest,
            latest_time=latest_time,
            exec_mode="normal",
            max_count=max_count,
        )
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"sid": sid, "status": "QUEUED", "spl": spl},
            start_time=start_time,
            warnings=analysis.warnings,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_status(sid: str) -> ToolResult[dict[str, Any]]:
    """Query execution status, progress percentage, and statistics of a Search Job by SID.

    Args:
        sid: Search Job ID.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        job_info = await client.get_job_status(sid)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=job_info.model_dump(),
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_results(
    sid: str,
    offset: int = 0,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Retrieve paginated results for a completed or running Search Job.

    Args:
        sid: Search Job ID.
        offset: Offset into results.
        count: Number of results to fetch.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        results = await client.get_job_results(sid=sid, offset=offset, count=count)
        paginated_items, is_truncated, next_offset = paginate_list(results, offset=0, count=count)
        wrapped = wrap_untrusted_content(paginated_items)
        wrapped["sid"] = sid
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=wrapped,
            start_time=start_time,
            truncated=is_truncated,
            next_offset=next_offset,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_events(
    sid: str,
    offset: int = 0,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Retrieve raw events associated with a Search Job.

    Args:
        sid: Search Job ID.
        offset: Offset into events.
        count: Number of events to fetch.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        events = await client.get_job_events(sid=sid, offset=offset, count=count)
        wrapped = wrap_untrusted_content(events)
        wrapped["sid"] = sid
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=wrapped,
            start_time=start_time,
            total_count=len(events),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_preview(sid: str, count: int = 50) -> ToolResult[dict[str, Any]]:
    """Retrieve preliminary preview results for an in-progress search job.

    Args:
        sid: Search Job ID.
        count: Number of preview results to fetch.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        preview = await client.get_job_preview(sid=sid, count=count)
        wrapped = wrap_untrusted_content(preview)
        wrapped["sid"] = sid
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=wrapped,
            start_time=start_time,
            total_count=len(preview),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_cancel(
    sid: str,
    confirm: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Cancel an active authorized search job.

    Args:
        sid: Search Job ID to cancel.
        confirm: Confirmation flag for cancellation.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_search_cancel"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        check_human_confirmation(tool_name, resource_id=sid, action="cancel_search", confirm=confirm)

        await client.cancel_job(sid)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"sid": sid, "cancelled": True, "message": f"Search job '{sid}' successfully cancelled."},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_explain(
    spl: str,
    earliest_time: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Validate SPL structure, analyze risk, performance anti-patterns, and cost estimation.

    Args:
        spl: SPL query to analyze.
        earliest_time: Optional earliest time bound.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        analysis = SPLValidator.analyze(
            spl=spl,
            read_only=settings.mcp_read_only,
            earliest_time=earliest_time,
        )
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=analysis.model_dump(),
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_history(count: int = 50) -> ToolResult[dict[str, Any]]:
    """Query recent search history and jobs dispatched by the current user.

    Args:
        count: Maximum number of history jobs to list.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("search/jobs", params={"count": count, "sort_key": "dispatch_time", "sort_dir": "desc"})
        entries = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                content = item.get("content", {})
                entries.append(
                    {
                        "sid": item.get("name"),
                        "search": content.get("eventSearch") or content.get("remoteSearch") or content.get("search"),
                        "dispatch_time": item.get("published"),
                        "dispatch_state": content.get("dispatchState"),
                        "run_duration": content.get("runDuration"),
                        "result_count": content.get("resultCount"),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"jobs": entries, "count": len(entries)},
            start_time=start_time,
            total_count=len(entries),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
