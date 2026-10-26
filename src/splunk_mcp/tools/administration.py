"""Domain E: Administration and Configuration Tools (Tools 41 - 50)."""

from __future__ import annotations

import time
from typing import Any

from splunk_mcp.client import get_splunk_client
from splunk_mcp.config import get_settings
from splunk_mcp.models import ToolResult
from splunk_mcp.pagination import extract_entry_content
from splunk_mcp.security import redact_secrets


async def splunk_get_server_info() -> ToolResult[dict[str, Any]]:
    """Retrieve Splunk server runtime info, version, OS, license state, and topology roles."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        info = await client.get_server_info()
        return ToolResult.ok(
            data=info.model_dump(),
            start_time=start_time,
            server_version=info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_server_health() -> ToolResult[dict[str, Any]]:
    """Retrieve Splunk system health report, status features, and subsystem warnings."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("server/health/splunkd")
        features = {}
        health_status = "GREEN"

        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                name = item.get("name")
                c = item.get("content", {})
                features[name] = {
                    "health": c.get("health", "GREEN"),
                    "reasons": c.get("reasons", []),
                    "disabled": c.get("disabled", False),
                }
                if c.get("health") == "RED":
                    health_status = "RED"
                elif c.get("health") == "YELLOW" and health_status != "RED":
                    health_status = "YELLOW"

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"overall_health": health_status, "features": features},
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_apps(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List installed Splunk apps and add-ons with versions and status."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("apps/local", params={"count": count})
        apps = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                apps.append(
                    {
                        "name": item.get("name"),
                        "label": c.get("label"),
                        "version": c.get("version"),
                        "author": c.get("author"),
                        "disabled": c.get("disabled", False),
                        "visible": c.get("visible", True),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"apps": apps, "count": len(apps)},
            start_time=start_time,
            total_count=len(apps),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_app_details(name: str) -> ToolResult[dict[str, Any]]:
    """Get metadata, configurations, and permissions for a specific Splunk app.

    Args:
        name: App folder name (e.g. 'search', 'SplunkForwarder').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get(f"apps/local/{name}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            return ToolResult.fail(f"App '{name}' not found.", start_time=start_time, read_only=settings.mcp_read_only)

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


async def splunk_list_users(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List configured user accounts, roles, realnames, and authentication types with secrets redacted."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("authentication/users", params={"count": count})
        users = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                users.append(
                    {
                        "username": item.get("name"),
                        "realname": c.get("realname"),
                        "email": c.get("email"),
                        "roles": c.get("roles", []),
                        "type": c.get("type"),
                        "locked_out": c.get("locked-out", False),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"users": users, "count": len(users)},
            start_time=start_time,
            total_count=len(users),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_user(username: str) -> ToolResult[dict[str, Any]]:
    """Get details, assigned roles, and permissions of a specific user.

    Args:
        username: Username to inspect.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get(f"authentication/users/{username}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            return ToolResult.fail(
                f"User '{username}' not found.", start_time=start_time, read_only=settings.mcp_read_only
            )

        content = extract_entry_content(res["entry"][0])
        content_scrubbed = redact_secrets(content)
        server_info = await client.get_server_info()
        return ToolResult.ok(
            data=content_scrubbed,
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_roles(count: int = 100) -> ToolResult[dict[str, Any]]:
    """List configured roles, inherited roles, and allowed search indexes."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("authorization/roles", params={"count": count})
        roles = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                c = item.get("content", {})
                roles.append(
                    {
                        "name": item.get("name"),
                        "imported_roles": c.get("imported_roles", []),
                        "srchIndexesAllowed": c.get("srchIndexesAllowed", []),
                        "srchIndexesDefault": c.get("srchIndexesDefault", []),
                        "srchJobsQuota": c.get("srchJobsQuota"),
                    }
                )

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"roles": roles, "count": len(roles)},
            start_time=start_time,
            total_count=len(roles),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_role_capabilities(role_name: str) -> ToolResult[dict[str, Any]]:
    """Get granular capabilities and restrictions assigned to a specific role.

    Args:
        role_name: Name of the role (e.g. 'admin', 'user', 'power').
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get(f"authorization/roles/{role_name}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            return ToolResult.fail(
                f"Role '{role_name}' not found.", start_time=start_time, read_only=settings.mcp_read_only
            )

        content = res["entry"][0].get("content", {})
        caps = content.get("capabilities", [])
        imported_caps = content.get("imported_capabilities", [])

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={
                "role": role_name,
                "capabilities": caps,
                "imported_capabilities": imported_caps,
                "total_capabilities": len(set(caps + imported_caps)),
            },
            start_time=start_time,
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_list_configurations() -> ToolResult[dict[str, Any]]:
    """List available .conf configuration files accessible through REST properties."""
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        res = await client.get("properties")
        confs = []
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                confs.append(item.get("name"))

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"configurations": sorted(confs), "count": len(confs)},
            start_time=start_time,
            total_count=len(confs),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)


async def splunk_get_configuration(
    conf_file: str,
    stanza: str | None = None,
) -> ToolResult[dict[str, Any]]:
    """Read stanzas and properties from a configuration file with secrets scrubbed.

    Args:
        conf_file: Name of conf file (e.g. 'server', 'props', 'transforms', 'inputs').
        stanza: Optional specific stanza name.
    """
    start_time = time.perf_counter()
    settings = get_settings()
    client = get_splunk_client()

    try:
        endpoint = f"configs/conf-{conf_file}"
        if stanza:
            endpoint = f"{endpoint}/{stanza}"

        res = await client.get(endpoint)
        stanzas = {}
        if isinstance(res, dict) and "entry" in res:
            for item in res["entry"]:
                name = item.get("name")
                c = item.get("content", {})
                stanzas[name] = redact_secrets(c)

        server_info = await client.get_server_info()
        return ToolResult.ok(
            data={"conf_file": conf_file, "stanzas": stanzas, "count": len(stanzas)},
            start_time=start_time,
            total_count=len(stanzas),
            server_version=server_info.version,
            read_only=settings.mcp_read_only,
        )
    except Exception as e:
        return ToolResult.fail(str(e), start_time=start_time, read_only=settings.mcp_read_only)
