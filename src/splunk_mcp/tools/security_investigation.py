"""Domain G: Security, SIEM, and Forensic Investigation Tools (Tools 61 - 70)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.security import escape_spl_value, wrap_untrusted_content


async def splunk_detect_failed_logins(
    index: str | None = None,
    earliest_time: str = "-24h@h",
    count: int = 50,
) -> ToolResult[dict[str, Any]]:
    """Detect and aggregate failed authentication events across Splunk audit, Windows, and Linux logs.

    Args:
        index: Optional specific index (defaults to searching _audit and default indexes).
        earliest_time: Earliest search window (default '-24h@h').
        count: Maximum aggregated rows to return.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        idx_clause = (
            f'index="{escape_spl_value(index)}"'
            if index
            else "(index=_audit action=login_failed) OR (action=failure OR action=failed EventCode=4625)"
        )
        spl = (
            f"search {idx_clause} earliest={earliest_time} "
            f"| stats count by user src action "
            f"| sort - count | head {count}"
        )
        results = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"failed_logins": results, "total_unique_combinations": len(results)},
            start_time=start_time,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_detect_brute_force(
    threshold: int = 5,
    time_window: str = "15m",
    earliest_time: str = "-4h",
) -> ToolResult[dict[str, Any]]:
    """Detect potential brute force attacks or credential stuffing based on repeated failed logins.

    Args:
        threshold: Minimum failed attempts to flag (default 5).
        time_window: Bin duration (default '15m').
        earliest_time: Time range to analyze (default '-4h').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = (
            f"search (index=_audit action=login_failed) OR (action=failure EventCode=4625) earliest={earliest_time} "
            f"| bin _time span={time_window} "
            f"| stats count by _time src user "
            f"| where count >= {threshold} "
            f'| eval time_period=strftime(_time, "%Y-%m-%d %H:%M:%S") '
            f"| sort - count"
        )
        results = await client.run_search_sync(spl=spl, count=100)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"threshold": threshold, "brute_force_suspects": results, "count": len(results)},
            start_time=start_time,
            warnings=[f"Detected {len(results)} potential brute-force authentication spikes."] if results else [],
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_investigate_ip(
    ip_address: str,
    earliest_time: str = "-24h@h",
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Forensic investigation of an IP address across firewall, proxy, authentication, and web logs.

    Args:
        ip_address: Target IP address to investigate.
        earliest_time: Time window to scan (default '-24h@h').
        count: Maximum events to return.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sanitized_ip = escape_spl_value(ip_address)
        spl = (
            f'search "{sanitized_ip}" earliest={earliest_time} '
            f"| stats count by sourcetype index action "
            f"| sort - count | head {count}"
        )
        activity_summary = await client.run_search_sync(spl=spl, count=count)

        raw_sample_spl = f'search "{sanitized_ip}" earliest={earliest_time} | head 10'
        raw_events = await client.run_search_sync(spl=raw_sample_spl, count=10)

        wrapped = wrap_untrusted_content(raw_events)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "ip_address": ip_address,
                "activity_by_sourcetype": activity_summary,
                "sample_events": wrapped,
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_investigate_user(
    username: str,
    earliest_time: str = "-24h@h",
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Audit user actions, accessed resources, IP origins, and privilege usage.

    Args:
        username: Target username.
        earliest_time: Time range to audit.
        count: Maximum results.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sanitized_user = escape_spl_value(username)
        # Search Splunk audit log and general logs for user activity
        spl = (
            f'search (index=_audit user="{sanitized_user}") OR (user="{sanitized_user}") earliest={earliest_time} '
            f"| stats count by action info clientip status "
            f"| sort - count | head {count}"
        )
        actions = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"username": username, "observed_actions": actions, "count": len(actions)},
            start_time=start_time,
            total_count=len(actions),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_investigate_host(
    hostname: str,
    earliest_time: str = "-24h@h",
    count: int = 100,
) -> ToolResult[dict[str, Any]]:
    """Investigate system logs, processes, network connections, and errors for a host.

    Args:
        hostname: Target host name or FQDN.
        earliest_time: Earliest search window.
        count: Maximum events.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sanitized_host = escape_spl_value(hostname)
        spl = (
            f'search host="{sanitized_host}" earliest={earliest_time} '
            f"| stats count by sourcetype log_level "
            f"| sort - count | head {count}"
        )
        sources = await client.run_search_sync(spl=spl, count=count)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"hostname": hostname, "host_breakdown": sources},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_search_ioc(
    ioc_value: str,
    ioc_type: str | None = None,
    earliest_time: str = "-7d@d",
) -> ToolResult[dict[str, Any]]:
    """Search for Indicators of Compromise (hashes, domains, IPs, URLs) across all indexed data.

    Args:
        ioc_value: The IOC string (e.g. SHA256 hash, malicious domain, external IP).
        ioc_type: Optional type description ('hash', 'ip', 'domain').
        earliest_time: Time range (default '-7d@d').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sanitized_ioc = escape_spl_value(ioc_value)
        spl = (
            f'search "{sanitized_ioc}" earliest={earliest_time} '
            f"| stats count by index sourcetype host "
            f"| sort - count | head 50"
        )
        matches = await client.run_search_sync(spl=spl, count=50)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "ioc": ioc_value,
                "ioc_type": ioc_type or "generic",
                "matched": len(matches) > 0,
                "detections": matches,
            },
            start_time=start_time,
            warnings=[f"IOC match found in {len(matches)} distinct telemetry sources!"] if matches else [],
            total_count=len(matches),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_correlate_events(
    entity_value: str,
    window_minutes: int = 30,
    timestamp: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Correlate multi-source events occurring within a synchronized time window around an entity.

    Args:
        entity_value: Target identifier (e.g. IP, username, hostname).
        window_minutes: Time window in minutes before and after timestamp.
        timestamp: Anchor epoch or ISO timestamp (default current time).
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sanitized_entity = escape_spl_value(entity_value)
        earliest = f"-{window_minutes}m"
        latest = f"+{window_minutes}m"

        spl = (
            f'search "{sanitized_entity}" earliest={earliest} latest={latest} '
            f'| eval event_time=strftime(_time, "%Y-%m-%d %H:%M:%S") '
            f"| fields event_time index sourcetype host _raw | sort _time | head 100"
        )
        correlated = await client.run_search_sync(spl=spl, count=100)
        wrapped = wrap_untrusted_content(correlated)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"entity": entity_value, "window_minutes": window_minutes, "correlated_events": wrapped},
            start_time=start_time,
            total_count=len(correlated),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_detect_anomalies(
    index: str,
    sourcetype: str | None = None,
    field_to_analyze: str = "count",
    time_span: str = "1h",
) -> ToolResult[dict[str, Any]]:
    """Execute statistical anomaly detection (outliers based on standard deviation) over time series.

    Args:
        index: Index to inspect.
        sourcetype: Optional sourcetype.
        field_to_analyze: Metric or field (default 'count').
        time_span: Aggregation bucket (default '1h').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        st_filter = f'sourcetype="{escape_spl_value(sourcetype)}"' if sourcetype else ""
        spl = (
            f'search index="{escape_spl_value(index)}" {st_filter} earliest=-7d '
            f"| timechart span={time_span} count as event_count "
            f"| anomalydetection event_count action=annotate "
            f'| where isanomaly="true"'
        )
        results = await client.run_search_sync(spl=spl, count=50)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": index, "anomalies_detected": len(results), "anomaly_records": results},
            start_time=start_time,
            warnings=[f"Detected {len(results)} statistical anomalies."] if results else [],
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_security_alerts(
    severity: str | None = None,
    earliest_time: str = "-24h@h",
    count: int = 50,
) -> ToolResult[dict[str, Any]]:
    """Query security alerts, high-severity trigger events, and findings.

    Args:
        severity: Optional severity filter ('critical', 'high', 'medium').
        earliest_time: Time window (default '-24h@h').
        count: Maximum alert items.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("alerts/fired_alerts", params={"count": count})
        alerts = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                alerts.append(
                    {
                        "name": item.get("name"),
                        "severity": c.get("severity"),
                        "trigger_time": item.get("published"),
                        "digest": c.get("digest"),
                    }
                )

        if severity:
            alerts = [a for a in alerts if str(a.get("severity")).lower() == severity.lower()]

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"alerts": alerts, "count": len(alerts)},
            start_time=start_time,
            total_count=len(alerts),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_build_incident_timeline(
    entity_type: str,
    entity_value: str,
    earliest_time: str = "-12h",
    latest_time: str = "now",
    max_events: int = 50,
) -> ToolResult[dict[str, Any]]:
    """Composite tool: construct a high-fidelity chronological timeline for an incident entity.

    Args:
        entity_type: Type of entity ('ip', 'user', or 'host').
        entity_value: The entity string (e.g. '10.0.0.5', 'jsmith', 'srv-db-01').
        earliest_time: Incident timeline start.
        latest_time: Incident timeline end.
        max_events: Maximum chronological timeline events.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        sanitized = escape_spl_value(entity_value)
        field_name = "src" if entity_type == "ip" else ("user" if entity_type == "user" else "host")

        spl = (
            f'search ({field_name}="{sanitized}" OR "{sanitized}") earliest={earliest_time} latest={latest_time} '
            f'| eval timestamp=strftime(_time, "%Y-%m-%d %H:%M:%S") '
            f"| fields timestamp index sourcetype host user action _raw "
            f"| sort _time | head {max_events}"
        )
        timeline_events = await client.run_search_sync(spl=spl, count=max_events)
        wrapped = wrap_untrusted_content(timeline_events)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "entity_type": entity_type,
                "entity_value": entity_value,
                "time_range": f"{earliest_time} to {latest_time}",
                "total_events": len(timeline_events),
                "timeline": wrapped,
            },
            start_time=start_time,
            total_count=len(timeline_events),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
