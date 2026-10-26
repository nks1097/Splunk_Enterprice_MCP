"""Pagination utilities for Splunk REST API and MCP responses."""

from typing import Any


def paginate_list(
    items: list[Any],
    offset: int = 0,
    count: int = 100,
) -> tuple[list[Any], bool, int | None]:
    """Paginate an in-memory list of items.

    Returns:
        (paginated_items, is_truncated, next_offset)
    """
    total = len(items)
    if offset >= total:
        return [], False, None

    end = offset + count
    slice_items = items[offset:end]
    has_more = end < total
    next_offset = end if has_more else None

    return slice_items, has_more, next_offset


def extract_entry_content(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract flattened dictionary combining name, title, and content from Splunk REST entry."""
    data = {}
    if "name" in entry:
        data["name"] = entry["name"]
    if "id" in entry:
        data["id"] = entry["id"]
    if "updated" in entry:
        data["updated"] = entry["updated"]

    content = entry.get("content", {})
    if isinstance(content, dict):
        data.update(content)

    acl = entry.get("acl", {})
    if isinstance(acl, dict):
        data["app"] = acl.get("app")
        data["owner"] = acl.get("owner")
        data["sharing"] = acl.get("sharing")

    return data
