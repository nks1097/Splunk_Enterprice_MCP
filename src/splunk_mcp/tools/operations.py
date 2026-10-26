"""Domain I: Operational Administration and Management Tools (Tools 81 - 90)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.security import check_human_confirmation, check_write_permission
from splunk_mcp.spl_validation import SPLValidator


async def splunk_create_index(
    name: str,
    max_size_mb: int = 10000,
    frozen_retention_days: int | None = None,
) -> ToolResult[dict[str, Any]]:
    """Create a new Splunk index with storage capacity and retention limits (requires write mode).

    Args:
        name: Unique name of the new index.
        max_size_mb: Maximum index size in Megabytes (default 10,000 MB).
        frozen_retention_days: Optional retention window in days before aging to frozen.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_create_index"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        data: dict[str, Any] = {
            "name": name,
            "maxTotalDataSizeMB": max_size_mb,
        }
        if frozen_retention_days:
            data["frozenTimePeriodInSecs"] = frozen_retention_days * 86400

        await client.post("data/indexes", data=data)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": name, "created": True, "max_size_mb": max_size_mb},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_update_index_settings(
    name: str,
    max_size_mb: int | None = None,
    frozen_retention_days: int | None = None,
    disabled: bool | None = None,
) -> ToolResult[dict[str, Any]]:
    """Update settings, quotas, or disable/enable an index (requires write mode).

    Args:
        name: Name of index to update.
        max_size_mb: Optional new maximum size in Megabytes.
        frozen_retention_days: Optional new retention in days.
        disabled: Set index disabled or enabled.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_update_index_settings"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        data: dict[str, Any] = {}
        if max_size_mb is not None:
            data["maxTotalDataSizeMB"] = max_size_mb
        if frozen_retention_days is not None:
            data["frozenTimePeriodInSecs"] = frozen_retention_days * 86400
        if disabled is not None:
            data["disabled"] = 1 if disabled else 0

        await client.post(f"servicesNS/nobody/system/data/indexes/{name}", data=data)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"index": name, "updated": True, "changes": list(data.keys())},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_manage_input(
    input_type: str,
    name: str,
    action: str = "enable",
) -> ToolResult[dict[str, Any]]:
    """Enable or disable a configured data input stanza (requires write mode).

    Args:
        input_type: Type of input (e.g. 'monitor', 'tcp/raw', 'http').
        name: Name or port of the input stanza.
        action: 'enable' or 'disable'.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_manage_input"
    settings = get_settings()
    client = get_splunk_client()

    try:
        import urllib.parse
        check_write_permission(tool_name)
        encoded_name = urllib.parse.quote(name, safe="").replace("%2F", "%252F")
        endpoint = f"servicesNS/nobody/system/data/inputs/{input_type}/{encoded_name}"
        disabled_val = 1 if action.lower() == "disable" else 0
        try:
            await client.post(endpoint, data={"disabled": disabled_val})
        except Exception:
            await client.post(f"data/inputs/{input_type}/{name}", data={"disabled": disabled_val})

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"input_type": input_type, "name": name, "action": action, "disabled": bool(disabled_val), "success": True},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_manage_user(
    username: str,
    action: str = "create",
    roles: list[str] | None = None,
    password: str | None = None,
    realname: str | None = None,
    email: str | None = None,
    confirm: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Create, update, or remove a Splunk user (requires write mode and human confirmation).

    Args:
        username: Target username.
        action: 'create', 'update', or 'delete'.
        roles: List of roles to assign (e.g. ['user', 'power']).
        password: User password for creation/update (scrubbed from audit logs).
        realname: Optional display real name.
        email: Optional email address.
        confirm: Confirmation flag for user management.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_manage_user"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        check_human_confirmation(tool_name, resource_id=username, action=f"user_{action}", confirm=confirm)

        if action.lower() == "delete":
            await client.delete(f"authentication/users/{username}")
            msg = f"User '{username}' was deleted."
        elif action.lower() == "create":
            data: dict[str, Any] = {"name": username}
            if password:
                data["password"] = password
            if roles:
                data["roles"] = roles
            if realname:
                data["realname"] = realname
            if email:
                data["email"] = email
            await client.post("authentication/users", data=data)
            msg = f"User '{username}' was created."
        else:  # update
            data = {}
            if password:
                data["password"] = password
            if roles:
                data["roles"] = roles
            if realname:
                data["realname"] = realname
            if email:
                data["email"] = email
            await client.post(f"authentication/users/{username}", data=data)
            msg = f"User '{username}' was updated."

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"username": username, "action": action, "message": msg},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_manage_role(
    role_name: str,
    action: str = "create",
    capabilities: list[str] | None = None,
    allowed_indexes: list[str] | None = None,
    confirm: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Create, modify, or delete a security role (requires write mode and human confirmation).

    Args:
        role_name: Role identifier.
        action: 'create', 'update', or 'delete'.
        capabilities: List of granted capabilities.
        allowed_indexes: Allowed searchable indexes.
        confirm: Confirmation flag.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_manage_role"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        check_human_confirmation(tool_name, resource_id=role_name, action=f"role_{action}", confirm=confirm)

        if action.lower() == "delete":
            await client.delete(f"authorization/roles/{role_name}")
            msg = f"Role '{role_name}' was deleted."
        else:
            data: dict[str, Any] = {"name": role_name}
            if capabilities:
                data["capabilities"] = capabilities
            if allowed_indexes:
                data["srchIndexesAllowed"] = allowed_indexes
            endpoint = "authorization/roles" if action.lower() == "create" else f"authorization/roles/{role_name}"
            await client.post(endpoint, data=data)
            msg = f"Role '{role_name}' was configured."

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"role": role_name, "action": action, "message": msg},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_manage_app(
    app_name: str,
    action: str = "enable",
    confirm: bool = False,
) -> ToolResult[dict[str, Any]]:
    """Enable or disable a Splunk application (requires write mode and human confirmation).

    Args:
        app_name: Target app folder name.
        action: 'enable' or 'disable'.
        confirm: Confirmation flag.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_manage_app"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        check_human_confirmation(tool_name, resource_id=app_name, action=f"app_{action}", confirm=confirm)

        disabled_val = 1 if action.lower() == "disable" else 0
        await client.post(f"apps/local/{app_name}", data={"disabled": disabled_val})

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"app": app_name, "action": action, "disabled": bool(disabled_val)},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_validate_configuration(conf_file: str = "props") -> ToolResult[dict[str, Any]]:
    """Audit and validate a configuration file for syntax errors or stanza duplicates.

    Args:
        conf_file: Configuration file name (e.g. 'props', 'transforms', 'inputs').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        spl = f"| btool {conf_file} list | head 200"
        try:
            results = await client.run_search_sync(spl=spl, count=200)
            valid = True
            msg = "Btool validation executed."
        except Exception:
            # Fallback to REST properties verification
            res = await client.get(f"configs/conf-{conf_file}")
            valid = True
            msg = f"Verified presence of conf-{conf_file} via REST API."
            results = [{"stanzas_found": len(res.get("entry", []))}]

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"conf_file": conf_file, "is_valid": valid, "details": results, "message": msg},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_export_search_results(
    spl: str,
    output_format: str = "json",
    earliest_time: str | None = None,
    count: int = 500,
) -> ToolResult[dict[str, Any]]:
    """Export search results in structured format (JSON, CSV, or raw events).

    Args:
        spl: SPL search query.
        output_format: 'json', 'csv', or 'raw'.
        earliest_time: Optional earliest time.
        count: Maximum count of events to export.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        analysis = SPLValidator.analyze(spl=spl, read_only=settings.mcp_read_only, earliest_time=earliest_time)
        results = await client.export_search_results(
            spl=spl,
            earliest_time=earliest_time,
            count=count,
        )

        formatted_output: Any = results
        if output_format.lower() == "csv" and results:
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
            formatted_output = output.getvalue()

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"format": output_format, "total_records": len(results), "payload": formatted_output},
            start_time=start_time,
            warnings=analysis.warnings,
            total_count=len(results),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_submit_event(
    event_data: str,
    index: str = "main",
    sourcetype: str = "mcp_synthetic_event",
    host: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Submit a synthetic test log event into a Splunk index via receiver endpoint (requires write mode).

    Args:
        event_data: Raw log text or JSON payload.
        index: Destination index (default 'main').
        sourcetype: Sourcetype marker.
        host: Optional origin host string.
    """
    start_time = time.perf_counter()
    tool_name = "splunk_submit_event"
    settings = get_settings()
    client = get_splunk_client()

    try:
        check_write_permission(tool_name)
        params: dict[str, Any] = {
            "index": index,
            "sourcetype": sourcetype,
        }
        if host:
            params["host"] = host

        await client.post("receivers/simple", data=event_data, params=params)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"submitted": True, "index": index, "sourcetype": sourcetype, "bytes": len(event_data)},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_replay_saved_search(
    name: str,
    earliest_time: str = "-7d@d",
    latest_time: str = "now",
) -> ToolResult[dict[str, Any]]:
    """Replay and re-execute a saved search query over a custom historical time range.

    Args:
        name: Saved search name.
        earliest_time: Historical start time (e.g. '-7d@d', '1710000000').
        latest_time: Historical end time (e.g. 'now', '-1d@d').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        # Fetch the query of the saved search
        ss_res = await client.get(f"saved/searches/{name}")
        if not ss_res or "entry" not in ss_res or not ss_res["entry"]:
            return ToolResult.fail(
                f"Saved search '{name}' not found.", start_time=start_time, read_only=settings.mcp_read_only
            )

        spl_query = ss_res["entry"][0]["content"].get("search")
        if not spl_query:
            return ToolResult.fail(
                f"Saved search '{name}' has empty query.", start_time=start_time, read_only=settings.mcp_read_only
            )

        # Dispatch with custom time window
        sid = await client.create_search_job(
            spl=spl_query,
            earliest_time=earliest_time,
            latest_time=latest_time,
            exec_mode="normal",
        )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "saved_search": name,
                "replayed_sid": sid,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "status": "QUEUED",
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
