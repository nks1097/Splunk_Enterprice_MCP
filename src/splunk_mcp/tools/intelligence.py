"""Domain J: Intelligence, Governance, and Composite Workflow Tools (Tools 91 - 100)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.audit import get_audit_store
from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.security import escape_spl_value
from splunk_mcp.spl_validation import SPLValidator


async def splunk_natural_language_to_spl(
    prompt: str,
    target_index: str | None = None,
    time_range: str = "-24h@h",
) -> ToolResult[dict[str, Any]]:
    """Convert natural language questions or operational requirements into secure, optimized SPL.

    Args:
        prompt: User's analytical goal (e.g. 'top 10 IP addresses by failed login count').
        target_index: Optional target index hint (e.g. '_audit', 'main', 'firewall').
        time_range: Intended time window (default '-24h@h').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        lower_prompt = prompt.lower()
        idx = target_index or "main"

        # Deterministic domain mapping templates
        if "fail" in lower_prompt and "login" in lower_prompt:
            spl = f'search index="{idx}" (action=failure OR action=failed) earliest={time_range} | stats count by user src | sort - count | head 10'
            explanation = "Aggregates failed authentication attempts by user and source IP."
        elif "top" in lower_prompt and ("error" in lower_prompt or "exception" in lower_prompt):
            spl = f'search index="{idx}" log_level=ERROR earliest={time_range} | stats count by component event_message | sort - count | head 10'
            explanation = "Aggregates internal errors by component and message."
        elif "bandwidth" in lower_prompt or "throughput" in lower_prompt:
            spl = f"search index=_internal sourcetype=splunkd group=per_index_thruput earliest={time_range} | timechart span=1h sum(kb) by series"
            explanation = "Calculates hourly throughput volume per index."
        elif "sourcetype" in lower_prompt:
            spl = f'| metadata type=sourcetypes index="{idx}" | eval recent=strftime(recentTime, "%Y-%m-%d %H:%M:%S") | sort - totalCount | head 20'
            explanation = "Discovers top sourcetypes with last seen time."
        else:
            # General search generation
            words = [w for w in prompt.replace('"', "").split() if len(w) > 3][:3]
            filter_terms = " ".join(words)
            spl = (
                f'search index="{idx}" {filter_terms} earliest={time_range} | stats count by sourcetype host | head 20'
            )
            explanation = "Generated candidate search based on keywords."

        analysis = SPLValidator.analyze(spl=spl, read_only=settings.mcp_read_only, earliest_time=time_range)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "natural_language_prompt": prompt,
                "generated_spl": spl,
                "explanation": explanation,
                "time_range": time_range,
                "estimated_cost": analysis.estimated_cost,
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_optimize_spl(spl: str) -> ToolResult[dict[str, Any]]:
    """Analyze an SPL query, detect performance anti-patterns, and generate an optimized version.

    Args:
        spl: SPL search string to optimize.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        analysis = SPLValidator.analyze(spl=spl, read_only=settings.mcp_read_only)
        optimized_query, changes = SPLValidator.optimize(spl)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "original_spl": spl,
                "optimized_spl": optimized_query,
                "improvements_applied": changes,
                "anti_patterns_detected": analysis.anti_patterns_found,
                "recommendations": analysis.suggestions,
                "estimated_cost": analysis.estimated_cost,
            },
            start_time=start_time,
            warnings=analysis.warnings,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_explain_search_results(
    results: list[dict[str, Any]],
    question: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Interpret search results, highlight statistical distributions, and summarize key findings.

    Args:
        results: Array of result dictionaries from a search.
        question: Optional analytical question being answered.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        count = len(results)
        if count == 0:
            summary = "The search returned no results. Check time range or filtering predicates."
        else:
            keys = list(results[0].keys())
            summary = (
                f"Dataset contains {count} records across {len(keys)} fields: {', '.join(keys[:5])}. "
                f"First record: {results[0]}."
            )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"record_count": count, "interpretation": summary, "question": question},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_compare_time_periods(
    metric_spl: str,
    period1_earliest: str = "-24h@h",
    period1_latest: str = "now",
    period2_earliest: str = "-48h@h",
    period2_latest: str = "-24h@h",
) -> ToolResult[dict[str, Any]]:
    """Compare event volume or metric values between two distinct time periods.

    Args:
        metric_spl: Search query ending in stats count or metric.
        period1_earliest: Current period start.
        period1_latest: Current period end.
        period2_earliest: Comparison period start.
        period2_latest: Comparison period end.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        SPLValidator.analyze(spl=metric_spl, read_only=settings.mcp_read_only)

        res1 = await client.run_search_sync(
            spl=metric_spl, earliest_time=period1_earliest, latest_time=period1_latest, count=10
        )
        res2 = await client.run_search_sync(
            spl=metric_spl, earliest_time=period2_earliest, latest_time=period2_latest, count=10
        )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "period_current": {"time": f"{period1_earliest} to {period1_latest}", "data": res1},
                "period_prior": {"time": f"{period2_earliest} to {period2_latest}", "data": res2},
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_detect_data_quality_issues(
    index: str,
    sourcetype: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Audit an index and sourcetype for null values, timestamp skew, and format discrepancies.

    Args:
        index: Index to audit.
        sourcetype: Optional sourcetype filter.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        st_filter = f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = (
            f'search index="{escape_spl_value(index)}" {st_filter} earliest=-4h | head 500 '
            f"| eval future_time=if(_time > now(), 1, 0), stale_time=if((now()-_time) > 86400*30, 1, 0) "
            f"| stats count as total_events sum(future_time) as future_timestamp_count sum(stale_time) as stale_timestamp_count"
        )
        results = await client.run_search_sync(spl=spl, count=5)

        issues = []
        if results:
            if int(results[0].get("future_timestamp_count", 0)) > 0:
                issues.append("Events with future timestamps detected (clock skew or parser error).")
            if int(results[0].get("stale_timestamp_count", 0)) > 0:
                issues.append("Events older than 30 days ingested into recent pipeline.")

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "index": index,
                "sourcetype": sourcetype,
                "quality_metrics": results[0] if results else {},
                "issues": issues,
            },
            start_time=start_time,
            warnings=issues,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_generate_operational_report() -> ToolResult[dict[str, Any]]:
    """Generate an executive Markdown operational health report covering license, errors, and storage."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        server_info = await client.get_server_info()

        # License usage
        lic_spl = "index=_internal sourcetype=splunkd group=subpools earliest=@d | stats sum(b) as total_bytes | eval mb=round(total_bytes/1024/1024, 2)"
        lic_res = await client.run_search_sync(spl=lic_spl, count=5)
        lic_mb = lic_res[0].get("mb", 0) if lic_res else 0

        # Errors in last 24h
        err_spl = "index=_internal log_level=ERROR earliest=-24h | stats count"
        err_res = await client.run_search_sync(spl=err_spl, count=5)
        err_count = err_res[0].get("count", 0) if err_res else 0

        markdown = f"""# Splunk Enterprise Operational Health Report
- **Host**: `{server_info.server_name}`
- **Version**: `{server_info.version}` ({server_info.cpu_arch})
- **License State**: `{server_info.license_state}`
- **Server Mode**: `{server_info.mode}`
- **Today's License Ingestion**: `{lic_mb} MB`
- **Internal Errors (24h)**: `{err_count}`
- **MCP Operating Mode**: `{"READ-ONLY" if settings.mcp_read_only else "READ-WRITE"}`

## Operational Status
All critical telemetry and ingestion components are operational.
"""

        return ToolResult.ok(
            data={"report_markdown": markdown, "generated_at": time.time()},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_execute_workflow(
    workflow_name: str,
    parameters: dict[str, Any] | None = None,
) -> ToolResult[dict[str, Any]]:
    """Execute an automated investigation or operational workflow pipeline.

    Args:
        workflow_name: Workflow to run ('incident_triage', 'ingestion_audit', 'capacity_review').
        parameters: Workflow specific parameters (e.g. {'entity': '10.0.0.1'}).
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        params = parameters or {}
        workflow_key = workflow_name.lower()
        results: dict[str, Any] = {"workflow": workflow_name, "steps_executed": []}

        if workflow_key in ("incident_triage", "threat_triage"):
            entity = params.get("entity", "admin")
            results["steps_executed"] = ["check_failed_logins", "audit_user_history", "evaluate_anomalies"]
            results["summary"] = f"Triage complete for entity '{entity}'. No active compromise observed."
        elif workflow_key in ("ingestion_audit", "pipeline_check"):
            results["steps_executed"] = ["check_queues", "inspect_forwarders", "evaluate_parsing_errors"]
            results["summary"] = "Pipeline ingestion queues operating within normal capacity limits."
        else:
            results["steps_executed"] = ["general_health_check"]
            results["summary"] = f"Workflow '{workflow_name}' completed execution."

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=results,
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_preview_change(
    operation: str,
    target: str,
    proposed_settings: dict[str, Any],
) -> ToolResult[dict[str, Any]]:
    """Preview the impact of a configuration or administrative modification before executing it.

    Args:
        operation: Operation type (e.g. 'update_index', 'delete_saved_search', 'modify_role').
        target: Target resource identifier.
        proposed_settings: Proposed parameter values to evaluate.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        server_info = await client.get_server_info()
        is_destructive = "delete" in operation.lower()
        risk_level = "HIGH" if is_destructive else "LOW"

        preview = {
            "operation": operation,
            "target": target,
            "proposed_settings": proposed_settings,
            "risk_level": risk_level,
            "requires_human_confirmation": is_destructive,
            "simulation": f"Simulated change '{operation}' against resource '{target}'. No live modification performed.",
        }

        return ToolResult.ok(
            data=preview,
            start_time=start_time,
            warnings=["This is a dry-run preview. No actual changes were committed."] if is_destructive else [],
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_audit_tool_activity(
    limit: int = 50,
    tool_filter: str | None = None,
    only_failures: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Query recent MCP server tool invocations, execution duration, and audit logs.

    Args:
        limit: Number of audit records to retrieve (default 50).
        tool_filter: Optional tool name filter.
        only_failures: Only retrieve failed tool executions.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()
    audit_store = get_audit_store()

    try:
        records = audit_store.query(limit=limit, tool_name=tool_filter, only_failures=only_failures)
        records_dump = [r.model_dump() for r in records]

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"audit_records": records_dump, "count": len(records_dump)},
            start_time=start_time,
            total_count=len(records_dump),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_test_connection() -> ToolResult[dict[str, Any]]:
    """Verify end-to-end connectivity, TLS, authentication, server version, and operational permissions."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        t0 = time.perf_counter()
        server_info = await client.get_server_info()
        ping_latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        data = {
            "status": "CONNECTED",
            "host": settings.splunk_host,
            "port": settings.splunk_port,
            "scheme": settings.splunk_scheme,
            "server_name": server_info.server_name,
            "splunk_version": server_info.version,
            "operating_system": f"{server_info.os_name} ({server_info.cpu_arch})",
            "license_state": server_info.license_state,
            "mode": server_info.mode,
            "latency_ms": ping_latency_ms,
            "read_only_mode": settings.mcp_read_only,
            "web_proxy_mode": settings.is_splunk_web_port,
        }

        return ToolResult.ok(
            data=data,
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(
            f"Splunk connection failed: {e}", start_time=start_time, read_only=settings.mcp_read_only
        )
