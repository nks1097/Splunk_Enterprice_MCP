"""Structured audit logging and correlation ID tracking for Splunk MCP."""

from __future__ import annotations

import logging
import sys
import time
from collections import deque
from typing import Any

from pydantic import BaseModel, Field

from splunk_mcp.security import redact_secrets

# Configure logger specifically writing to stderr so STDIO JSON-RPC on stdout is never corrupted
logger = logging.getLogger("splunk_mcp.audit")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class AuditRecord(BaseModel):
    """Immutable audit record representing a single tool invocation."""

    request_id: str = Field(description="Unique correlation ID")
    timestamp: float = Field(default_factory=time.time, description="Invocation epoch timestamp")
    tool_name: str = Field(description="Name of the MCP tool called")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Sanitized arguments passed to tool")
    success: bool = Field(default=True, description="Whether tool execution succeeded")
    error: str | None = Field(default=None, description="Sanitized error description if failed")
    duration_ms: float = Field(default=0.0, description="Duration of tool execution in milliseconds")


class AuditStore:
    """Thread-safe circular audit store keeping recent tool events for governance."""

    def __init__(self, capacity: int = 500) -> None:
        self._capacity = capacity
        self._records: deque[AuditRecord] = deque(maxlen=capacity)

    def record(
        self,
        request_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        success: bool,
        error: str | None = None,
        duration_ms: float = 0.0,
    ) -> AuditRecord:
        """Log and store an audit event."""
        sanitized_params = redact_secrets(parameters)
        sanitized_error = redact_secrets(error) if error else None

        entry = AuditRecord(
            request_id=request_id,
            tool_name=tool_name,
            parameters=sanitized_params,
            success=success,
            error=sanitized_error,
            duration_ms=round(duration_ms, 2),
        )
        self._records.append(entry)

        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"AUDIT req_id={request_id} tool={tool_name} success={success} duration={round(duration_ms, 2)}ms",
        )
        return entry

    def query(
        self,
        limit: int = 50,
        tool_name: str | None = None,
        only_failures: bool = False,
    ) -> list[AuditRecord]:
        """Query audit records filtered by criteria."""
        results = list(self._records)
        if tool_name:
            results = [r for r in results if r.tool_name.lower() == tool_name.lower()]
        if only_failures:
            results = [r for r in results if not r.success]
        return results[-limit:]


_audit_store = AuditStore()


def get_audit_store() -> AuditStore:
    """Get the global audit store instance."""
    return _audit_store
