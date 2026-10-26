"""Exception hierarchy for Splunk MCP Server."""


class SplunkMCPError(Exception):
    """Base exception for all Splunk MCP errors."""

    def __init__(self, message: str, status_code: int | None = None, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(SplunkMCPError):
    """Raised when authentication credentials or token are invalid or expired (HTTP 401)."""

    def __init__(
        self, message: str = "Splunk authentication failed. Check credentials or token.", details: dict | None = None
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(SplunkMCPError):
    """Raised when the user lacks required Splunk permissions or role capabilities (HTTP 403)."""

    def __init__(
        self,
        message: str = "Access forbidden. User lacks required permissions or role capabilities.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundError(SplunkMCPError):
    """Raised when a requested resource (index, job, user, dashboard) does not exist (HTTP 404)."""

    def __init__(
        self, message: str = "The requested Splunk resource was not found.", details: dict | None = None
    ) -> None:
        super().__init__(message, status_code=404, details=details)


class ReadOnlyError(SplunkMCPError):
    """Raised when an operation would modify state while MCP is operating in read-only mode."""

    def __init__(
        self,
        tool_name: str,
        message: str | None = None,
    ) -> None:
        msg = message or (
            f"Operation '{tool_name}' blocked: Splunk MCP is running in READ-ONLY mode. "
            "To permit administrative and modification actions, set MCP_READ_ONLY=false in the environment."
        )
        super().__init__(msg, status_code=403, details={"tool": tool_name, "mode": "read_only"})


class ConfirmationRequiredError(SplunkMCPError):
    """Raised when a destructive or high-impact operation requires explicit human confirmation."""

    def __init__(self, tool_name: str, resource_id: str, action: str) -> None:
        msg = (
            f"Operation '{tool_name}' on '{resource_id}' is destructive ({action}) and requires human confirmation. "
            "Please review the planned change and re-run with confirm=True to proceed."
        )
        super().__init__(
            msg,
            status_code=400,
            details={"tool": tool_name, "resource": resource_id, "action": action, "require_confirmation": True},
        )


class SPLValidationError(SplunkMCPError):
    """Raised when an SPL query violates security policies or syntax safety checks."""

    def __init__(self, reason: str, query: str | None = None) -> None:
        msg = f"SPL Validation Error: {reason}"
        super().__init__(msg, status_code=400, details={"reason": reason, "query": query})


class ConnectionError(SplunkMCPError):
    """Raised when communication with Splunk host fails due to network or TLS errors."""

    def __init__(self, message: str, host: str | None = None) -> None:
        super().__init__(message, status_code=503, details={"host": host})


class RateLimitError(SplunkMCPError):
    """Raised when Splunk search quota or concurrency limit is reached (HTTP 429)."""

    def __init__(self, message: str = "Search concurrency or quota limit exceeded.") -> None:
        super().__init__(message, status_code=429)


class ServerError(SplunkMCPError):
    """Raised when Splunk returns an internal server error (HTTP 5xx)."""

    def __init__(self, message: str, status_code: int = 500, details: dict | None = None) -> None:
        super().__init__(message, status_code=status_code, details=details)
