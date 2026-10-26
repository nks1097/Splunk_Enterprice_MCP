#!/usr/bin/env python3
"""
Splunk Enterprise MCP Server - Native STDIO Bridge for Antigravity IDE / Claude.
Ensures UTF-8 encoding, sys.path resolution, and clean stdio transport.
"""

import os
import sys
from pathlib import Path

# Force UTF-8 encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

# Resolve directories
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

# Add src and base dir to sys.path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Create log directory and redirect stderr for clean stdio transport
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
sys.stderr = open(LOG_DIR / "splunk_bridge.log", "a", encoding="utf-8")

# Import and execute server
from splunk_mcp.server import main

if __name__ == "__main__":
    main()
