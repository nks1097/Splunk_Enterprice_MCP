"""Domain B: Indexes, Events, and Data Discovery Tools (Tools 11 - 20)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import IndexInfo, ToolResult
from splunk_mcp.pagination import extract_entry_content, paginate_list
from splunk_mcp.security import escape_spl_value, wrap_untrusted_content


async def splunk_list_indexes(
    count: int = 100,
    offset: int = 0,
) -> ToolResult[dict[str, Any]]:
    """List accessible Splunk indexes with disk size, event count, and disabled status.

    Args:
        count: Number of indexes to list.
        offset: Pagination offset.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("data/indexes", params={"count": count, "offset": offset})
        indexes = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                indexes.append(
                    IndexInfo(
                        name=item.get("name", "unknown"),
                        total_event_count=int(c.get("totalEventCount", 0)),
                        current_size_mb=round(float(c.get("currentDBSizeMB", 0.0)), 2),
                        max_size_mb=round(float(c.get("maxTotalDataSizeMB", 0.0)), 2),
                        home_path=c.get("homePath"),
                        cold_path=c.get("coldPath"),
                        thawed_path=c.get("thawedPath"),
                        disabled=c.get("disabled", False),
                        frozen_time_period_in_secs=int(c.get("frozenTimePeriodInSecs", 0)),
                    ).model_dump()
                )

        paginated, is_truncated, next_offset = paginate_list(indexes, offset=0, count=count)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"indexes": paginated, "count": len(paginated)},
            start_time=start_time,
            truncated=is_truncated,
            next_offset=next_offset,
            total_count=len(indexes),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_index(name: str) -> ToolResult[dict[str, Any]]:
    """Query configuration, retention policies, and storage paths for a specific index.

    Args:
        name: Index name (e.g. 'main', '_internal', 'wineventlog').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get(f"data/indexes/{name}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            return ToolResult.fail(
                f"Index '{name}' not found.", start_time=start_time, read_only=settings.mcp_read_only
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


async def splunk_index_stats() -> ToolResult[dict[str, Any]]:
    """Retrieve aggregate storage volume and event statistics across all accessible indexes."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            "| rest /services/data/indexes "
            "| fields title totalEventCount currentDBSizeMB maxTotalDataSizeMB frozenTimePeriodInSecs disabled "
            "| eval currentDBSizeMB=round(currentDBSizeMB, 2) "
            "| sort - currentDBSizeMB"
        )
        results = await client.run_search_sync(spl=spl, count=200)

        total_size = sum(float(r.get("currentDBSizeMB", 0)) for r in results)
        total_events = sum(int(r.get("totalEventCount", 0)) for r in results)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "total_indexes": len(results),
                "total_storage_mb": round(total_size, 2),
                "total_storage_gb": round(total_size / 1024, 2),
                "total_events": total_events,
                "indexes": results,
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_sourcetypes(
    index: str | None = None,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Discover sourcetypes with event count and last seen recency.

    Args:
        index: Optional index filter (e.g. 'main', '_internal').
        count: Maximum number of sourcetypes to retrieve.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        idx_filter = f"index={escape_spl_value(index)}" if index else ""
        spl = f'| metadata type=sourcetypes {idx_filter} | eval recentTime=strftime(recentTime, "%Y-%m-%d %H:%M:%S") | sort - totalCount | head {count}'
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"sourcetypes": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_sources(
    index: str | None = None,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Discover event sources across indexes with event counts.

    Args:
        index: Optional index filter.
        count: Maximum number of sources to list.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        idx_filter = f"index={escape_spl_value(index)}" if index else ""
        spl = f'| metadata type=sources {idx_filter} | eval recentTime=strftime(recentTime, "%Y-%m-%d %H:%M:%S") | sort - totalCount | head {count}'
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"sources": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_hosts(
    index: str | None = None,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Discover hosts reporting data into Splunk with event counts and latest observed timestamp.

    Args:
        index: Optional index filter.
        count: Maximum number of hosts to list.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        idx_filter = f"index={escape_spl_value(index)}" if index else ""
        spl = f'| metadata type=hosts {idx_filter} | eval recentTime=strftime(recentTime, "%Y-%m-%d %H:%M:%S") | sort - totalCount | head {count}'
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"hosts": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_field_summary(
    index: str,
    sourcetype: str | None = None,
    sample_count: int = 500,
) -> ToolResult[dict[str, Any]]:
    """Obtain statistical distribution of fields and top values for an index and sourcetype.

    Args:
        index: Target index name.
        sourcetype: Optional sourcetype filter.
        sample_count: Number of events to sample for summary.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        st_filter = f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = f'search index="{escape_spl_value(index)}" {st_filter} earliest=-24h | head {sample_count} | fieldsummary'
        results = await client.run_search_sync(spl=spl, count=100)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": index, "sourcetype": sourcetype, "fields": results},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_data_freshness(
    index: str,
    sourcetype: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Evaluate data recency, latest event timestamp, and ingestion latency.

    Args:
        index: Target index.
        sourcetype: Optional sourcetype.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = (
            f'| metadata type=sourcetypes index="{escape_spl_value(index)}" '
            f"| eval now=now(), lag_seconds=now-recentTime "
            f'| eval latest_event=strftime(recentTime, "%Y-%m-%d %H:%M:%S"), status=if(lag_seconds < 300, "HEALTHY", if(lag_seconds < 3600, "DELAYED", "STALE")) '
            f"| fields sourcetype latest_event lag_seconds totalCount status"
        )
        results = await client.run_search_sync(spl=spl, count=50)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": index, "freshness_metrics": results},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_data_gaps(
    index: str,
    sourcetype: str | None = None,
    time_span: str = "1h",
    earliest_time: str = "-24h@h",
) -> ToolResult[dict[str, Any]]:
    """Detect time gaps in ingested data streams where expected events are missing.

    Args:
        index: Index to analyze.
        sourcetype: Optional sourcetype filter.
        time_span: Bucket duration for binning (e.g. '15m', '1h').
        earliest_time: Earliest search window.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        st_filter = f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = (
            f'search index="{escape_spl_value(index)}" {st_filter} earliest={earliest_time} '
            f"| timechart span={time_span} count "
            f"| fillnull value=0 count "
            f"| where count=0"
        )
        results = await client.run_search_sync(spl=spl, count=100)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": index, "gaps_detected": len(results), "gap_periods": results},
            start_time=start_time,
            warnings=["Data gaps detected where event count dropped to 0."] if results else [],
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_sample_events(
    index: str,
    sourcetype: str | None = None,
    count: int = 10,
) -> ToolResult[dict[str, Any]]:
    """Retrieve representative raw event samples without full table scans.

    Args:
        index: Target index.
        sourcetype: Optional sourcetype filter.
        count: Number of sample events (default 10, max 100).
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sample_count = min(count, 100)
        st_filter = f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = f'search index="{escape_spl_value(index)}" {st_filter} earliest=-24h | head {sample_count}'
        results = await client.run_search_sync(spl=spl, count=sample_count)

        wrapped = wrap_untrusted_content(results)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=wrapped,
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
