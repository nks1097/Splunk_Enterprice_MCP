"""Production-ready asynchronous Splunk REST and Web API Client with dual-mode connectivity."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from splunk_mcp.config import Settings, get_settings
from splunk_mcp.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    SplunkMCPError,
)
from splunk_mcp.exceptions import (
    ConnectionError as SplunkConnectionError,
)
from splunk_mcp.models import SearchJobInfo, ServerInfo

logger = logging.getLogger("splunk_mcp.client")


class SplunkClient:
    """Enterprise asynchronous Splunk Client supporting direct REST API (8089) and Web Proxy (8000)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._session_key: str | None = None
        self._csrf_token: str | None = None
        self._cookies: dict[str, str] = {}
        self._cached_server_info: ServerInfo | None = None
        self._client: httpx.AsyncClient | None = None

    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or initialize reusable httpx AsyncClient."""
        if self._client is None or self._client.is_closed:
            verify: Any = self.settings.splunk_verify_tls
            if not self.settings.splunk_verify_tls:
                verify = False
            elif self.settings.splunk_ca_bundle:
                verify = self.settings.splunk_ca_bundle

            self._client = httpx.AsyncClient(
                verify=verify,
                timeout=httpx.Timeout(self.settings.splunk_timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close underlying HTTP client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> SplunkClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _build_url(self, endpoint: str) -> str:
        """Build request URL taking into account direct 8089 vs Web proxy on 8000."""
        endpoint_clean = endpoint.lstrip("/")
        if not endpoint_clean.startswith("services/"):
            endpoint_clean = f"services/{endpoint_clean}"

        if self.settings.is_splunk_web_port:
            return f"{self.settings.base_url}/en-US/splunkd/__raw/{endpoint_clean}"
        return f"{self.settings.base_url}/{endpoint_clean}"

    async def _authenticate_web(self, client: httpx.AsyncClient) -> None:
        """Authenticate with Splunk Web (port 8000) and acquire session key & CSRF token."""
        login_url = f"{self.settings.base_url}/en-US/account/login"
        try:
            get_res = await client.get(login_url)
            cval = get_res.cookies.get("cval")
            if not cval:
                # If cval cookie is not in response, try from client cookies
                cval = client.cookies.get("cval")

            username = self.settings.splunk_username or "admin"
            password = self.settings.splunk_password.get_secret_value() if self.settings.splunk_password else ""

            post_data = {
                "username": username,
                "password": password,
                "cval": cval or "",
                "return_to": "/en-US/app/launcher/home",
            }

            post_res = await client.post(
                login_url,
                data=post_data,
                headers={"Referer": login_url},
            )

            if post_res.status_code >= 400:
                raise AuthenticationError(f"Splunk Web login failed with status {post_res.status_code}")

            # Extract splunkd session key and csrf token from cookies
            for k, v in client.cookies.items():
                self._cookies[k] = v
                if k.startswith("splunkd_"):
                    self._session_key = v
                elif "csrf_token" in k or k == "cval":
                    self._csrf_token = v

            if not self._session_key and "splunkweb_uid" not in client.cookies:
                raise AuthenticationError("Splunk Web login succeeded but session cookies were not returned.")

            logger.info("Successfully established Splunk Web session.")
        except httpx.RequestError as e:
            raise SplunkConnectionError(f"Failed to connect to Splunk Web at {login_url}: {e}")

    def _get_auth_headers(self) -> dict[str, str]:
        """Construct authentication headers based on configuration or session state."""
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "Splunk-Enterprise-MCP-Server/1.0",
        }

        # Splunk Web proxy mode
        if self.settings.is_splunk_web_port:
            headers["X-Requested-With"] = "XMLHttpRequest"
            if self._csrf_token:
                headers["X-Splunk-Form-Key"] = self._csrf_token
            if self._session_key:
                headers["Authorization"] = f"Splunk {self._session_key}"
            return headers

        # Direct REST API mode (8089)
        if self.settings.splunk_token:
            token = self.settings.splunk_token.get_secret_value()
            headers["Authorization"] = f"Bearer {token}"
        elif self.settings.splunk_username and self.settings.splunk_password:
            import base64

            auth_str = f"{self.settings.splunk_username}:{self.settings.splunk_password.get_secret_value()}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        retries: int = 2,
    ) -> Any:
        """Execute an asynchronous authenticated HTTP request to Splunk REST API."""
        client = await self.get_http_client()

        # In web mode, ensure we have an active session
        if self.settings.is_splunk_web_port and not self._session_key:
            await self._authenticate_web(client)

        url = self._build_url(endpoint)
        query_params = dict(params or {})
        if "output_mode" not in query_params:
            query_params["output_mode"] = "json"

        headers = self._get_auth_headers()

        last_error = None
        for attempt in range(retries + 1):
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=query_params,
                    data=data,
                    headers=headers,
                )

                # If 401 on web mode, retry once with re-authentication
                if response.status_code == 401 and self.settings.is_splunk_web_port and attempt == 0:
                    logger.warning("Session expired or CSRF token invalid. Re-authenticating...")
                    await self._authenticate_web(client)
                    headers = self._get_auth_headers()
                    continue

                if response.status_code == 401:
                    raise AuthenticationError("Splunk credentials or Bearer token rejected (HTTP 401).")
                elif response.status_code == 403:
                    raise AuthorizationError(f"Access forbidden for '{endpoint}' (HTTP 403).")
                elif response.status_code == 404:
                    raise NotFoundError(f"Splunk resource '{endpoint}' not found (HTTP 404).")
                elif response.status_code == 429:
                    raise RateLimitError("Splunk search quota or rate limit exceeded.")
                elif response.status_code >= 500:
                    raise ServerError(
                        f"Splunk returned server error ({response.status_code}): {response.text[:200]}",
                        status_code=response.status_code,
                    )

                # Parse JSON if possible
                if "application/json" in response.headers.get("Content-Type", "") or "output_mode=json" in url:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return response.text

                return response.text

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise SplunkConnectionError(
                    f"Network error connecting to Splunk at {url}: {e}", host=self.settings.splunk_host
                )
            except SplunkMCPError:
                raise
            except Exception as e:
                raise SplunkMCPError(f"Unexpected error communicating with Splunk: {e}")

        if last_error:
            raise SplunkConnectionError(f"Failed after {retries} retries: {last_error}")

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Send GET request to Splunk REST endpoint."""
        return await self.request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send POST request to Splunk REST endpoint."""
        return await self.request("POST", endpoint, params=params, data=data)

    async def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Send DELETE request to Splunk REST endpoint."""
        return await self.request("DELETE", endpoint, params=params)

    # Search Execution API
    async def create_search_job(
        self,
        spl: str,
        earliest_time: str | None = None,
        latest_time: str | None = None,
        exec_mode: str = "blocking",
        max_count: int | None = None,
    ) -> str:
        """Dispatch a search query and return Job SID."""
        data: dict[str, Any] = {
            "search": spl,
            "exec_mode": exec_mode,
            "output_mode": "json",
        }
        if earliest_time:
            data["earliest_time"] = earliest_time
        if latest_time:
            data["latest_time"] = latest_time
        if max_count:
            data["max_count"] = max_count

        res = await self.post("search/jobs", data=data)
        if isinstance(res, dict) and "sid" in res:
            return res["sid"]
        raise SplunkMCPError("Failed to obtain search job SID from response.")

    async def get_job_status(self, sid: str) -> SearchJobInfo:
        """Fetch search job status and progress by SID."""
        res = await self.get(f"search/jobs/{sid}")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            raise NotFoundError(f"Search Job SID '{sid}' not found.")

        content = res["entry"][0]["content"]
        return SearchJobInfo(
            sid=sid,
            is_done=content.get("isDone", False),
            is_failed=content.get("isFailed", False),
            is_paused=content.get("isPaused", False),
            dispatch_state=content.get("dispatchState", "UNKNOWN"),
            done_progress=float(content.get("doneProgress", 0.0)),
            event_count=int(content.get("eventCount", 0)),
            result_count=int(content.get("resultCount", 0)),
            scan_count=int(content.get("scanCount", 0)),
            run_duration=float(content.get("runDuration", 0.0)),
            messages=res.get("messages", []),
        )

    async def get_job_results(
        self,
        sid: str,
        offset: int = 0,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve paginated results for a search job."""
        params = {"offset": offset, "count": count, "output_mode": "json"}
        res = await self.get(f"search/jobs/{sid}/results", params=params)
        if isinstance(res, dict):
            return res.get("results", [])
        return []

    async def get_job_events(
        self,
        sid: str,
        offset: int = 0,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve raw events associated with a search job."""
        params = {"offset": offset, "count": count, "output_mode": "json"}
        res = await self.get(f"search/jobs/{sid}/events", params=params)
        if isinstance(res, dict):
            return res.get("results", [])
        return []

    async def get_job_preview(self, sid: str, count: int = 50) -> list[dict[str, Any]]:
        """Retrieve preview results for a running search job."""
        params = {"count": count, "output_mode": "json"}
        res = await self.get(f"search/jobs/{sid}/results_preview", params=params)
        if isinstance(res, dict):
            return res.get("results", [])
        return []

    async def cancel_job(self, sid: str) -> bool:
        """Cancel an active search job."""
        data = {"action": "cancel"}
        await self.post(f"search/jobs/{sid}/control", data=data)
        return True

    async def run_search_sync(
        self,
        spl: str,
        earliest_time: str | None = None,
        latest_time: str | None = None,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Convenience method to execute a search and return its results."""
        sid = await self.create_search_job(
            spl=spl,
            earliest_time=earliest_time,
            latest_time=latest_time,
            exec_mode="blocking",
            max_count=count,
        )
        return await self.get_job_results(sid, offset=0, count=count)

    async def export_search_results(
        self,
        spl: str,
        earliest_time: str | None = None,
        latest_time: str | None = None,
        count: int = 1000,
    ) -> list[dict[str, Any]]:
        """Export search results directly via streaming export endpoint."""
        data: dict[str, Any] = {
            "search": spl,
            "output_mode": "json",
            "count": count,
        }
        if earliest_time:
            data["earliest_time"] = earliest_time
        if latest_time:
            data["latest_time"] = latest_time

        client = await self.get_http_client()
        url = self._build_url("search/jobs/export")
        headers = self._get_auth_headers()

        response = await client.post(url, data=data, headers=headers)
        lines = response.text.strip().split("\n")
        results = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                row = json.loads(line_str)
                if "result" in row:
                    results.append(row["result"])
                elif isinstance(row, dict) and "_raw" in row:
                    results.append(row)
            except json.JSONDecodeError:
                continue
        return results

    async def get_server_info(self) -> ServerInfo:
        """Fetch Splunk instance version, hostname, and operating state."""
        if self._cached_server_info:
            return self._cached_server_info

        res = await self.get("server/info")
        if not isinstance(res, dict) or "entry" not in res or not res["entry"]:
            raise SplunkMCPError("Unable to retrieve server info from Splunk.")

        content = res["entry"][0]["content"]
        info = ServerInfo(
            server_name=content.get("serverName", self.settings.splunk_host),
            version=content.get("version", "unknown"),
            build=content.get("build"),
            os_name=content.get("os_name"),
            cpu_arch=content.get("cpu_arch"),
            license_state=content.get("licenseState"),
            server_roles=content.get("server_roles", []),
            mode=content.get("mode"),
        )
        self._cached_server_info = info
        return info


_default_client: SplunkClient | None = None


def get_splunk_client() -> SplunkClient:
    """Get or create singleton Splunk Client instance."""
    global _default_client
    if _default_client is None:
        _default_client = SplunkClient()
    return _default_client


def set_splunk_client(client: SplunkClient) -> None:
    """Override singleton client (for testing)."""
    global _default_client
    _default_client = client
