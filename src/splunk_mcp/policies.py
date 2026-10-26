"""Policy evaluation and permission mapping for Splunk MCP tools."""

from __future__ import annotations

from enum import Enum


class ToolCategory(str, Enum):
    """Categorization of MCP tools for access control and governance."""

    SEARCH = "search"
    DISCOVERY = "discovery"
    READ = "read"
    INVESTIGATION = "investigation"
    PERFORMANCE = "performance"
    WRITE = "write"
    ADMIN = "admin"
    DESTRUCTIVE = "destructive"


# Mapping of tools requiring WRITE permission (blocked when MCP_READ_ONLY=True)
WRITE_TOOLS: set[str] = {
    "splunk_create_saved_search",
    "splunk_update_saved_search",
    "splunk_delete_saved_search",
    "splunk_acknowledge_alert",
    "splunk_manage_alert_suppression",
    "splunk_create_dashboard",
    "splunk_update_dashboard",
    "splunk_delete_dashboard",
    "splunk_create_index",
    "splunk_update_index_settings",
    "splunk_manage_input",
    "splunk_manage_user",
    "splunk_manage_role",
    "splunk_manage_app",
    "splunk_submit_event",
    "splunk_search_cancel",
}

# Mapping of tools considered DESTRUCTIVE requiring explicit human confirmation
DESTRUCTIVE_TOOLS: set[str] = {
    "splunk_delete_saved_search",
    "splunk_delete_dashboard",
    "splunk_manage_user",
    "splunk_manage_role",
    "splunk_manage_app",
    "splunk_search_cancel",
}


def is_write_tool(tool_name: str) -> bool:
    """Check if a tool performs write or mutation actions."""
    return tool_name in WRITE_TOOLS


def is_destructive_tool(tool_name: str) -> bool:
    """Check if a tool performs destructive actions."""
    return tool_name in DESTRUCTIVE_TOOLS
