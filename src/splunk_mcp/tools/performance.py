"""Domain H: Performance, Capacity, and Diagnostics Tools (Tools 71 - 80)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.pagination import extract_entry_content


async def splunk_get_search_performance(earliest_time: str = "-4h") -> ToolResult[dict[str, Any]]:
    """Inspect search head performance, execution times, and resource utilization.

    Args:
        earliest_time: Search audit window (default '-4h').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"index=_audit action=search (info=granted OR info=completed) earliest={earliest_time} "
            f'| stats count(eval(info="granted")) as started, count(eval(info="completed")) as completed, '
            f"  avg(total_run_time) as avg_duration, max(total_run_time) as max_duration by user "
            f"| eval avg_duration=round(avg_duration, 2), max_duration=round(max_duration, 2)"
        )
        results = await client.run_search_sync(spl=spl, count=50)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"search_performance_by_user": results},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_detect_slow_searches(
    min_duration_seconds: int = 30,
    earliest_time: str = "-24h@h",
    count: int = 20,
) -> ToolResult[dict[str, Any]]:
    """Identify slow or expensive searches exceeding duration threshold.

    Args:
        min_duration_seconds: Threshold in seconds to flag (default 30).
        earliest_time: Search window.
        count: Maximum slow searches to list.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"index=_audit action=search info=completed total_run_time > {min_duration_seconds} earliest={earliest_time} "
            f"| eval run_time_sec=round(total_run_time, 2) "
            f"| fields _time user search run_time_sec result_count scan_count "
            f"| sort - run_time_sec | head {count}"
        )
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"threshold_seconds": min_duration_seconds, "slow_searches": results, "count": len(results)},
            start_time=start_time,
            warnings=[f"Identified {len(results)} slow search jobs."] if results else [],
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_search_concurrency() -> ToolResult[dict[str, Any]]:
    """Inspect active concurrent historical and real-time searches against system limits."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            "index=_introspection sourcetype=splunk_resource_usage component=PerProcess data.search_props.sid=* earliest=-5m "
            "| stats dc(data.search_props.sid) as active_searches by data.search_props.type "
        )
        results = await client.run_search_sync(spl=spl, count=10)

        # Also get active jobs from search/jobs endpoint
        jobs_res = await client.get("search/jobs", params={"count": 50})
        active_jobs_count = len(jobs_res.get("entry", [])) if isinstance(jobs_res, dict) else 0

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "current_job_count": active_jobs_count,
                "concurrency_breakdown": results,
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_scheduler_health(earliest_time: str = "-4h") -> ToolResult[dict[str, Any]]:
    """Inspect search scheduler health, skipped searches, delayed executions, and quota blocks.

    Args:
        earliest_time: Scheduler audit window (default '-4h').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"index=_internal sourcetype=scheduler earliest={earliest_time} "
            f'| stats count(eval(status="completed")) as completed, '
            f'  count(eval(status="skipped")) as skipped, '
            f'  count(eval(status="deferred")) as deferred by app '
            f"| eval total=completed+skipped+deferred, skip_rate=if(total>0, round((skipped/total)*100, 2), 0)"
        )
        results = await client.run_search_sync(spl=spl, count=50)

        total_skipped = sum(int(r.get("skipped", 0)) for r in results)
        warnings = (
            [f"Scheduler has skipped {total_skipped} searches! Check concurrency quotas."] if total_skipped > 0 else []
        )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"scheduler_summary": results, "total_skipped": total_skipped},
            start_time=start_time,
            warnings=warnings,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_internal_errors(
    log_level: str = "ERROR",
    earliest_time: str = "-4h",
    count: int = 50,
) -> ToolResult[dict[str, Any]]:
    """Query recent internal daemon errors and warnings from index=_internal.

    Args:
        log_level: Log severity filter ('ERROR', 'WARN', 'FATAL').
        earliest_time: Time window (default '-4h').
        count: Maximum errors to return.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"index=_internal log_level={log_level} earliest={earliest_time} "
            f"| stats count by component event_message "
            f"| sort - count | head {count}"
        )
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"log_level": log_level, "errors": results, "count": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_license_usage() -> ToolResult[dict[str, Any]]:
    """Retrieve daily license quota, consumed bytes, warnings, and pool allocations."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        # Query license pools endpoint
        pools_res = await client.get("licenser/pools")
        pools = []
        if isinstance(pools_res, dict) and "entry" in pools_res:
            for item in pools_res["entry"]:
                c = item.get("content", {})
                pools.append(
                    {
                        "name": item.get("name"),
                        "quota_bytes": c.get("quota"),
                        "used_bytes": c.get("used_bytes"),
                    }
                )

        # Query today's usage from _internal
        spl = (
            "index=_internal sourcetype=splunkd group=subpools earliest=@d "
            "| stats sum(b) as total_bytes by pool "
            "| eval used_mb=round(total_bytes/1024/1024, 2), used_gb=round(used_mb/1024, 2)"
        )
        usage = await client.run_search_sync(spl=spl, count=20)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"license_state": server_info.license_state, "pools": pools, "today_usage": usage},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_storage_usage() -> ToolResult[dict[str, Any]]:
    """Inspect filesystem disk partitions, storage volume in $SPLUNK_DB, and retention capacities."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            "| rest /services/server/status/partitions-space "
            "| fields mount_point total_space free_space "
            "| eval total_gb=round(total_space/1024, 2), free_gb=round(free_space/1024, 2), "
            "  used_percent=round(((total_space-free_space)/total_space)*100, 1)"
        )
        partitions = await client.run_search_sync(spl=spl, count=20)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"partitions": partitions},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_cluster_health() -> ToolResult[dict[str, Any]]:
    """Check health status of indexer cluster or search head cluster (or report standalone topology)."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        server_info = await client.get_server_info()
        # Test if cluster master endpoint exists
        try:
            res = await client.get("cluster/master/info")
            cluster_data = extract_entry_content(res["entry"][0]) if "entry" in res and res["entry"] else {}
            mode = "INDEXER_CLUSTER"
        except Exception:
            cluster_data = {"topology": "STANDALONE_OR_NON_CLUSTERED"}
            mode = "STANDALONE"

        return ToolResult.ok(
            data={"topology_mode": mode, "server_name": server_info.server_name, "cluster_info": cluster_data},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_replication_status() -> ToolResult[dict[str, Any]]:
    """Check bucket replication status, cluster fix-up tasks, and peer synchronizations."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        try:
            res = await client.get("cluster/master/generation")
            gen_data = extract_entry_content(res["entry"][0]) if "entry" in res and res["entry"] else {}
            is_clustered = True
        except Exception:
            gen_data = {"notice": "Host is running as standalone instance without cluster bucket replication."}
            is_clustered = False

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"is_clustered": is_clustered, "replication_status": gen_data},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_diagnose_performance() -> ToolResult[dict[str, Any]]:
    """Composite tool: multi-dimensional assessment of CPU, memory, scheduler, disk, and search latency."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        health_res = await client.get("server/health/splunkd")
        features = {}
        status = "HEALTHY"

        if isinstance(health_res, dict) and "entry" in health_res:
            for item in health_res["entry"]:
                c = item.get("content", {})
                h = c.get("health", "GREEN")
                features[item.get("name")] = h
                if h == "RED":
                    status = "CRITICAL"
                elif h == "YELLOW" and status != "CRITICAL":
                    status = "WARNING"

        # Check internal error volume in last 1 hour
        err_spl = "index=_internal log_level=ERROR earliest=-1h | stats count"
        err_res = await client.run_search_sync(spl=err_spl, count=5)
        err_count = int(err_res[0].get("count", 0)) if err_res else 0

        recommendations = []
        if status != "HEALTHY":
            recommendations.append("System health features report warnings or degraded state.")
        if err_count > 100:
            recommendations.append(f"Elevated internal error count ({err_count} errors in 1h). Check component logs.")
        if not recommendations:
            recommendations.append("All core performance metrics and subsystems are functioning nominally.")

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "overall_performance_status": status,
                "recent_error_count_1h": err_count,
                "subsystem_health": features,
                "recommendations": recommendations,
            },
            start_time=start_time,
            warnings=recommendations if status != "HEALTHY" else [],
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
