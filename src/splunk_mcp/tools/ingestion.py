"""Domain F: Ingestion, Forwarders, and Pipeline Monitoring Tools (Tools 51 - 60)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.pagination import extract_entry_content
from splunk_mcp.security import escape_spl_value


async def splunk_list_inputs(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List configured data inputs (TCP, UDP, monitor, scripts, HTTP Event Collector).

    Args:
        count: Maximum number of inputs.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("data/inputs/all", params={"count": count})
        inputs = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                inputs.append(
                    {
                        "name": item.get("name"),
                        "index": c.get("index"),
                        "sourcetype": c.get("sourcetype"),
                        "disabled": c.get("disabled", False),
                        "connection_host": c.get("connection_host"),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"inputs": inputs, "count": len(inputs)},
            start_time=start_time,
            total_count=len(inputs),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_input(
    input_type: str,
    name: str,
) -> ToolResult[dict[str, Any]]:
    """Get configuration and status of a specific input stanza.

    Args:
        input_type: Input type (e.g. 'monitor', 'tcp/raw', 'http', 'script').
        name: Stanza name or port.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get(f"data/inputs/{input_type}/{name}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            return ToolResult.fail(
                f"Input '{input_type}/{name}' not found.", start_time=start_time, read_only=settings.mcp_read_only
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


async def splunk_list_forwarders(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List connected Universal and Heavy Forwarders observed in the indexing pipeline.

    Args:
        count: Maximum number of forwarders.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            "index=_internal sourcetype=splunkd group=tcpin_connections earliest=-24h "
            "| stats latest(version) as version latest(arch) as arch latest(os) as os "
            "  latest(fwdType) as fwdType sum(kb) as total_kb latest(_time) as last_seen by hostname "
            '| eval last_seen=strftime(last_seen, "%Y-%m-%d %H:%M:%S"), total_mb=round(total_kb/1024, 2) '
            "| fields hostname fwdType version os arch total_mb last_seen | sort - total_mb | head " + str(count)
        )
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"forwarders": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_forwarder_status(hostname: str) -> ToolResult[dict[str, Any]]:
    """Inspect transmission volume, connection drops, and status for a specific forwarder.

    Args:
        hostname: Forwarder hostname.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f'index=_internal sourcetype=splunkd group=tcpin_connections hostname="{escape_spl_value(hostname)}" earliest=-24h '
            f"| stats latest(version) as version latest(fwdType) as fwdType sum(kb) as total_kb "
            f"  latest(_time) as last_seen by hostname "
            f'| eval now=now(), lag_seconds=now-last_seen, last_seen_str=strftime(last_seen, "%Y-%m-%d %H:%M:%S") '
            f'| eval status=if(lag_seconds < 900, "ACTIVE", if(lag_seconds < 86400, "SILENT", "MISSING"))'
        )
        results = await client.run_search_sync(spl=spl, count=10)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"hostname": hostname, "status": results[0] if results else {"status": "NOT_FOUND"}},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_check_forwarder_connectivity(threshold_minutes: int = 15) -> ToolResult[dict[str, Any]]:
    """Detect missing forwarders that stopped transmitting data beyond expected threshold.

    Args:
        threshold_minutes: Minutes without data before flagging as disconnected (default 15).
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        threshold_sec = threshold_minutes * 60
        spl = (
            f"index=_internal sourcetype=splunkd group=tcpin_connections earliest=-24h "
            f"| stats latest(_time) as last_seen latest(version) as version by hostname "
            f"| eval lag_seconds=now()-last_seen, threshold={threshold_sec} "
            f"| where lag_seconds > threshold "
            f'| eval last_seen=strftime(last_seen, "%Y-%m-%d %H:%M:%S"), inactive_minutes=round(lag_seconds/60, 1) '
            f"| fields hostname version last_seen inactive_minutes | sort - inactive_minutes"
        )
        results = await client.run_search_sync(spl=spl, count=100)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"threshold_minutes": threshold_minutes, "missing_forwarders": results, "count": len(results)},
            start_time=start_time,
            warnings=[f"{len(results)} forwarders have ceased communicating."] if results else [],
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_ingestion_metrics(
    time_span: str = "1h",
    earliest_time: str = "-24h@h",
) -> ToolResult[dict[str, Any]]:
    """Retrieve historical ingestion throughput (MB/hour) broken down by index.

    Args:
        time_span: Bucket span (e.g. '15m', '1h').
        earliest_time: Earliest search window.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"index=_internal sourcetype=splunkd group=per_index_thruput earliest={earliest_time} "
            f"| eval mb=kb/1024 "
            f"| timechart span={time_span} sum(mb) as total_mb by series"
        )
        results = await client.run_search_sync(spl=spl, count=200)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"span": time_span, "metrics": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_ingestion_lag(
    index: str,
    sourcetype: str | None = None,
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Measure pipeline processing lag between event occurrence timestamp and indexing time.

    Args:
        index: Index to evaluate.
        sourcetype: Optional sourcetype filter.
        count: Sample size of events.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        st_filter = f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = (
            f'search index="{escape_spl_value(index)}" {st_filter} earliest=-4h '
            f"| eval lag_seconds=_indextime - _time "
            f"| stats avg(lag_seconds) as avg_lag, min(lag_seconds) as min_lag, max(lag_seconds) as max_lag, p95(lag_seconds) as p95_lag by sourcetype "
            f"| eval avg_lag=round(avg_lag, 2), p95_lag=round(p95_lag, 2)"
        )
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": index, "lag_statistics": results},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_parsing_errors(earliest_time: str = "-24h@h") -> ToolResult[dict[str, Any]]:
    """Detect timestamp parsing, line-breaking, and regex extraction errors recorded in _internal.

    Args:
        earliest_time: Search window (default '-24h@h').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"index=_internal (component=LineBreakingProcessor OR component=DateParserVerbose OR component=RegexProcessor) "
            f"log_level=WARN OR log_level=ERROR earliest={earliest_time} "
            f"| stats count by component log_level event_message "
            f"| sort - count | head 50"
        )
        results = await client.run_search_sync(spl=spl, count=50)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"parsing_errors": results, "count": len(results)},
            start_time=start_time,
            warnings=["Parsing errors detected in Splunk ingestion pipeline."] if results else [],
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_check_source_coverage(
    expected_sources: list[str],
    index: str = "main",
    lookback: str = "-4h",
) -> ToolResult[dict[str, Any]]:
    """Verify that expected data sources are active and currently indexing data.

    Args:
        expected_sources: List of expected source or sourcetype strings.
        index: Target index.
        lookback: Time interval to inspect.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = f'| metadata type=sources index="{escape_spl_value(index)}" | fields source totalCount recentTime'
        results = await client.run_search_sync(spl=spl, count=500)
        active_sources = {r.get("source") for r in results}

        missing = [s for s in expected_sources if s not in active_sources]
        present = [s for s in expected_sources if s in active_sources]

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "index": index,
                "total_expected": len(expected_sources),
                "active_count": len(present),
                "missing_count": len(missing),
                "missing_sources": missing,
                "active_sources": present,
            },
            start_time=start_time,
            warnings=[f"{len(missing)} expected sources are absent from index '{index}'."] if missing else [],
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_diagnose_ingestion() -> ToolResult[dict[str, Any]]:
    """Composite diagnostic: evaluate overall pipeline health, queue sizes, drop rates, and bottlenecks."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        # Check queue saturation
        queue_spl = (
            "index=_internal sourcetype=splunkd group=queue (name=parsingqueue OR name=indexqueue OR name=typingqueue) earliest=-30m "
            "| stats latest(current_size) as curr_size latest(max_size) as max_size latest(fill_percentage) as fill by name "
            "| eval fill=round(fill, 1)"
        )
        queues = await client.run_search_sync(spl=queue_spl, count=10)

        # Check ingestion drops or blocked queues
        blocked_spl = (
            "index=_internal sourcetype=splunkd log_level=WARN component=Queue blocked earliest=-30m "
            "| stats count by message | head 10"
        )
        blocked = await client.run_search_sync(spl=blocked_spl, count=10)

        # Evaluate health status
        is_blocked = len(blocked) > 0
        saturated_queues = [q for q in queues if float(q.get("fill", 0)) > 80.0]

        status = "HEALTHY"
        recommendations = []
        if is_blocked or saturated_queues:
            status = "CRITICAL" if is_blocked else "WARNING"
            recommendations.append("High queue fill detected. Inspect indexer disk I/O and consider pipeline scaling.")
        else:
            recommendations.append("Ingestion queues are within nominal capacity limits (<80% fill).")

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "pipeline_status": status,
                "queues": queues,
                "blocked_events_count": len(blocked),
                "saturated_queues": saturated_queues,
                "recommendations": recommendations,
            },
            start_time=start_time,
            warnings=[f"Pipeline status is {status}"] if status != "HEALTHY" else [],
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
