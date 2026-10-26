#!/usr/bin/env python3
"""
Splunk Enterprise MCP Server - Native STDIO Bridge for Antigravity IDE / Claude.
Fully supports 'server/discover', 'initialize', 'tools/list', 'tools/call', and 'ping'.
Maintains clean stdio transport by isolating logs to stderr file.
"""

import asyncio
import inspect
import json
import os
import sys
from pathlib import Path

# Force UTF-8 encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

# Resolve directories
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

os.chdir(BASE_DIR)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load .env explicitly
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env", override=True)
except Exception:
    pass

# Redirect stderr to log file for clean JSON-RPC stdio
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
sys.stderr = open(LOG_DIR / "splunk_bridge.log", "a", encoding="utf-8")

# Import Splunk tools
from splunk_mcp.tools import ALL_TOOLS
from splunk_mcp.config import get_settings

SETTINGS = get_settings()
TOOL_MAP = {fn.__name__: fn for fn in ALL_TOOLS}

# Cache JSON schemas for all tools
SCHEMAS_DIR = Path.home() / ".gemini" / "antigravity-ide" / "mcp" / "splunk"


def get_tool_schema(tool_name: str) -> dict:
    """Retrieve parameter schema for tool from cache or inspect signature."""
    schema_file = SCHEMAS_DIR / f"{tool_name}.json"
    if schema_file.exists():
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("parameters", {"type": "object", "properties": {}})
        except Exception:
            pass
    return {"type": "object", "properties": {}}


def build_tools_list() -> list:
    """Return all 100 tools in standard MCP JSON-RPC format."""
    tools = []
    for fn in ALL_TOOLS:
        name = fn.__name__
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        schema = get_tool_schema(name)
        tools.append({
            "name": name,
            "description": doc,
            "inputSchema": schema,
        })
    return tools


def write_response(payload: dict) -> None:
    """Send newline-delimited JSON-RPC response to stdout."""
    line = json.dumps(payload, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


async def execute_tool_async(tool_name: str, arguments: dict) -> dict:
    """Execute target Splunk tool asynchronously."""
    handler = TOOL_MAP.get(tool_name)
    if not handler:
        return {
            "content": [{"type": "text", "text": f"Tool '{tool_name}' not found."}],
            "isError": True,
        }

    try:
        if inspect.iscoroutinefunction(handler):
            result = await handler(**arguments)
        else:
            result = handler(**arguments)

        data_to_dump = result.model_dump() if hasattr(result, "model_dump") else result
        text_out = json.dumps(data_to_dump, ensure_ascii=False, indent=2, default=str)

        return {
            "content": [{"type": "text", "text": text_out}],
            "isError": getattr(result, "success", True) is False,
        }
    except Exception as exc:
        return {
            "content": [{"type": "text", "text": f"Error executing tool '{tool_name}': {exc}"}],
            "isError": True,
        }


def main() -> None:
    """Main JSON-RPC synchronous loop over stdin."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        for raw_line in sys.stdin:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                msg = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            method = msg.get("method", "")
            msg_id = msg.get("id")

            # 1. Antigravity IDE Discovery
            if method == "server/discover":
                write_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "serverInfo": {
                            "name": "splunk",
                            "version": "1.0.0",
                        },
                        "capabilities": {
                            "tools": {"listChanged": False},
                        },
                    },
                })
                continue

            # 2. MCP Initialize
            if method == "initialize":
                write_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": False},
                        },
                        "serverInfo": {
                            "name": "splunk",
                            "version": "1.0.0",
                        },
                    },
                })
                continue

            # 3. Notification ignore
            if method == "notifications/initialized":
                continue

            # 4. Ping
            if method == "ping":
                write_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {},
                })
                continue

            # 5. List Tools
            if method == "tools/list":
                write_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": build_tools_list(),
                    },
                })
                continue

            # 6. Call Tool
            if method == "tools/call":
                params = msg.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                call_result = loop.run_until_complete(execute_tool_async(tool_name, arguments))
                write_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": call_result,
                })
                continue

            # Unknown method
            if msg_id is not None:
                write_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not supported.",
                    },
                })

    except (KeyboardInterrupt, BrokenPipeError, EOFError):
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
